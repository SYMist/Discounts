document.addEventListener("DOMContentLoaded", function () {
  let calendar;
  let rawEvents = [];
  let selectedOutlet = "ALL";
  let selectedBrands = new Set();  // 복수 선택을 위한 Set
  let urlMapping = {};  // URL 매핑 캐시

  function initCalendar(events) {
    const calendarEl = document.getElementById("calendar");
    calendar = new FullCalendar.Calendar(calendarEl, {
      initialView: "dayGridMonth",
      locale: "ko",
      headerToolbar: {
        left: "prev,next today",
        center: "title",
        right: "dayGridMonth,listMonth",
      },
      events: events,
      eventClick: function (info) {
        const event = info.event;
        const id = event.extendedProps.event_id;
        if (id) {
          // 캐시된 매핑 사용
          const filename = urlMapping[id];
          if (filename) {
            const url = `/pages/${filename}`;
            window.open(url, "_blank");
          } else {
            // 매핑에 없을 경우 구버전 URL로 시도
            const url = `/pages/event-${id}.html`;
            window.open(url, "_blank");
          }
        } else {
          alert("상세 페이지를 찾을 수 없습니다.");
        }
      },
    });
    calendar.render();
  }

  function applyFilters() {
    if (!calendar) return;
    // 필터 조건에 맞는 이벤트만 렌더
    const filtered = rawEvents.filter(e => {
    const okOutlet = selectedOutlet === "ALL" || e.outlet === selectedOutlet;
    // B) 복수 브랜드 중 하나라도 매칭되면 통과, 아무것도 선택되지 않으면 모두 통과
    const okBrand = selectedBrands.size === 0
      ? true
      : e.items.some(item => selectedBrands.has(item.brand));
    return okOutlet && okBrand;
  });
    calendar.removeAllEvents();
    filtered.forEach(event => calendar.addEvent(event));
  }

  function filterEvents(outlet) {
    selectedOutlet = outlet;
    // 기존에 선택된 브랜드 Clear
    selectedBrands.clear();

    // 지점 버튼 Active 토글
    document
      .querySelectorAll('#branch-filter-bar .filter-btn')
      .forEach(btn => {
        btn.classList.toggle('active', btn.dataset.branch === outlet);
      });

    buildBrandFilter();
    applyFilters();
  }

  window.filterEvents = filterEvents;

  function buildBrandFilter() {
    const container = document.getElementById('brand-filter-bar');
    container.innerHTML = '';

    // ① selectedOutlet에 맞는 이벤트만
    const eventsForOutlet = selectedOutlet === 'ALL'
      ? rawEvents
      : rawEvents.filter(e => e.outlet === selectedOutlet);

    // ② 브랜드 집합
    const brands = Array.from(new Set(
      eventsForOutlet.flatMap(e => e.items.map(item => item.brand))
        .filter(b => b && b.trim())
    ));

    // ③ 버튼 헬퍼: selectedBrands 에 있으면 active
    const makeBtn = (label, val) => {
      const btn = document.createElement('button');
      btn.textContent = label;
      btn.className = 'filter-btn';
      btn.dataset.brand = val;
      if (selectedBrands.has(val)) btn.classList.add('active');
      return btn;
    };

    // “전체” 버튼
    container.appendChild(makeBtn('전체', ''));

    // 각 브랜드 버튼
    brands.forEach(b => container.appendChild(makeBtn(b, b)));
  }

  function parseSheetData(data, outletName) {
    const rows = data.values.slice(1);
    const grouped = {};

    for (const row of rows) {
      if (row.length < 13 || !row[0] || !row[1]) continue;

      const [title, period, , , thumbnail, , desc, , , , , , eventId] = row;
      const dateParts = period.split("~");
      if (dateParts.length !== 2) continue;

      const start = parseDate(dateParts[0]);
      const end = parseDate(dateParts[1]);
      if (!start || !end) continue;

      const key = `${title}_${start}_${end}`;
      if (!grouped[key]) {
        grouped[key] = {
          title: `[${outletName}] ${title}`,
          start,
          end,
          description: desc,
          outlet: outletName,
          items: [],
          thumbnail,
          event_id: eventId
        };
      }

      // 브랜드/제품은 기존 크롤러에서 items로 전달됨
      const brand = row[7] || '';
      const product = row[8] || '';
      const price = row[9] || '';
      grouped[key].items.push({ brand, product, price });
    }

    return Object.values(grouped);
  }

  function parseDate(str) {
    const clean = str.replace(/\([^)]*\)/g, '').trim();
    if (!clean.includes('.')) return null;
    const [m, d] = clean.split('.').map(p => p.padStart(2, '0'));
    return `2025-${m}-${d}`;
  }

  function loadUrlMapping() {
    return fetch('/url-mapping.json')
      .then(response => response.json())
      .then(mapping => {
        urlMapping = mapping;
        console.log(`📋 URL 매핑 로드됨: ${Object.keys(mapping).length}개`);
      })
      .catch(error => {
        console.warn('URL 매핑 로드 실패:', error);
      });
  }

  function loadAllSheets() {
    const sheetId = '16JLl5-GVDSSQsdMowjZkTAzOmi6qkkz93to_GxMjQ18';
    const apiKey = '{{GOOGLE_API_KEY}}';
    const sheets = [
      { name: 'Sheet1', outlet: '송도' },
      { name: 'Sheet2', outlet: '김포' },
      { name: 'Sheet3', outlet: '스페이스원' }
    ];

    gapi.load('client', () => {
      gapi.client.init({ apiKey }).then(() => {
        Promise.all(
          sheets.map(s =>
            gapi.client.request({
              path: `https://sheets.googleapis.com/v4/spreadsheets/${sheetId}/values/${s.name}!A2:M`,
            }).then(res => parseSheetData(res.result, s.outlet))
          )
        ).then(results => {
          rawEvents = results.flat();
          initCalendar(rawEvents);
          buildBrandFilter();
        });
      });
    });
  }

  // URL 매핑 로드 후 시트 데이터 로드
  loadUrlMapping().then(() => {
    loadAllSheets();
  });
  // 브랜드 필터 클릭 핸들러 (단 한 번만 등록)
  document.getElementById('brand-filter-bar').addEventListener('click', e => {
    if (!e.target.matches('.filter-btn')) return;
    const val = e.target.dataset.brand;
    if (val === '') {
      selectedBrands.clear();
    } else {
      if (selectedBrands.has(val)) selectedBrands.delete(val);
      else selectedBrands.add(val);
    }
    // UI 업데이트
    document.querySelectorAll('#brand-filter-bar .filter-btn').forEach(btn => {
      const b = btn.dataset.brand;
      btn.classList.toggle(
        'active',
        b === '' 
          ? selectedBrands.size === 0 
          : selectedBrands.has(b)
      );
    });
    applyFilters();
  });
});