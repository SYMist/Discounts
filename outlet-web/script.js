document.addEventListener("DOMContentLoaded", function () {
  let calendar;
  let rawEvents = [];
  let selectedOutlet = "ALL";
  let selectedBrand = "";

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
          const url = `https://symist.github.io/Discounts/pages/event-${id}.html`;
          window.open(url, "_blank");
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
      const okBrand = !selectedBrand || e.items.some(item => item.brand === selectedBrand);
      return okOutlet && okBrand;
    });
    calendar.removeAllEvents();
    filtered.forEach(event => calendar.addEvent(event));
  }

  function filterEvents(outlet) {
    selectedOutlet = outlet;
    // 버튼 Active 토글
    document.querySelectorAll('#branch-filter-bar .filter-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.branch === outlet);
    });
    applyFilters();
  }

  window.filterEvents = filterEvents;

  function buildBrandFilter() {
    const container = document.getElementById('brand-filter-bar');
    container.innerHTML = '';
    // 모든 아이템의 브랜드 수집
    const brands = Array.from(new Set(
      rawEvents.flatMap(e => e.items.map(item => item.brand)).filter(b => b && b.trim())
    ));
    // 버튼 헬퍼
    const makeBtn = (label, val) => {
      const btn = document.createElement('button');
      btn.textContent = label;
      btn.className = 'filter-btn';
      btn.dataset.brand = val;
      if (val === '') btn.classList.add('active');
      return btn;
    };
    container.appendChild(makeBtn('전체', ''));
    brands.forEach(b => container.appendChild(makeBtn(b, b)));
    container.addEventListener('click', e => {
      if (!e.target.matches('.filter-btn')) return;
      selectedBrand = e.target.dataset.brand;
      container.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.toggle('active', btn === e.target);
      });
      applyFilters();
    });
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

  loadAllSheets();
});