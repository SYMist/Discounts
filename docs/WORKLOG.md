# WORKLOG

## 작성 가이드
- 날짜별 섹션(예: `## YYYY-MM-DD`) 아래에 체크박스 리스트로 작업을 기록합니다.
- 완료는 `[x]`, 미완료는 `[ ]`로 표시합니다.
- 필요 시 `### 참고 파일 경로`, `### 비고` 섹션을 추가할 수 있습니다.
- 최신 일자는 파일 하단에 계속 추가합니다.
- 운영 절차(권장)
  1) `### 백로그`에 태스크를 리스트업합니다.
  2) 진행할 때, 백로그에서 해당 태스크를 삭제하고 오늘 날짜 섹션을 만든 뒤 그 항목을 옮깁니다.
  3) 해당 날짜 섹션에서 완료 처리(`[x]`)합니다.
 - 위치 규칙: 날짜 섹션들은 항상 `### 백로그` 섹션 위에 배치합니다.

## 2025-10-21
- [x] 크롤러 경로/도메인 환경변수화 (기본값 유지, 비파괴)
- [x] 리다이렉트/워커 생성 도구 추가 (url-mapping.json 단일 소스로 자동 생성)
- [x] 폴더 구조 개편(운영 무중단, 기본값 호환 유지)
- [x] 레거시 자산 → 새 구조 복사 실행
- [x] 크롤러/툴 문서 및 의존성 명시

## 2025-10-22
- [x] 문서루트 전환 준비 및 점검 계획 확정
- [x] 리다이렉트/워커 규칙 재생성
- [x] 공개 디렉터리 점검
- [x] 배포 파이프라인 정리
- [x] 프론트 점검
- [x] SEO 자가 점검
- [x] WORKLOG 업데이트 및 커밋/푸시

## 2025-10-23
- [x] 서버 문서 루트 전환 및 스모크 테스트(또는 Pages 커스텀 도메인 Active 확인 후 스모크)
- [x] 크롤러 새 기본 경로로 실행 검증
- [x] Google API 키 주입 빌드 커맨드 수정(변수 확장, sed) 후 재배포
- [x] Google Cloud API 키 허용 웹사이트에 Pages/커스텀 도메인 추가 및 정상 노출 확인

- [x] 크롤러 목록 수집을 HTTP(AJAX) 방식으로 전환(안정적 페이징) 및 클릭 폴백 유지
- [x] 실행 스위치 추가: `OUTLET_LISTING_MODE`(`http|click`), `OUTLET_MAX_PAGES`, `OUTLET_HEADLESS`, `OUTLET_SKIP_SHEETS`
- [x] 전체 페이지 수집(OUTLET_MAX_PAGES=4) 실행 및 Google Sheets 업데이트 반영
- [x] 생성물 재생성 반영: `apps/web/public/pages/*`, `sitemap.xml`, `url-mapping.json`, `index.html`
- [x] Cloudflare Pages Functions 추가: pages.dev → discounts.deluxo.co.kr 301 리다이렉트 (`apps/web/functions/[[path]].js`)
- [x] Functions 루트 경로 추가: `functions/[[path]].js` (UI 설정 없이 자동 인식)

## 2025-10-27
- [x] Cloudflare Pages: pages.dev → discounts.deluxo.co.kr 301 리다이렉트 활성화(Functions 배포)
- [x] 커스텀 도메인에서 AdSense 노출 확인 및 pages.dev 접근 자동 이동 확인
 - [x] GA4 연동 준비: Cloudflare Pages Variables에 `GA_MEASUREMENT_ID` 추가
 - [x] 빌드 커맨드 보강: GA Measurement ID/Google API 키 치환 및 .bak 정리
 - [x] GA4 gtag 스니펫 플레이스홀더 삽입: `apps/web/public/index.html`, `apps/crawler/templates/index.tpl.html`, `apps/crawler/templates/template.html`
 - [x] 배포 반영 확인: 커스텀 도메인 소스에 `gtag/js?id=G-…`와 `gtag('config','G-…')` 실치환 확인
 

## 2025-10-29
- [x] GA 이벤트 트래킹 코드 추가: `calendar_event_click`, `highlight_click`, `detail_official_click`
  - 파일: `apps/web/public/script.js`, `apps/crawler/templates/template.html`
- [x] 배포 및 실시간 수집 확인: Realtime/DebugView에 `calendar_event_click` 반영 확인
- [x] gtag 디버그 모드 지원(?ga_debug=1) 추가 및 디버그 핑 전송
- [x] Analytics 문서 추가: 이벤트 스키마/검증 가이드(`docs/ANALYTICS.md`)
- [x] 개인정보처리방침 업데이트: GA/AdSense 고지 및 옵트아웃 안내(`apps/web/public/privacy.html`)
 - [x] 이벤트 공통 파라미터: URL UTM(`utm_source`, `utm_medium`, `utm_campaign`, `utm_content`, `utm_term`) 자동 병합

### 백로그

- [ ] /events 허브 페이지 생성(전체 + 지점별 songdo/gimpo/spaceone 목록) 및 자동 갱신 스크립트
- [ ] index 노출형 "전체 보기" 섹션 추가(정적 링크 display:none 제거/대체)
- [ ] 상세 페이지 개선: Breadcrumb(UI + BreadcrumbList 스키마) 추가, 같은 지점 관련 행사 3~5개 내부 링크 노출
- [ ] sitemap 품질 보강: lastmod 갱신 확인, URL 증가 시 sitemap index 분할 도입 검토
- [ ] Search Console 모니터링: URL 검사(핵심 페이지 순차 색인 요청), 제외 사유(크롤링됨‑미인덱스/중복) 원인 정리 및 대응
- [ ] Core Web Vitals 점검: 이미지 크기/캐시/폰트 로딩 최적화(PageSpeed 지표 기반)
- [ ] 스키마 보강(사이트 레벨): Organization/WebSite + (선택) SearchAction 추가
- [ ] 크롤러 자동화: 일정 주기로 전체 수집 + sitemap/index 재생성(예: GitHub Actions 스케줄)

### 참고 파일 경로
- 크롤러: `apps/crawler/crawler_organized.py`
- 템플릿: `apps/crawler/templates/template.html`, `apps/crawler/templates/index.tpl.html`
- 웹 루트: `apps/web/public/`
- 리다이렉트/워커 생성: `apps/web/tools/build_redirects.py`
- 레거시 동기화: `tools/sync_legacy_to_apps.py`
- 구조 문서: `docs/STRUCTURE.md`

### 비고
- 모든 변경은 기본 경로/규칙을 보존하도록 설계되어 현재 운영에 영향 없음.
- 레거시 복사 완료로 새 구조로의 전환 준비가 끝났으며, 내일은 서버 문서루트만 전환하면 새 구조로 완전 이행 가능.
## 2025-11-02
- [x] /events 허브 페이지 생성(전체/지점별) 및 파일 생성 스크립트 추가
  - 파일: `apps/web/tools/generate_events_pages.py`
  - 산출물: `apps/web/public/events/index.html`, `events/songdo.html`, `events/gimpo.html`, `events/spaceone.html`
- [x] 메인에 노출형 "전체 보기" 섹션 추가(내부 링크 강화)
  - 파일: `apps/web/public/index.html`
- [x] sitemap.xml 생성 로직에 /events 페이지 포함
  - 파일: `apps/crawler/crawler_organized.py: generate_sitemap`
