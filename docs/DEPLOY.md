# 배포 가이드

## Cloudflare Pages 전환

### 기본 설정
- 프로젝트 생성: GitHub 저장소 연결 → Project 생성
- Output directory: `apps/web/public`
- Build command(선택):
  - API 키 주입: `python3 apps/web/tools/inject_api_key.py --key $GOOGLE_API_KEY`
  - _redirects 생성: `python3 apps/web/tools/build_pages_redirects.py`
  - 주의: 빌더에 Python이 없으면, 로컬에서 생성/커밋 후 빌드 명령은 비워둡니다.

### GA4 Measurement ID 주입
- Pages → Settings → Variables and Secrets에 `GA_MEASUREMENT_ID=G-XXXXXXXXXX` 추가(Production/Preview)
- 빌드 커맨드에서 플레이스홀더 치환(전체 HTML; 큰따옴표 사용)
```
find apps/web/public -type f -name '*.html' -print0 | \
  xargs -0 sed -i.bak "s|GA_MEASUREMENT_ID_PLACEHOLDER|${GA_MEASUREMENT_ID}|g" && \
find apps/crawler/templates -type f -name '*.html' -print0 | \
  xargs -0 sed -i.bak "s|GA_MEASUREMENT_ID_PLACEHOLDER|${GA_MEASUREMENT_ID}|g" && \
find apps/web/public apps/crawler/templates -name '*.bak' -delete
```
- 또는 빌드 커맨드를 간소화: `bash tools/replace_ga.sh`

### 리디렉션/리라이트(_redirects)
- `apps/web/public/_redirects` 사용(이미 생성 도구 제공)
- 포함 규칙:
  - 200 리라이트: `/{branch}/{slug}` → `/pages/{branch}-{slug}.html`
  - 301 정규화: `/pages/{branch}-{slug}.html` → `/{branch}/{slug}`
  - 301 매핑: `/pages/event-<id>.html` → `/{branch}/{slug}`

### pages.dev → 커스텀 도메인 301 (프리뷰 제외)
- Pages UI에 "Always use primary domain" 토글이 없는 경우, Functions로 간단히 301 처리합니다.
- 방법 1(권장, UI 설정 없이 자동 인식): 리포지토리 루트에 `functions/[[path]].js`
```
export async function onRequest(context) {
  const url = new URL(context.request.url);
  if (url.hostname.endsWith('.pages.dev')) {
    url.hostname = 'discounts.deluxo.co.kr';
    return Response.redirect(url.toString(), 301);
  }
  return context.next();
}
```
- 방법 2(UI로 Functions 디렉터리 지정): `apps/web/functions` 경로 사용
  - Cloudflare Pages → Settings → Functions → Functions directory를 `apps/web/functions`로 설정 후 재배포
- 검증: `curl -I https://<project>.pages.dev/…` → 301 Location: https://discounts.deluxo.co.kr/…

### DNS 연결
- Pages 도메인 발급 후, Cloudflare DNS에서 `discounts.deluxo.co.kr` → Pages CNAME 연결
- 기존 GitHub Pages CNAME을 Pages로 바꾸고 프록시(주황구름)는 유지 권장

## (대안) 원본 서버 문서루트 전환
- 목표 경로: `apps/web/public`
- Apache 예시 (vhost):
```
<VirtualHost *:80>
  ServerName discounts.deluxo.co.kr
  DocumentRoot /path/to/repo/apps/web/public

  <Directory /path/to/repo/apps/web/public>
    AllowOverride All
    Require all granted
    Options FollowSymLinks
  </Directory>

  ErrorLog ${APACHE_LOG_DIR}/discounts_error.log
  CustomLog ${APACHE_LOG_DIR}/discounts_access.log combined
</VirtualHost>
```
- Nginx 예시 (프리티 URL 포함):
```
server {
  server_name discounts.deluxo.co.kr;
  root /path/to/repo/apps/web/public;

  location ~ ^/(songdo|gimpo|spaceone)/(.+)$ {
    try_files /pages/$1-$2.html =404;
  }
  location ~ ^/pages/(songdo|gimpo|spaceone)-(.+)\.html$ {
    return 301 https://discounts.deluxo.co.kr/$1/$2;
  }
}
```

## 리다이렉트/워커 생성
- 실행: `python3 apps/web/tools/build_redirects.py`
- 산출물: `apps/web/tools/generated_redirects.htaccess`, `apps/web/tools/cloudflare_worker_complete.js`

## API 키 주입
- 실행: `export GOOGLE_API_KEY=your_key && python3 apps/web/tools/inject_api_key.py`
- script.js의 `{{GOOGLE_API_KEY}}`가 실제 키로 치환됩니다(커밋 금지 권장).

## 배포
- rsync 사용 예:
```
export DEPLOY_HOST=your.host
export DEPLOY_USER=youruser
export DEPLOY_PATH=/var/www/discounts/apps/web/public
./tools/deploy_rsync.sh
```

## 점검(스모크 테스트)
- 200: `/index.html`, `/url-mapping.json`, `/songdo/{slug}`
- 301: `/pages/{branch}-{slug}.html` → `/{branch}/{slug}`
- SEO: `python3 apps/web/tools/check_seo.py`
