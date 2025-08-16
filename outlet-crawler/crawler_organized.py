import time
import gspread
import os
import requests
import re
from bs4 import BeautifulSoup
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- 전역 변수
url_mapping = {}

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
    list_url = f"https://www.ehyundai.com/newPortal/SN/SN_0101000.do?branchCd={branchCd}&SN=1"
    driver.get(list_url)
    time.sleep(2)
    driver.execute_script(f"getContents('01', {page}, 0);")
    time.sleep(3)
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
        
# --- HTML 페이지 생성
def generate_html(detail_data, event_id):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(BASE_DIR, "template.html")
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    # 템플릿 변수 치환
    html = template
    html = html.replace("{{제목}}", detail_data["제목"])
    html = html.replace("{{기간}}", detail_data["기간"])
    html = html.replace("{{상세 제목}}", detail_data["상세 제목"])
    html = html.replace("{{상세 기간}}", detail_data["상세 기간"])
    html = html.replace("{{썸네일}}", detail_data.get("썸네일", ""))
    html = html.replace("{{혜택 설명}}", detail_data["혜택 설명"].replace("\n", "<br>"))
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
    output_dir = os.path.join(BASE_DIR, "../outlet-web/pages")
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
    
    # filename 변수를 템플릿에 추가
    html = html.replace("{{filename}}", filename)
    
    # 파일명 생성 (pages 폴더 안에 저장)
    filename_html = os.path.join(output_dir, filename)
    
    # HTML 파일 저장
    with open(filename_html, "w", encoding="utf-8") as f:
        f.write(html)
    
    # URL 매핑에 추가 (전역 변수 사용)
    event_id = detail_data.get("id", "")
    if event_id and 'url_mapping' in globals():
        url_mapping[event_id] = filename
    
    print(f"✔ SEO 친화적인 HTML 생성 완료: {url_path}")
    
    return url_path

def generate_sitemap(pages_dir, base_url, output_path):
    urls = []
    # ── ① 루트 페이지(https://discounts.deluxo.co.kr/) 추가
    today = datetime.today().strftime('%Y-%m-%d')
    # base_url이 "https://discounts.deluxo.co.kr/pages" 라면
    site_root = base_url.rsplit("/", 1)[0] + "/"
    urls.append((site_root, today))
    # ── ② (선택) privacy.html 같은 정적 페이지 추가
    urls.append((site_root + "privacy.html", today))
    
    # 새로운 SEO 친화적인 URL 구조의 파일들 처리
    for filename in os.listdir(pages_dir):
        if filename.endswith(".html") and '-' in filename and not filename.startswith('index'):
            filepath = os.path.join(pages_dir, filename)
            lastmod = datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d')
            
            # 파일명을 URL 경로로 변환
            name_without_ext = filename.replace('.html', '')
            if name_without_ext.startswith('songdo-'):
                url_path = name_without_ext.replace('songdo-', 'songdo/')
            elif name_without_ext.startswith('gimpo-'):
                url_path = name_without_ext.replace('gimpo-', 'gimpo/')
            elif name_without_ext.startswith('spaceone-'):
                url_path = name_without_ext.replace('spaceone-', 'spaceone/')
            else:
                continue
            
            url = f"{base_url}/{url_path}"
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
    today_str = datetime.today().strftime('%Y-%m-%d')
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    CREDENTIAL_PATH = os.path.join(BASE_DIR, "credentials.json")
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIAL_PATH, scope)
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
    driver = setup_driver()
    new_rows = []
    for page in range(1, 5):
        print(f"[{sheet_name}] 페이지 {page} 크롤링 중...")
        events = fetch_event_list(driver, branchCd, page)
        for event in events:
            title_tag = event.select_one(".info_tit")
            period_tag = event.select_one(".info_txt")
            img_tag = event.select_one("img")
            link_tag = event.select_one("a")
            title = title_tag.get_text(separator=" ", strip=True) if title_tag else ""
            period = period_tag.get_text(strip=True) if period_tag else ""
            image_url = img_tag["src"] if img_tag else ""
            detail_url = "https://www.ehyundai.com" + link_tag["href"] if link_tag else ""
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
    driver.quit()
    upload_to_google_sheet("outlet-data", sheet_name, new_rows)

# --- 메인 실행
def main():
    OUTLET_TARGETS = [
        ("B00174000", "송도",     "Sheet1"),
        ("B00172000", "김포",     "Sheet2"),
        ("B00178000", "스페이스원","Sheet3"),
    ]

    for branchCd, outletName, sheet_name in OUTLET_TARGETS:
        crawl_outlet(branchCd, outletName, sheet_name)
    
    # URL 매핑 JSON 파일 생성
    import json
    mapping_path = os.path.join(os.path.dirname(__file__), "../outlet-web/url-mapping.json")
    with open(mapping_path, "w", encoding="utf-8") as f:
        json.dump(url_mapping, f, ensure_ascii=False, indent=2)
    print(f"📋 URL 매핑 파일 생성: {len(url_mapping)}개 항목")

    # ✅ 새로운 URL 구조의 sitemap.xml 생성
    generate_sitemap(
        pages_dir=os.path.join(os.path.dirname(__file__), "../outlet-web/pages"),
        base_url="https://discounts.deluxo.co.kr/pages",
        output_path=os.path.join(os.path.dirname(__file__), "../outlet-web/sitemap.xml")
    )

    # ✅ index.html (정적 이벤트 링크 목록) 생성
    generate_index(
        pages_dir=os.path.join(os.path.dirname(__file__), "../outlet-web/pages"),
        index_path=os.path.join(os.path.dirname(__file__), "../outlet-web/index.html")
    )

    print("\n🎉 전체 아울렛 크롤링 및 저장 + 새로운 URL 구조의 sitemap 생성 완료!")
    print("🔗 새로운 URL 구조: discounts.deluxo.co.kr/pages/{지점명}-{제목}.html")

if __name__ == "__main__":
    main()