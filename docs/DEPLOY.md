# 배포 가이드

## 문서루트 전환
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

