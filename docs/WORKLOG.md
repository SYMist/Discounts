# WORKLOG

## 작성 가이드
- 이 문서는 날짜별 섹션(예: `## YYYY-MM-DD`)을 순차 추가하는 방식으로 작성합니다.
- 각 날짜에는 아래 소제목을 권장합니다.
  - `### 오늘 한 것들`
  - `### 내일 할 것들`
  - `### 참고 파일 경로` (필요 시)
  - `### 비고` (필요 시)
- 최신 일자는 파일 하단에 계속 추가합니다.

## 2025-10-21

### 오늘 한 것들
- 크롤러 경로/도메인 환경변수화 (기본값 유지, 비파괴)
  - 파일: `apps/crawler/crawler_organized.py`
  - 지원 환경변수: `OUTLET_TEMPLATE_PATH`, `OUTLET_INDEX_TEMPLATE_PATH`, `OUTLET_PAGES_DIR`, `OUTLET_MAPPING_PATH`, `OUTLET_SITE_BASE_URL`, `OUTLET_SITEMAP_PATH`, `OUTLET_INDEX_OUTPUT_PATH`, `OUTLET_CREDENTIALS_PATH`
  - Google Credentials 경로 탐색 로직 개선(ENV → `apps/crawler/credentials.json` → 레거시 경로)
- 리다이렉트/워커 생성 도구 추가 (url-mapping.json 단일 소스로 자동 생성)
  - 파일: `apps/web/tools/build_redirects.py`, `apps/web/tools/README.md`
  - 산출물: `generated_redirects.htaccess`, `cloudflare_worker_complete.js`
- 폴더 구조 개편(운영 무중단, 기본값 호환 유지)
  - 크롤러 이동: `apps/crawler/`
  - 템플릿 이동: `apps/crawler/templates/`
  - 웹 루트 신설: `apps/web/public/` (index.html, sitemap.xml, url-mapping.json, pages/, images/ 등 위치)
  - 구조 문서: `docs/STRUCTURE.md`
  - 레거시 보조 스크립트: `tools/sync_legacy_to_apps.py`
- 레거시 자산 → 새 구조 복사 실행
  - 실행: `python3 tools/sync_legacy_to_apps.py`
  - 결과: `apps/web/public/` 하위로 복사 완료, `pages` 파일 505개 확인
- 크롤러/툴 문서 및 의존성 명시
  - `apps/crawler/requirements.txt`, `apps/crawler/README.md`

## 2025-10-22

### 오늘 한 것들
- 문서루트 전환 준비 및 점검 계획 확정
  - 목표 문서루트: `apps/web/public`
  - 전환 후 점검 체크리스트 정리(200/301 응답 확인 항목)
- 리다이렉트/워커 규칙 재생성
  - 실행: `python3 apps/web/tools/build_redirects.py`
  - 산출물: `apps/web/tools/generated_redirects.htaccess`, `apps/web/tools/cloudflare_worker_complete.js`
- 공개 디렉터리 점검
  - 핵심 파일 존재 확인: `index.html`, `url-mapping.json`, `sitemap.xml`, `.htaccess`, `script.js`, `style.css`, `robots.txt`, `ads.txt`
  - 페이지 개수 확인: `apps/web/public/pages` 505개

### 내일 할 것들
- 서버 문서루트 실제 전환(운영 서버 설정 적용) 및 스모크 테스트
- 크롤러 새 경로에서 실행 검증(자격증명 포함)
- (선택) `.htaccess` 301 규칙 블록의 최신화 반영 또는 Cloudflare Worker 배포
- WORKLOG 업데이트 및 커밋/푸시

### 내일 할 것들
- 서버 문서 루트 전환 및 스모크 테스트
  - 문서 루트를 `apps/web/public`로 변경 후 점검: `/url-mapping.json` 200, `/songdo/{slug}` 200, `/pages/{branch}-{slug}.html` 301 정규화
- 크롤러 새 기본 경로로 실행 검증
  - `pip install -r apps/crawler/requirements.txt`
  - `python3 apps/crawler/crawler_organized.py` 실행 → `apps/web/public/pages`/`url-mapping.json`/`sitemap.xml`/`index.html` 갱신 확인
- 리다이렉트/워커 규칙 재생성(선택)
  - `python3 apps/web/tools/build_redirects.py` 실행 → `.htaccess` 규칙 블록 및 Cloudflare Worker 최신화 비교/반영
- 배포 파이프라인 정리
  - 배포 대상 디렉토리 단일화: `apps/web/public`만 동기화
  - (선택) 레거시 `outlet-web/`는 보관 또는 제거 계획 수립
- 프론트 점검
  - `script.js`의 `{{GOOGLE_API_KEY}}` 주입 전략(환경변수/빌드 단계 치환) 확정 및 테스트
- SEO 자가 점검
  - `sitemap.xml` 최신성/URL 유효성 확인, `robots.txt`/`ads.txt` 노출 확인

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
