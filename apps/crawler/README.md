# Outlet Crawler (apps/crawler)

현대 프리미엄 아울렛(송도/김포/스페이스원) 행사 크롤러입니다. 기본 동작은 기존과 동일하며, 환경변수로 출력 경로를 재설정할 수 있습니다.

## 요구사항
- Python 3.9+
- Chrome/ChromeDriver (Selenium)
- 설치: `pip install -r apps/crawler/requirements.txt`

## 기본 동작 (신규 기본 경로)
- 상세 페이지 HTML: `apps/web/public/pages/{branch}-{slug}.html`
- URL 매핑 JSON: `apps/web/public/url-mapping.json`
- 사이트맵: `apps/web/public/sitemap.xml`
- 메인 인덱스: `apps/web/public/index.html`

## 환경변수 (선택)
- `OUTLET_TEMPLATE_PATH` — 상세 템플릿 경로 (기본: `apps/crawler/templates/template.html`)
- `OUTLET_INDEX_TEMPLATE_PATH` — 메인 인덱스 템플릿 경로 (기본: `apps/crawler/templates/index.tpl.html`)
- `OUTLET_PAGES_DIR` — 상세 페이지 출력 디렉터리 (기본: `apps/web/public/pages`)
- `OUTLET_MAPPING_PATH` — URL 매핑 JSON 경로 (기본: `apps/web/public/url-mapping.json`)
- `OUTLET_SITE_BASE_URL` — 사이트 기본 URL (기본: `https://discounts.deluxo.co.kr`)
- `OUTLET_SITEMAP_PATH` — 사이트맵 출력 경로 (기본: `apps/web/public/sitemap.xml`)
- `OUTLET_INDEX_OUTPUT_PATH` — 메인 인덱스 출력 경로 (기본: `apps/web/public/index.html`)
- `OUTLET_CREDENTIALS_PATH` — Google 서비스계정 키 경로 (기본: `apps/crawler/credentials.json` → 레거시 `outlet-crawler/credentials.json` 순)

예시:
```
export OUTLET_PAGES_DIR=/var/www/outlet/public/pages
export OUTLET_MAPPING_PATH=/var/www/outlet/public/url-mapping.json
python3 apps/crawler/crawler_organized.py
```

## Google Sheets
- 서비스 계정 키 파일: `apps/crawler/credentials.json` (레거시: `outlet-crawler/credentials.json`)
- 시트 이름: `Sheet1`/`Sheet2`/`Sheet3`

## 주의
- 서버의 웹 루트는 `apps/web/public`을 가리키도록 권장합니다.
- `.htaccess` 프리티 URL 규칙은 `public/pages/{branch}-{slug}.html` 구조를 가정합니다.
