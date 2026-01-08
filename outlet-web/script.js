// 즉시 실행 함수 - DOM 로드 상태와 무관하게 실행 (v20260108)
(function() {
  let calendar;
  let rawEvents = [];
  let selectedOutlet = "ALL";
  let selectedBrands = new Set();  // 복수 선택을 위한 Set
  let urlMapping = {};  // URL 매핑 캐시

  // 디버깅용 전역 노출 (즉시 설정)
  window._debug = {
    get rawEvents() { return rawEvents; },
    get urlMapping() { return urlMapping; },
    get calendar() { return calendar; }
  };
  console.log('✅ _debug 객체가 window에 등록되었습니다.');

  function init() {

  // GA 디버그 플래그 (?ga_debug=1 로 접근 시 활성화)
  const qs = new URLSearchParams(location.search);
  const debugMode = qs.has('ga_debug');
  const utmParams = {
    utm_source: qs.get('utm_source') || undefined,
    utm_medium: qs.get('utm_medium') || undefined,
    utm_campaign: qs.get('utm_campaign') || undefined,
    utm_content: qs.get('utm_content') || undefined,
    utm_term: qs.get('utm_term') || undefined,
  };

  // GA 이벤트 전송 헬퍼 (gtag 존재 시에만 동작)
  function sendGA(eventName, params) {
    try {
      if (typeof window.gtag === 'function') {
        const payload = Object.assign({}, utmParams, params || {});
        if (debugMode) payload.debug_mode = true;
        if (debugMode) console.log('[GA]', eventName, payload);
        window.gtag('event', eventName, payload);
      }
    } catch (e) { /* no-op */ }
  }

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
          // UUID에서 shortId 추출
          let shortId = id;
          if (id.includes('-')) {
            const parts = id.split('-');
            shortId = parts[parts.length - 1];
          }

          // 캐시된 매핑 사용 (변형 ID도 체크)
          let filename = urlMapping[id] || urlMapping[shortId];
          if (!filename) {
            // _02가 있으면 기본 ID로 시도
            if (shortId.endsWith('_02')) {
              const baseId = shortId.slice(0, -3);
              filename = urlMapping[baseId];
            }
            // 기본 ID면 _02 변형으로 시도
            else {
              filename = urlMapping[shortId + '_02'];
            }
          }
          
          if (filename) {
            const url = `/pages/${filename}`;
            // GA: 캘린더 이벤트 클릭
            sendGA('calendar_event_click', {
              event_id: id,
              title: event.title || '',
              outlet: (event.extendedProps && event.extendedProps.outlet) || '',
              start: event.startStr || event.start || '',
              end: event.endStr || event.end || ''
            });
            window.open(url, "_blank");
          } else {
            console.error(`매핑되지 않은 이벤트 클릭됨 - ${id}`);
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
    let skippedCount = 0;
    let noMappingCount = 0;

    console.log(`📥 [${outletName}] 시트에서 ${rows.length}개 행 수신`);

    for (const row of rows) {
      // 디버깅: 첫 5개 행의 구조 출력
      if (rows.indexOf(row) < 3) {
        console.log(`[DEBUG] row[${rows.indexOf(row)}] 길이=${row.length}:`, row.slice(0, 5), '... eventId=', row[12]);
      }

      if (row.length < 13 || !row[0] || !row[1]) {
        skippedCount++;
        continue;
      }

      // 시트 컬럼: A=제목, B=기간, C=시작날짜(ISO), D=종료날짜(ISO), E=썸네일, F=?, G=설명, ..., M=eventId
      const [title, period, startDateISO, endDateISO, thumbnail, , desc, , , , , , eventId] = row;

      // C, D 컬럼에 ISO 날짜가 있으면 직접 사용, 없으면 기간 텍스트 파싱
      let start = startDateISO && startDateISO.match(/^\d{4}-\d{2}-\d{2}$/) ? startDateISO : null;
      let end = endDateISO && endDateISO.match(/^\d{4}-\d{2}-\d{2}$/) ? endDateISO : null;

      // ISO 날짜가 없으면 기간 텍스트에서 파싱 (fallback)
      if (!start || !end) {
        const dateParts = period.split("~");
        if (dateParts.length !== 2) continue;
        start = start || parseDate(dateParts[0]);
        end = end || parseDate(dateParts[1]);

        // 시작일이 종료일보다 큰 경우 (연말-연초 이벤트) 종료일 연도 조정
        if (start && end && start > end) {
          const [y, m, d] = end.split('-');
          end = `${parseInt(y) + 1}-${m}-${d}`;
          console.log(`🔄 연도 조정: ${dateParts[0]}~${dateParts[1]} → start=${start}, end=${end}`);
        }
      }

      if (!start || !end) continue;

      // 날짜 유효성 검사
      const startDate = new Date(start);
      const endDate = new Date(end);
      if (isNaN(startDate.getTime()) || isNaN(endDate.getTime())) {
        console.warn(`⚠️ 유효하지 않은 날짜: start="${start}", end="${end}", title="${title}"`);
        continue;
      }

      // FullCalendar의 end는 exclusive이므로 하루 추가
      endDate.setDate(endDate.getDate() + 1);
      const endExclusive = endDate.toISOString().split('T')[0];

      // URL 매핑이 없는 이벤트는 제외 (변형 ID도 체크)
      // eventId가 UUID 형식(예: 78565274-4f6e-420f-9df7-f2ba0c6c1728)이면 마지막 부분 추출
      let shortId = eventId;
      if (eventId && eventId.includes('-')) {
        const parts = eventId.split('-');
        shortId = parts[parts.length - 1]; // 마지막 부분 (예: f2ba0c6c1728)
      }

      let mappedFilename = urlMapping[eventId] || urlMapping[shortId];
      if (!mappedFilename) {
        // _02가 있으면 기본 ID로 시도
        if (shortId.endsWith('_02')) {
          const baseId = shortId.slice(0, -3);
          mappedFilename = urlMapping[baseId];
        }
        // 기본 ID면 _02 변형으로 시도
        else {
          mappedFilename = urlMapping[shortId + '_02'];
        }
      }
      
      if (!mappedFilename) {
        noMappingCount++;
        console.log(`⚠️ 매핑되지 않은 이벤트 제외: eventId="${eventId}", shortId="${shortId}", title="${title}"`);
        continue;
      }

      const key = `${title}_${start}_${end}`;
      if (!grouped[key]) {
        grouped[key] = {
          title: `[${outletName}] ${title}`,
          start,
          end: endExclusive,  // FullCalendar용 exclusive 종료일
          endDisplay: end,     // 표시용 실제 종료일
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

    const result = Object.values(grouped);
    console.log(`📊 [${outletName}] 결과: ${result.length}개 이벤트 (스킵: ${skippedCount}, 매핑없음: ${noMappingCount})`);
    return result;
  }

  function parseDate(str) {
    const clean = str.replace(/\([^)]*\)/g, '').trim();
    if (!clean.includes('.')) return null;
    const [m, d] = clean.split('.').map(p => p.padStart(2, '0'));
    // 현재 연도 기준으로 날짜 결정 (월이 현재보다 6개월 이상 과거면 다음해로 추정)
    const now = new Date();
    const currentYear = now.getFullYear();
    const currentMonth = now.getMonth() + 1;
    const parsedMonth = parseInt(m, 10);

    // 현재 월보다 6개월 이상 뒤(예: 현재 1월인데 7월 이후 이벤트)면 지난해일 수 있음
    // 현재 월보다 6개월 이상 앞(예: 현재 12월인데 1월 이벤트)면 내년일 수 있음
    let year = currentYear;
    if (parsedMonth > currentMonth + 6) {
      year = currentYear - 1; // 지난해
    } else if (parsedMonth < currentMonth - 6) {
      year = currentYear + 1; // 내년
    }

    return `${year}-${m}-${d}`;
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
          const displayEnd = event.endDisplay || event.end;
          li.innerHTML = `
            <strong>${event.title}</strong><br>
            <small>기간: ${formatDateRange(event.start, displayEnd)}</small>
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
              // UUID에서 shortId 추출
              let shortId = id;
              if (id.includes('-')) {
                const parts = id.split('-');
                shortId = parts[parts.length - 1];
              }

              let filename = urlMapping[id] || urlMapping[shortId];
              if (!filename) {
                // _02가 있으면 기본 ID로 시도
                if (shortId.endsWith('_02')) {
                  const baseId = shortId.slice(0, -3);
                  filename = urlMapping[baseId];
                }
                // 기본 ID면 _02 변형으로 시도
                else {
                  filename = urlMapping[shortId + '_02'];
                }
              }

              if (filename) {
                const url = `/pages/${filename}`;
                // GA: 하이라이트 클릭
                sendGA('highlight_click', {
                  event_id: id,
                  title: event.title || '',
                  outlet: event.outlet || '',
                  start: event.start || '',
                  end: event.endDisplay || event.end || ''
                });
                window.open(url, '_blank');
              } else {
                const url = `/pages/event-${shortId}.html`;
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

        // UUID에서 shortId 추출
        let shortId = id;
        if (id && id.includes('-')) {
          const parts = id.split('-');
          shortId = parts[parts.length - 1];
        }

        let url = `/pages/event-${shortId}.html`; // 기본 URL

        // URL 매핑이 있으면 사용 (변형 ID도 체크)
        let filename = urlMapping[id] || urlMapping[shortId];
        if (!filename) {
          // _02가 있으면 기본 ID로 시도
          if (shortId.endsWith('_02')) {
            const baseId = shortId.slice(0, -3);
            filename = urlMapping[baseId];
          }
          // 기본 ID면 _02 변형으로 시도
          else {
            filename = urlMapping[shortId + '_02'];
          }
        }

        if (filename) {
          url = `/pages/${filename}`;
        }

        const displayEnd = event.endDisplay || event.end;
        li.innerHTML = `<a href="${url}">${event.title} (${formatDateRange(event.start, displayEnd)})</a>`;
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
    // 템플릿 문자열이 아닌 실제 API 키인지 확인 (빌드 미치환 또는 $ENV 그대로 남은 경우 방지)
    if (apiKey.includes('{{') || apiKey.startsWith('$') || !apiKey || apiKey.length < 10) {
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
    // GA 디버그 모드일 때 핑 전송
    if (debugMode) sendGA('debug_ping', { page: location.pathname });
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
  } // end of init function

  // DOM 준비 상태에 따라 init 호출
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    // DOM이 이미 로드됨 - 즉시 실행
    init();
  }
})();
