# Analytics Guide (GA4)

## 개요
- 본 사이트는 Google Analytics 4(GA4)를 사용하여 페이지뷰 및 핵심 클릭 이벤트를 측정합니다.
- 측정 ID는 Cloudflare Pages 환경변수 `GA_MEASUREMENT_ID`로 주입되며, 빌드 커맨드에서 플레이스홀더를 치환합니다.

## 주입/빌드
- 환경변수: `GA_MEASUREMENT_ID=G-XXXXXXXXXX`
- 빌드 커맨드 예시
```
sed -i.bak "s|GA_MEASUREMENT_ID_PLACEHOLDER|${GA_MEASUREMENT_ID}|g" \
  apps/web/public/index.html \
  apps/crawler/templates/index.tpl.html \
  apps/crawler/templates/template.html && \
find apps/web/public apps/crawler/templates -name '*.bak' -delete
```

## 이벤트 스키마
- 페이지뷰: gtag 기본 `page_view`
- 커스텀 이벤트
  - `calendar_event_click`
    - 파라미터: `event_id`, `title`, `outlet`, `start`, `end`
  - `highlight_click`
    - 파라미터: `event_id`, `title`, `outlet`, `start`, `end`
  - `detail_official_click`
    - 파라미터: `event_id`, `title`, `outlet`, `link`

## 디버깅/검증
- Realtime/DebugView
  - GA 콘솔: Reports → Realtime, Admin → DebugView
- 네트워크 체크(브라우저 DevTools → Network)
  - `gtag/js?id=G-…` 200 로드
  - `www.google-analytics.com/g/collect` 204 발생
- 디버그 모드(선택)
  - URL에 `?ga_debug=1` 추가 시, `debug_mode=true`로 이벤트 전송 및 콘솔 로그 출력

## 내부 트래픽/설정 권장
- Admin → Data filters에서 Internal/Developer Traffic를 Testing 후 적용
- Data streams(Web) → Enhanced measurement ON
- Property Timezone을 KST로 설정

## 변경 위치
- gtag 스니펫: `apps/web/public/index.html`, `apps/crawler/templates/index.tpl.html`, `apps/crawler/templates/template.html`
- 이벤트 전송: `apps/web/public/script.js`, 상세 배너 클릭: `apps/crawler/templates/template.html`

