# Search Console 운영 가이드

## 목적
- 신규/중요 URL의 색인 속도를 높이고, 제외 사유를 꾸준히 해소합니다.

## 일일 루틴(권장)
1) 사이트맵 상태 확인
   - Sitemaps: `/sitemap.xml` 제출 상태와 오류/경고 확인
   - 분할된 `sitemap-*.xml`이 있는 경우 index가 모든 part를 가리키는지 확인
2) 핵심 URL 인덱싱 요청(최대 10~20개)
   - `apps/web/tools/list_recent_urls.py --days 3 --limit 50`로 최근 URL 후보를 뽑아 상위 우선 제출
3) 제외 사유 분석
   - “크롤링됨-미인덱스”, “중복(선정하지 않음)” 우선
   - 원인 예: 내부 링크 부족, 페이지 유사도 높음, 링크 깊이, 새로 생성된 페이지군 등
   - 조치: 내부링크 보강(/events 허브, 관련 행사, 브레드크럼), 제목/콘텐츠 중복 완화, sitemap과 URL Inspection 병행

## 유틸리티
- 최근 URL 리스트업(수동 제출 후보)
```
python3 apps/web/tools/list_recent_urls.py --days 7 --limit 100 > recent_urls.txt
```
옵션
- `--days`: 최근 N일(기본 7일)
- `--limit`: 최대 개수(기본 100)

## 팁
- 색인 요청은 핵심 페이지(지점 메인 행사, 고가치 브랜드/프로모션) 위주로 소량 반복이 효과적입니다.
- 동일 지점/브랜드 묶음으로 내부 링크를 촘촘히 유지하면 ‘중복’ 판단을 피하고 크롤링 우선순위가 올라갑니다.
- Safari Private 등 일부 환경은 GA 실시간 집계가 낮게 표시될 수 있으므로 Chrome Incognito로 측정하세요.

