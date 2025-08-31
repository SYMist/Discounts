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
          // 캐시된 매핑 사용 (매핑되지 않은 이벤트는 이미 필터링됨)
          const filename = urlMapping[id];
          if (filename) {
            const url = `/pages/${filename}`;
            window.open(url, "_blank");
          } else {
            // 이론적으로 여기에 도달하지 않아야 함 (이미 필터링됨)
            console.error(`예상치 못한 오류: 매핑되지 않은 이벤트 클릭됨 - ${id}`);
            alert("상세 페이지를 찾을 수 없습니다.");
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

      // URL 매핑이 없는 이벤트는 제외
      if (!urlMapping[eventId]) {
        console.log(`⚠️ 매핑되지 않은 이벤트 제외: ${eventId} - ${title}`);
        continue;
      }

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

  function updateHighlightEvents() {
    const today = new Date();
    const currentDateStr = today.toISOString().split('T')[0]; // YYYY-MM-DD 형태
    
    // 각 지점별로 현재 진행 중인 이벤트 중 상위 2개씩 선택
    const outlets = ['송도', '김포', '스페이스원'];
    const highlightEvents = [];
    
    outlets.forEach(outlet => {
      const outletEvents = rawEvents
        .filter(event => {
          // 현재 진행 중인 이벤트 필터링
          return event.outlet === outlet && 
                 event.start <= currentDateStr && 
                 event.end >= currentDateStr;
        })
        .slice(0, 2); // 상위 2개만 선택 (구글시트 순서대로)
      
      highlightEvents.push(...outletEvents);
    });
    
    // 하이라이트 이벤트 UI 업데이트
    const highlightContainer = document.querySelector('#highlight-events ul');
    if (highlightContainer) {
      highlightContainer.innerHTML = '';
      
      if (highlightEvents.length === 0) {
        highlightContainer.innerHTML = '<li>현재 진행 중인 이벤트가 없습니다.</li>';
      } else {
        highlightEvents.forEach(event => {
          const li = document.createElement('li');
          li.innerHTML = `
            <strong>${event.title}</strong><br>
            <small>기간: ${formatDateRange(event.start, event.end)}</small>
          `;
          li.style.cursor = 'pointer';
          li.style.marginBottom = '0.8rem';
          li.style.padding = '0.5rem';
          li.style.backgroundColor = '#f8f9fa';
          li.style.borderRadius = '4px';
          li.style.border = '1px solid #e9ecef';
          
          li.addEventListener('click', () => {
            const id = event.event_id;
            if (id) {
              const filename = urlMapping[id];
              if (filename) {
                const url = `/pages/${filename}`;
                window.open(url, '_blank');
              } else {
                const url = `/pages/event-${id}.html`;
                window.open(url, '_blank');
              }
            }
          });
          
          highlightContainer.appendChild(li);
        });
      }
    }
    
    // SEO용 정적 링크 업데이트
    updateStaticEventLinks();
  }
  
  function updateStaticEventLinks() {
    const staticContainer = document.querySelector('#static-event-links ul');
    if (staticContainer) {
      staticContainer.innerHTML = '';
      
      rawEvents.forEach(event => {
        const li = document.createElement('li');
        const id = event.event_id;
        let url = `/pages/event-${id}.html`; // 기본 URL
        
        // URL 매핑이 있으면 사용
        if (urlMapping[id]) {
          url = `/pages/${urlMapping[id]}`;
        }
        
        li.innerHTML = `<a href="${url}">${event.title} (${formatDateRange(event.start, event.end)})</a>`;
        staticContainer.appendChild(li);
      });
    }
  }
  
  function formatDateRange(start, end) {
    const startDate = new Date(start);
    const endDate = new Date(end);
    const startStr = `${startDate.getMonth() + 1}.${startDate.getDate()}`;
    const endStr = `${endDate.getMonth() + 1}.${endDate.getDate()}`;
    return `${startStr} ~ ${endStr}`;
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
          console.log(`📊 총 이벤트 수: ${rawEvents.length}개 (매핑된 이벤트만)`);
          initCalendar(rawEvents);
          buildBrandFilter();
          updateHighlightEvents(); // 하이라이트 이벤트 업데이트 추가
        });
      });
    });
  }

  // 테스트용 더미 데이터 함수
  function loadDummyData() {
    console.log('🧪 더미 데이터로 테스트 중...');
    const today = new Date();
    const todayStr = today.toISOString().split('T')[0];
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    const tomorrowStr = tomorrow.toISOString().split('T')[0];
    
    const nextWeek = new Date(today);
    nextWeek.setDate(nextWeek.getDate() + 7);
    const nextWeekStr = nextWeek.toISOString().split('T')[0];

    rawEvents = [
      {
        title: '[송도] 나이키 시즌 오프 최대 70%',
        start: todayStr,
        end: nextWeekStr,
        outlet: '송도',
        event_id: 'dummy-1',
        items: [{ brand: '나이키', product: '운동화', price: '50% 할인' }]
      },
      {
        title: '[송도] 언더아머 썸머 익스트림 세일',
        start: todayStr,
        end: tomorrowStr,
        outlet: '송도',
        event_id: 'dummy-2',
        items: [{ brand: '언더아머', product: '스포츠웨어', price: '최대 70%' }]
      },
      {
        title: '[김포] 라코스테 클리어런스 UP TO 85% OFF',
        start: todayStr,
        end: nextWeekStr,
        outlet: '김포',
        event_id: 'dummy-3',
        items: [{ brand: '라코스테', product: '폴로셔츠', price: '85% 할인' }]
      },
      {
        title: '[김포] 스케쳐스 썸머 특별 프로모션',
        start: todayStr,
        end: tomorrowStr,
        outlet: '김포',
        event_id: 'dummy-4',
        items: [{ brand: '스케쳐스', product: '운동화', price: '특가' }]
      },
      {
        title: '[스페이스원] 브룩스브라더스 패밀리 세일',
        start: todayStr,
        end: nextWeekStr,
        outlet: '스페이스원',
        event_id: 'dummy-5',
        items: [{ brand: '브룩스브라더스', product: '셔츠', price: '50% 할인' }]
      },
      {
        title: '[스페이스원] 스케쳐스 썸머 특별 프로모션',
        start: todayStr,
        end: tomorrowStr,
        outlet: '스페이스원',
        event_id: 'dummy-6',
        items: [{ brand: '스케쳐스', product: '샌들', price: '40% 할인' }]
      }
    ];
    
    initCalendar(rawEvents);
    buildBrandFilter();
    updateHighlightEvents();
  }

  // API 키 확인 후 분기 처리
  function checkApiAndLoad() {
    const apiKey = '{{GOOGLE_API_KEY}}';
    // 템플릿 문자열이 아닌 실제 API 키인지 확인
    if (apiKey.includes('{{') || !apiKey || apiKey.length < 10) {
      console.warn('⚠️ Google API 키가 설정되지 않았습니다. 더미 데이터로 테스트합니다.');
      loadDummyData();
    } else {
      console.log('📊 Google Sheets에서 실제 데이터를 로드합니다.');
      loadAllSheets();
    }
  }

  // URL 매핑 로드 후 데이터 로드
  loadUrlMapping().then(() => {
    checkApiAndLoad();
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