# Redirect/Worker Builder (apps/web/tools)

url-mapping.json을 단일 소스로 사용해 아래 산출물을 생성합니다.

- `generated_redirects.htaccess`: 구 URL(`/pages/event-*.html`) → 새 프리티 URL(`/branch/slug`) 301 리다이렉트 규칙
- `cloudflare_worker_complete.js`: 동일 매핑을 사용하는 클라우드플레어 Workers 스크립트

## 사용법

기본값(현재 디렉토리 기준 경로):

```
python3 apps/web/tools/build_redirects.py
```

옵션으로 경로 지정:

```
python3 apps/web/tools/build_redirects.py \
  --mapping ../public/url-mapping.json \
  --pages ../public/pages \
  --out-dir .
```

생성물 위치: `apps/web/tools/`

생성된 `generated_redirects.htaccess`의 내용을 웹 루트의 `.htaccess` 내
`# 2. 기존 pages/event-*.html 파일들을 새로운 구조로 리다이렉트 (301 리다이렉트)`
주석 하단의 규칙 블록에 반영하세요.

Cloudflare 사용 시 `cloudflare_worker_complete.js`를 배포하세요.

