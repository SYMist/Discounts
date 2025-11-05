import time
import os
import requests
import re
from bs4 import BeautifulSoup
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- 경로/환경설정 (기본값은 기존 경로 유지)
CFG = None

def _get_config():
    """환경변수를 통해 경로를 재설정할 수 있도록 지원합니다.
    기본값은 현재 코드가 사용하던 상대경로를 그대로 유지합니다.
    
    사용 가능한 환경변수
    - OUTLET_TEMPLATE_PATH
    - OUTLET_INDEX_TEMPLATE_PATH
    - OUTLET_PAGES_DIR
    - OUTLET_MAPPING_PATH
    - OUTLET_SITE_BASE_URL
    - OUTLET_SITEMAP_PATH
    - OUTLET_INDEX_OUTPUT_PATH
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return {
        "TEMPLATE_PATH": os.environ.get(
            "OUTLET_TEMPLATE_PATH",
            os.path.join(base_dir, "templates", "template.html"),
        ),
        "INDEX_TEMPLATE_PATH": os.environ.get(
            "OUTLET_INDEX_TEMPLATE_PATH",
            os.path.join(base_dir, "templates", "index.tpl.html"),
        ),
        "PAGES_DIR": os.environ.get(
            "OUTLET_PAGES_DIR",
            os.path.join(base_dir, "../web/public/pages"),
        ),
        "MAPPING_PATH": os.environ.get(
            "OUTLET_MAPPING_PATH",
            os.path.join(base_dir, "../web/public/url-mapping.json"),
        ),
        "SITE_BASE_URL": os.environ.get(
            "OUTLET_SITE_BASE_URL",
            "https://discounts.deluxo.co.kr",
        ),
        "SITEMAP_PATH": os.environ.get(
            "OUTLET_SITEMAP_PATH",
            os.path.join(base_dir, "../web/public/sitemap.xml"),
        ),
        "INDEX_OUTPUT_PATH": os.environ.get(
            "OUTLET_INDEX_OUTPUT_PATH",
            os.path.join(base_dir, "../web/public/index.html"),
        ),
    }

# --- 전역 변수 (main에서 초기화)
url_mapping = {}

# --- 유틸: 날짜 포맷 변환(YYYYMMDDHHMMSS -> M.D)
def _fmt_md(yyyymmddhhmmss: str) -> str:
    try:
        if not yyyymmddhhmmss:
            return ""
        s = yyyymmddhhmmss.strip()
        y = int(s[0:4]); m = int(s[4:6]); d = int(s[6:8])
        return f"{m}.{d}"
    except Exception:
        return ""

def parse_period(period_text):
    # 1) 줄바꿈 제거
    clean = period_text.replace("\n", "").replace("\r", "")
    # 2) 괄호 안 설명 모두 제거
    clean = re.sub(r"\([^)]*\)", "", clean)
    # 3) 공백(스페이스) 전부 제거
    clean = clean.replace(" ", "")
    # 4) '~' 기준으로 분리
    parts = clean.split("~")
    if len(parts) != 2:
        return "", ""
    # 5) ISO 포맷으로 변환
    def to_iso(s):
        if "." not in s:
            return ""
        m, d = s.split(".")
        return f"2025-{m.zfill(2)}-{d.zfill(2)}"
    return to_iso(parts[0]), to_iso(parts[1])

# --- WebDriver 설정
def setup_driver():
    options = Options()
    options.add_argument("--window-size=1920,1080")
    # Optional headless mode for non-interactive environments
    import os as _os
    if _os.environ.get("OUTLET_HEADLESS", "").lower() in ("1", "true", "yes"): 
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    return driver

# --- 가격 텍스트 처리
def process_price_text(price_text):
    if "정상가" in price_text and "판매가" in price_text:
        try:
            parts = price_text.split("판매가")
            original_price = parts[0].strip()
            sale_price = parts[1].strip()
            return f"<s>{original_price}</s> 판매가 {sale_price}"
        except:
            return price_text
    else:
        return price_text

# --- 행사 리스트 페이지 크롤링
def fetch_event_list(driver, branchCd, page):
    """행사 목록 페이징 수집.
    - 기본: HTTP(AJAX) 요청으로 안정적으로 수집
    - 폴백: Selenium + getContents 또는 첫 페이지 파싱
    반환: 
      - HTTP 모드: dict 리스트 [{title, period, image, link}]
      - 클릭/폴백: BeautifulSoup li 요소 리스트
    """
    import os as _os, re, requests
    mode = _os.environ.get("OUTLET_LISTING_MODE", "http").lower()

    list_url = f"https://www.ehyundai.com/newPortal/SN/SN_0101000.do?branchCd={branchCd}&SN=1"

    if mode == "http":
        try:
            html = requests.get(list_url, timeout=15).text
            m = re.search(r"var\s+curtMblDmCd\s*=\s*'([^']+)'", html)
            if not m:
                raise RuntimeError("mblDmCd 파싱 실패")
            mbl = m.group(1)
            # typeCd '01' = 이벤트
            api = "https://www.ehyundai.com/newPortal/SN/GetCmsContentsAJX.do"
            params = {
                'apiID': 'ifAppHdcms012',
                'param': f"mblDmCd={mbl}&evntCrdTypeCd=01&pageSize=9&page={page}",
            }
            js = requests.get(api, params=params, timeout=15).json()
            items = js.get('result', {}).get('items', [])
            evts = []
            for it in items:
                # 카테고리 판단
                t = (it.get('evntCrdTypeCd') or {}).get('value') or '01'
                if t == '02':
                    category = 'gift'
                elif t == '03':
                    category = 'culture'
                elif t == '04':
                    category = 'special'
                else:
                    category = 'event'
                img = it.get('imgPath2') or ''
                if img:
                    img = ("https://imgprism.ehyundai.com/" + img).replace("https://apiprism.ehyundai.com/", "")
                # 기간 문자열 구성
                stCd = (it.get('expsEvntStartGbcd') or {}).get('value')
                enCd = (it.get('expsEvntEndGbcd') or {}).get('value')
                st = it.get('expsEvntStartTxt') if stCd == '02' else _fmt_md(it.get('expsEvntStartDt') or '')
                en = it.get('expsEvntEndTxt') if enCd == '02' else _fmt_md(it.get('expsEvntEndDt') or '')
                period = (st or '') + (" ~ " if (st or en) and en else "") + (en or '')
                link = f"https://www.ehyundai.com/newPortal/SN/SN_0201000.do?evntCrdCd={it.get('evntCrdCd')}&category={category}&page={page}&branchCd={branchCd}"
                evts.append({
                    'title': it.get('evntCrdNm') or '',
                    'period': period,
                    'image': img,
                    'link': link,
                })
            return evts
        except Exception as e:
            print(f"⚠️ HTTP 목록 수집 실패: {e}. 클릭 모드로 폴백합니다.")
            # 폴백으로 계속 진행

    # ── 클릭/폴백 모드
    driver.get(list_url)
    # Wait for page scripts to load (getContents function) then load requested page
    try:
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script("return typeof getContents === 'function'")
        )
        try:
            driver.execute_script(f"getContents('01', {page}, 0);")
        except Exception as e:
            print(f"⚠️ getContents 호출 실패: {e}. 첫 페이지 그대로 파싱을 시도합니다.")
    except Exception:
        # 스크립트 미탑재 시 첫 페이지 파싱만
        pass
    # Wait for event list elements to be present
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#eventList > li"))
        )
    except Exception:
        time.sleep(2)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    return soup.select("#eventList > li")

# --- 행사 상세페이지 크롤링
def fetch_event_detail(driver, url):
    try:
        driver.get(url)
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "article"))
        )
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # ① 제목 가져오기 (fixAreas → fixArea)
        title_el = soup.select_one("section.fixArea h2")
        title_text = title_el.text.strip() if title_el else ""

        # ② 기간 문자열 가져오기
        period_el = soup.select_one("table.info td")
        period_text = period_el.text.strip() if period_el else ""

        # ③ ISO 포맷 날짜 파싱 & 텍스트 설명 수집
        start_iso, end_iso = parse_period(period_text)

        noimg_list = [
            f"{r.find('th').text.strip()}: {r.find('td').text.strip()}"
            for r in soup.select("article.noImgProduct tr")
            if r.find('th') and r.find('td')
        ]

        products = []
        for p in soup.select("article.twoProduct figure"):
            # 1) 줄바꿈 제거: 공백 하나로 통일
            brand_text = (
                p.select_one(".p_brandNm").get_text(" ", strip=True)
                if p.select_one(".p_brandNm")
                else ""
            )
            name_text = (
                p.select_one(".p_productNm").get_text(" ", strip=True)
                if p.select_one(".p_productNm")
                else ""
            )

            # 2) 해시태그 제거
            brand_text = " ".join(w for w in brand_text.split() if not w.startswith("#"))

            # 3) 분류 토큰 제거
            if brand_text.upper() in ("MEN", "WOMEN", "MEN/WOMEN"):
                brand_text = ""

            # 4) name_text가 비어있으면 brand_text → name_text
            if not name_text and brand_text:
                name_text, brand_text = brand_text, ""

            # 5) '[브랜드]' 둘러싼 경우 대괄호 제거
            if re.fullmatch(r"\[[^\]]+\]", brand_text):
                brand_text = brand_text[1:-1].strip()

            # 6) brand_text 없을 때 '[브랜드]제품명' 분리
            if not brand_text:
                m = re.match(r"^\[([^\]]+)\]\s*(.+)$", name_text)
                if m:
                    brand_text = m.group(1).strip()
                    name_text = m.group(2).strip()

            # 7) 변형 정보만 있는 경우(슬래시 포함) 합치기
            if brand_text and "/" in name_text:
                name_text = f"{brand_text} {name_text}"
                brand_text = ""

            # 8) 프로모션/증정 항목 건너뛰기
            if "증정" in brand_text or "구매시" in name_text or name_text.startswith("「"):
                continue

            # 9) SKU 코드만 있으면 건너뛰기
            if re.fullmatch(r"[A-Z0-9]+", name_text):
                continue

            # 가격 및 이미지 URL
            price_tag = p.select_one(".p_productPrc")
            price_txt = price_tag.get_text(" ", strip=True) if price_tag else ""
            img_tag = p.select_one(".p_productImg")
            img_url = img_tag["src"] if img_tag else ""

            # 최종 공백 정리
            name_text = " ".join(name_text.split())

            products.append({
                "브랜드": brand_text,
                "제품명": name_text,
                "가격": process_price_text(price_txt),
                "이미지": img_url
            })

        return {
            "상세 제목": title_text,
            "상세 기간": period_text,
            "시작일": start_iso,
            "종료일": end_iso,
            "텍스트 설명": noimg_list,
            "상품 리스트": products
        }

    except Exception as e:
        print(f"❌ 상세페이지 크롤링 실패: {e}")
        return {"상세 제목": "", "상세 기간": "", "시작일":"", "종료일":"", "텍스트 설명": [], "상품 리스트": []}

def fetch_event_detail_http(url):
    """Selenium 없이 HTTP로 상세 페이지를 파싱합니다."""
    try:
        import requests as _req
        html = _req.get(url, timeout=15).text
        soup = BeautifulSoup(html, "html.parser")

        title_el = soup.select_one("section.fixArea h2")
        title_text = title_el.text.strip() if title_el else ""

        period_el = soup.select_one("table.info td")
        period_text = period_el.text.strip() if period_el else ""
        start_iso, end_iso = parse_period(period_text)

        noimg_list = [
            f"{r.find('th').text.strip()}: {r.find('td').text.strip()}"
            for r in soup.select("article.noImgProduct tr")
            if r.find('th') and r.find('td')
        ]

        products = []
        for p in soup.select("article.twoProduct figure"):
            brand_text = (
                p.select_one(".p_brandNm").get_text(" ", strip=True)
                if p.select_one(".p_brandNm")
                else ""
            )
            name_text = (
                p.select_one(".p_productNm").get_text(" ", strip=True)
                if p.select_one(".p_productNm")
                else ""
            )
            brand_text = " ".join(w for w in brand_text.split() if not w.startswith("#"))
            if brand_text.upper() in ("MEN", "WOMEN", "MEN/WOMEN"):
                brand_text = ""
            if not name_text and brand_text:
                name_text, brand_text = brand_text, ""
            if re.fullmatch(r"\[[^\]]+\]", brand_text):
                brand_text = brand_text[1:-1].strip()
            if not brand_text:
                m = re.match(r"^\[([^\]]+)\]\s*(.+)$", name_text)
                if m:
                    brand_text = m.group(1).strip()
                    name_text = m.group(2).strip()
            if brand_text and "/" in name_text:
                name_text = f"{brand_text} {name_text}"
                brand_text = ""
            if "증정" in brand_text or "구매시" in name_text or name_text.startswith("「"):
                continue
            if re.fullmatch(r"[A-Z0-9]+", name_text):
                continue
            price_tag = p.select_one(".p_productPrc")
            price_txt = price_tag.get_text(" ", strip=True) if price_tag else ""
            img_tag = p.select_one(".p_productImg")
            img_url = img_tag["src"] if img_tag else ""
            name_text = " ".join(name_text.split())
            products.append({
                "브랜드": brand_text,
                "제품명": name_text,
                "가격": process_price_text(price_txt),
                "이미지": img_url
            })

        return {
            "상세 제목": title_text,
            "상세 기간": period_text,
            "시작일": start_iso,
            "종료일": end_iso,
            "텍스트 설명": noimg_list,
            "상품 리스트": products
        }
    except Exception as e:
        print(f"❌ 상세페이지(HTTP) 크롤링 실패: {e}")
        return {"상세 제목": "", "상세 기간": "", "시작일":"", "종료일":"", "텍스트 설명": [], "상품 리스트": []}
        
# --- HTML 페이지 생성
def generate_html(detail_data, event_id):
    global CFG
    # 템플릿 경로: 환경설정 우선, 없으면 기존 기본값
    template_path = None
    if CFG and CFG.get("TEMPLATE_PATH"):
        template_path = CFG["TEMPLATE_PATH"]
    else:
        template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates", "template.html")

    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    # 템플릿 변수 치환
    html = template
    # 제목/설명 정리: 개행 제거 및 JSON-LD용 이스케이프 값 추가
    import json as _json
    title_clean = detail_data["제목"].replace("\r", " ").replace("\n", " ").strip()
    desc_clean = detail_data["혜택 설명"].replace("\r", " ").strip()
    html = html.replace("{{제목}}", title_clean)
    html = html.replace("{{기간}}", detail_data["기간"])
    html = html.replace("{{상세 제목}}", detail_data["상세 제목"])
    html = html.replace("{{상세 기간}}", detail_data["상세 기간"])
    html = html.replace("{{썸네일}}", detail_data.get("썸네일", ""))
    html = html.replace("{{혜택 설명}}", desc_clean.replace("\n", "<br>"))
    # JSON-LD에 안전하게 삽입할 수 있도록 JSON 문자열로 이스케이프된 값 주입
    html = html.replace("{{제목_JSON}}", _json.dumps(title_clean, ensure_ascii=False))
    html = html.replace("{{혜택 설명_JSON}}", _json.dumps(desc_clean, ensure_ascii=False))
    html = html.replace("{{업데이트 날짜}}", datetime.today().strftime('%Y-%m-%d'))
    html = html.replace("{{시작일}}", detail_data.get("시작일", ""))
    html = html.replace("{{종료일}}", detail_data.get("종료일", ""))
    html = html.replace("{{지점명}}", detail_data.get("지점명", ""))
    html = html.replace("{{event_id}}", detail_data.get("id", ""))
    html = html.replace("{{상세 링크}}", detail_data.get("상세 링크", "#"))

    # 상품 리스트 HTML 생성 (이미지 저장 없이 URL만 사용)
    product_html = ""
    for p in detail_data["상품 리스트"]:
        product_html += f"""
        <div class='product'>
          <img
            src="{p['이미지']}"
            alt="{p['제품명']} 행사 이미지"
            loading="lazy" width="800" height="800"
          />
          <h3 class='name'>{p['제품명']}</h3>
          <p class='price'>{p['가격']}</p>
        </div>
        """

    html = html.replace("{{상품 목록}}", product_html)

    # pages 폴더에 SEO 친화적인 파일명으로 저장
    # 출력 디렉토리: 환경설정 우선, 없으면 기존 기본값
    output_dir = None
    if CFG and CFG.get("PAGES_DIR"):
        output_dir = CFG["PAGES_DIR"]
    else:
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../web/public/pages")
    os.makedirs(output_dir, exist_ok=True)
    
    # 지점명을 영문으로 변환
    branch_mapping = {
        "송도": "songdo",
        "김포": "gimpo", 
        "스페이스원": "spaceone"
    }
    
    branch = detail_data.get("지점명", "송도")
    branch_en = branch_mapping.get(branch, "songdo")
    
    # 제목을 URL 친화적으로 변환
    def slugify(text):
        import re
        # 한글을 유지하면서 특수문자 제거
        text = re.sub(r'[^\w\s가-힣]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        text = text.replace(' ', '-')
        text = re.sub(r'-+', '-', text)
        text = text.strip('-')
        return text.lower()
    
    title_slug = slugify(detail_data["제목"])
    
    # 새 URL 경로 생성
    url_path = f"{branch_en}/{title_slug}"
    filename = f"{branch_en}-{title_slug}.html"
    
    # 템플릿에 경로 변수 주입
    html = html.replace("{{filename}}", filename)
    # 사이트 기본 URL: 환경설정 사용
    site_base = (CFG or {}).get("SITE_BASE_URL", "https://discounts.deluxo.co.kr")
    pretty_path = f"{site_base.rstrip('/')}/{url_path}"
    html = html.replace("{{pretty_path}}", pretty_path)
    html = html.replace("{{site_base}}", site_base.rstrip('/'))
    html = html.replace("{{branch_en}}", branch_en)

    # 관련 행사(같은 지점) 3~5개 생성
    # 기준: 동일 브랜치 파일들 중 최근 수정 순 (현재 파일 제외)
    related_html = []
    try:
        import os as _os
        from bs4 import BeautifulSoup as _BS
        candidates = []
        for fn in _os.listdir(output_dir):
            if not fn.endswith('.html'):
                continue
            if not fn.startswith(f"{branch_en}-"):
                continue
            if fn == filename:
                continue
            path = _os.path.join(output_dir, fn)
            mtime = _os.path.getmtime(path)
            # 타이틀 추출
            title_text = None
            try:
                with open(path, 'r', encoding='utf-8') as rf:
                    soup = _BS(rf, 'html.parser')
                    h1 = soup.find('h1')
                    if h1 and h1.get_text(strip=True):
                        title_text = h1.get_text(strip=True)
            except Exception:
                title_text = None
            candidates.append((mtime, fn, title_text))
        # 최신순 정렬 후 상위 5개
        candidates.sort(key=lambda x: -x[0])
        for _, fn, title_text in candidates[:5]:
            slug = fn[len(branch_en)+1:-5]
            pretty = f"/{branch_en}/{slug}"
            title_display = title_text or slug
            related_html.append(f"<li><a href=\"{pretty}\">{title_display}</a></li>")
    except Exception:
        pass
    html = html.replace("{{관련 행사}}", "\n".join(related_html))
    
    # 파일명 생성 (pages 폴더 안에 저장)
    filename_html = os.path.join(output_dir, filename)
    
    # HTML 파일 저장
    with open(filename_html, "w", encoding="utf-8") as f:
        f.write(html)
    
    # URL 매핑에 추가 (개선된 포괄적 방식)
    event_id = detail_data.get("id", "")
    if event_id and 'url_mapping' in globals():
        mappings_count = add_comprehensive_mapping(event_id, filename)
        print(f"  📌 {mappings_count}개 변형 매핑 추가: {event_id} → {filename}")
    
    print(f"✔ SEO 친화적인 HTML 생성 완료: {url_path}")
    
    return url_path

def add_comprehensive_mapping(event_id, filename):
    """모든 가능한 event_id 변형들을 매핑에 추가하여 근본적으로 링크 문제 해결"""
    global url_mapping
    
    if not event_id:
        return 0
    
    mappings_added = 0
    
    # 1. 기본 event_id 매핑 추가
    url_mapping[event_id] = filename
    mappings_added += 1
    
    # 2. _02 패턴 처리
    if event_id.endswith('_02'):
        # _02가 있으면 기본 ID도 추가
        base_id = event_id[:-3]
        if base_id not in url_mapping:
            url_mapping[base_id] = filename
            mappings_added += 1
    else:
        # 기본 ID면 _02 변형도 추가
        extended_id = event_id + '_02'
        if extended_id not in url_mapping:
            url_mapping[extended_id] = filename
            mappings_added += 1
    
    # 3. _03, _04 등 추가 변형 예방적 추가
    if not any(event_id.endswith(suffix) for suffix in ['_02', '_03', '_04']):
        for suffix in ['_03', '_04']:
            variant_id = event_id + suffix
            if variant_id not in url_mapping:
                url_mapping[variant_id] = filename
                mappings_added += 1
    
    # 4. 길이별 변형 처리 (12자리 ↔ 9자리)
    if len(event_id) == 12 and not any(event_id.endswith(suffix) for suffix in ['_02', '_03', '_04']):
        # 12자리면 9자리 변형도 추가
        short_id = event_id[:9]
        for suffix in ['', '_02', '_03', '_04']:
            short_variant = short_id + suffix
            if short_variant not in url_mapping:
                url_mapping[short_variant] = filename
                mappings_added += 1
    
    return mappings_added

def generate_sitemap(pages_dir, base_url, output_path):
    urls = []
    # ── ① 루트 페이지(https://discounts.deluxo.co.kr/) 추가
    today = datetime.today().strftime('%Y-%m-%d')
    # base_url은 "https://discounts.deluxo.co.kr" 기준
    site_root = base_url.rstrip('/') + '/'
    urls.append((site_root, today))
    # ── ② (선택) privacy.html 같은 정적 페이지 추가
    urls.append((site_root + "privacy.html", today))
    
    # 새로운 SEO 친화적인 URL 구조의 파일들 처리 (프리티 URL 사용)
    for filename in os.listdir(pages_dir):
        if filename.endswith(".html") and '-' in filename and not filename.startswith('index'):
            filepath = os.path.join(pages_dir, filename)
            lastmod = datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d')
            name_without_ext = filename[:-5]  # strip .html
            if name_without_ext.startswith('songdo-'):
                url_path = name_without_ext.replace('songdo-', 'songdo/')
            elif name_without_ext.startswith('gimpo-'):
                url_path = name_without_ext.replace('gimpo-', 'gimpo/')
            elif name_without_ext.startswith('spaceone-'):
                url_path = name_without_ext.replace('spaceone-', 'spaceone/')
            else:
                continue
            url = f"{base_url.rstrip('/')}/{url_path}"
            urls.append((url, lastmod))

    # 이벤트 허브 페이지가 있으면 포함
    events_dir = os.path.abspath(os.path.join(pages_dir, '..', 'events'))
    if os.path.isdir(events_dir):
        for fn in os.listdir(events_dir):
            if not fn.endswith('.html'):
                continue
            fp = os.path.join(events_dir, fn)
            lastmod = datetime.fromtimestamp(os.path.getmtime(fp)).strftime('%Y-%m-%d')
            url = f"{base_url.rstrip('/')}/events/{fn}"
            if fn == 'index.html':
                url = f"{base_url.rstrip('/')}/events/"
            urls.append((url, lastmod))

    sitemap = ['<?xml version="1.0" encoding="UTF-8"?>']
    sitemap.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    for url, lastmod in urls:
        sitemap.append("  <url>")
        sitemap.append(f"    <loc>{url}</loc>")
        sitemap.append(f"    <lastmod>{lastmod}</lastmod>")
        sitemap.append("    <changefreq>daily</changefreq>")
        prio = "1.0" if url.rstrip("/") == site_root.rstrip("/") else "0.8"
        sitemap.append(f"    <priority>{prio}</priority>")
        sitemap.append("  </url>")
    sitemap.append('</urlset>')

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(sitemap))
    print(f"✔ 새로운 URL 구조의 sitemap.xml 생성 완료: {output_path}")

def generate_index(pages_dir, index_path):
    import os
    from datetime import datetime
    from bs4 import BeautifulSoup

    links = []
    for fn in sorted(os.listdir(pages_dir)):
        if not (fn.startswith("event-") and fn.endswith(".html")):
            continue
        filepath = os.path.join(pages_dir, fn)
        # ① 파일 열어서 제목(<h1> 또는 템플릿 구조에 맞는 요소) 파싱
        with open(filepath, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")
            # 예시: 상세페이지 템플릿에서 <h1>태그에 이벤트 제목이 있다면
            title_el = soup.select_one("h1") or soup.select_one("section.fixArea h2")
            title = title_el.get_text(strip=True) if title_el else fn.replace("event-", "").replace(".html","")
        url = f"pages/{fn}"
        links.append((title, url))

    # 상위 5개와 전체 리스트 분리
    preview_links = links[:5]
    full_links    = links

    # <li> 문자열로 변환
    preview_lis = "\n".join(f'    <li><a href="{u}">{t}</a></li>' for t,u in preview_links)
    full_lis    = "\n".join(f'    <li><a href="{u}">{t}</a></li>' for t,u in full_links)

    # 템플릿 로드
    # 인덱스 템플릿 경로: 환경설정 우선
    global CFG
    tpl_path = None
    if CFG and CFG.get("INDEX_TEMPLATE_PATH"):
        tpl_path = CFG["INDEX_TEMPLATE_PATH"]
    else:
        tpl_path = os.path.join(os.path.dirname(__file__), "index.tpl.html")
    tpl = open(tpl_path, encoding="utf-8").read()

    # 자리표시자 치환
    html = tpl.replace("{{PREVIEW_LINKS}}", preview_lis)
    html = html.replace("{{EVENT_LINKS}}", full_lis)

    # 결과 저장
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✔ index.html 생성 완료: {index_path}")


# --- Google Sheets 업로드
def upload_to_google_sheet(sheet_title, sheet_name, new_rows):
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    today_str = datetime.today().strftime('%Y-%m-%d')
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    # 자격증명 경로: ENV 우선 → 신규 기본경로(apps/crawler/credentials.json) → 레거시(outlet-crawler/credentials.json)
    cred_env = os.environ.get("OUTLET_CREDENTIALS_PATH")
    if cred_env and os.path.exists(cred_env):
        credential_path = cred_env
    else:
        new_default = os.path.join(BASE_DIR, "credentials.json")
        legacy_default = os.path.join(BASE_DIR, "..", "..", "outlet-crawler", "credentials.json")
        if os.path.exists(new_default):
            credential_path = new_default
        elif os.path.exists(legacy_default):
            credential_path = legacy_default
        else:
            raise FileNotFoundError("Google credentials.json not found. Set OUTLET_CREDENTIALS_PATH or place it under apps/crawler/ or outlet-crawler/.")

    creds = ServiceAccountCredentials.from_json_keyfile_name(credential_path, scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open(sheet_title)
    try:
        worksheet = spreadsheet.worksheet(sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=sheet_name, rows="1000", cols="20")

    headers = ["제목", "기간", "상세 제목", "상세 기간", "썸네일", "상세 링크", "혜택 설명",
               "브랜드", "제품명", "가격", "이미지", "업데이트 날짜", "event_id"]
    try:
        existing_data = worksheet.get_all_values()
        if existing_data and existing_data[0] == headers:
            existing_data = existing_data[1:]
    except:
        existing_data = []

    existing_links = {row[5] for row in existing_data if len(row) >= 6}
    filtered_new_rows = [row for row in new_rows if len(row) >= 6 and row[5] not in existing_links]
    print(f"✨ [{sheet_name}] 새로 추가할 항목 수: {len(filtered_new_rows)}개")

    if not filtered_new_rows:
        print(f"✅ [{sheet_name}] 추가할 데이터 없음.")
        return

    all_data = [headers] + filtered_new_rows + existing_data
    worksheet.clear()
    worksheet.update('A1', all_data)
    print(f"✅ [{sheet_name}] 총 {len(all_data)-1}개 데이터 저장 완료.")
    print(f"🔗 시트 링크: https://docs.google.com/spreadsheets/d/{spreadsheet.id}/edit")

# --- 아울렛 크롤링
def crawl_outlet(branchCd, outletName, sheet_name):
    import os as _os
    listing_mode = _os.environ.get("OUTLET_LISTING_MODE", "http").lower()
    detail_mode = _os.environ.get("OUTLET_DETAIL_MODE", "selenium").lower()
    driver = None
    # 드라이버는 필요한 경우에만 띄움 (listing click 또는 detail selenium)
    if listing_mode != "http" or detail_mode == "selenium":
        driver = setup_driver()
    new_rows = []
    # Max pages can be overridden via env (OUTLET_MAX_PAGES)
    import os as _os
    try:
        max_pages = int(_os.environ.get("OUTLET_MAX_PAGES", "4"))
    except Exception:
        max_pages = 4
    for page in range(1, max_pages + 1):
        print(f"[{sheet_name}] 페이지 {page} 크롤링 중...")
        events = fetch_event_list(driver, branchCd, page)
        for event in events:
            # HTTP 모드(dict)와 클릭/폴백 모드(li)를 모두 지원
            if isinstance(event, dict):
                title = event.get('title', '')
                period = event.get('period', '')
                image_url = event.get('image', '')
                detail_url = event.get('link', '')
            else:
                title_tag = event.select_one(".info_tit")
                period_tag = event.select_one(".info_txt")
                img_tag = event.select_one("img")
                link_tag = event.select_one("a")
                title = title_tag.get_text(separator=" ", strip=True) if title_tag else ""
                period = period_tag.get_text(strip=True) if period_tag else ""
                image_url = img_tag["src"] if img_tag else ""
                detail_url = "https://www.ehyundai.com" + link_tag["href"] if link_tag else ""
            if detail_mode == "http":
                detail = fetch_event_detail_http(detail_url)
            else:
                detail = fetch_event_detail(driver, detail_url)
            thumbnail_id = image_url.split("/")[-1].split(".")[0][-12:]
            event_id = thumbnail_id
            detail_data = {
                "id":       event_id,
                "제목":     title,
                "기간":     period,
                "상세 제목": detail["상세 제목"],
                "상세 기간": detail["상세 기간"],
                "시작일":   detail["시작일"],    # ← ISO 시작일
                "종료일":   detail["종료일"],    # ← ISO 종료일
                "지점명":   outletName,          # ← 지점명 추가
                "썸네일":   image_url,
                "상세 링크": detail_url,
                "혜택 설명":" / ".join(detail["텍스트 설명"]),
                "상품 리스트": detail["상품 리스트"]
            }
            url_path = generate_html(detail_data, event_id)
            base_info = [title, period, detail["상세 제목"], detail["상세 기간"],
                         image_url, detail_url, detail_data["혜택 설명"]]
            if detail["상품 리스트"]:
                for p in detail["상품 리스트"]:
                    row = base_info + [
                        p["브랜드"], p["제품명"], p["가격"], p["이미지"],
                        datetime.today().strftime('%Y-%m-%d'), event_id]
                    new_rows.append(row)
            else:
                new_rows.append(base_info + ["", "", "", "",
                                 datetime.today().strftime('%Y-%m-%d'), event_id])
    if driver:
        driver.quit()
    # Allow skipping Google Sheets upload for dry-run via OUTLET_SKIP_SHEETS
    import os as _os
    if _os.environ.get("OUTLET_SKIP_SHEETS", "").lower() in ("1", "true", "yes"):
        print("⚠️ OUTLET_SKIP_SHEETS=1: Google Sheets 업로드를 생략합니다.")
    else:
        upload_to_google_sheet("outlet-data", sheet_name, new_rows)

# --- 메인 실행
def main():
    # 기존 URL 매핑 파일 읽기 (누적 방식으로 변경)
    import json
    global CFG
    if CFG is None:
        CFG = _get_config()

    mapping_path = CFG.get("MAPPING_PATH")
    global url_mapping
    try:
        with open(mapping_path, "r", encoding="utf-8") as f:
            url_mapping = json.load(f)
        print(f"📋 기존 URL 매핑 로드: {len(url_mapping)}개 항목")
    except:
        url_mapping = {}
        print("📋 새로운 URL 매핑 파일 생성")

    OUTLET_TARGETS = [
        ("B00174000", "송도",     "Sheet1"),
        ("B00172000", "김포",     "Sheet2"),
        ("B00178000", "스페이스원","Sheet3"),
    ]

    # 크롤링 시작 전 매핑 개수
    initial_count = len(url_mapping)

    for branchCd, outletName, sheet_name in OUTLET_TARGETS:
        crawl_outlet(branchCd, outletName, sheet_name)
    
    # URL 매핑 JSON 파일 저장 (기존 + 새로운 매핑)
    with open(mapping_path, "w", encoding="utf-8") as f:
        json.dump(url_mapping, f, ensure_ascii=False, indent=2)
    
    new_count = len(url_mapping) - initial_count
    print(f"📋 URL 매핑 파일 업데이트: 기존 {initial_count}개 + 신규 {new_count}개 = 총 {len(url_mapping)}개 항목")

    # ✅ 새로운 URL 구조의 sitemap.xml 생성
    generate_sitemap(
        pages_dir=CFG.get("PAGES_DIR"),
        base_url=CFG.get("SITE_BASE_URL"),
        output_path=CFG.get("SITEMAP_PATH"),
    )

    # ✅ index.html (정적 이벤트 링크 목록) 생성
    generate_index(
        pages_dir=CFG.get("PAGES_DIR"),
        index_path=CFG.get("INDEX_OUTPUT_PATH"),
    )

    print("\n🎉 전체 아울렛 크롤링 및 저장 + 새로운 URL 구조의 sitemap 생성 완료!")
    print("🔗 새로운 URL 구조: discounts.deluxo.co.kr/pages/{지점명}-{제목}.html")

if __name__ == "__main__":
    main()
