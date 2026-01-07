#!/usr/bin/env python3
"""
기존 페이지들의 SEO 문제 일괄 수정
- 잘못된 날짜 형식 수정
- 종료된 이벤트에 noindex 추가
- Event 스키마 → Article 스키마 전환 (종료/날짜없음)
"""

import os
import re
import json
from datetime import datetime
from bs4 import BeautifulSoup

PAGES_DIR = os.path.join(os.path.dirname(__file__), "../public/pages")

def get_event_status(start_date_iso, end_date_iso):
    """이벤트 상태 반환: 'active', 'upcoming', 'expired'"""
    today = datetime.today().date()
    try:
        if end_date_iso:
            end_date = datetime.strptime(end_date_iso, "%Y-%m-%d").date()
            if end_date < today:
                return "expired"
        if start_date_iso:
            start_date = datetime.strptime(start_date_iso, "%Y-%m-%d").date()
            if start_date > today:
                return "upcoming"
        return "active"
    except ValueError:
        return "active"

def extract_dates_from_jsonld(content):
    """JSON-LD에서 날짜 추출"""
    start_match = re.search(r'"startDate"\s*:\s*"([^"]*)"', content)
    end_match = re.search(r'"endDate"\s*:\s*"([^"]*)"', content)

    start = start_match.group(1) if start_match else ""
    end = end_match.group(1) if end_match else ""

    # 잘못된 형식 정리 (예: "2025-09-7까지" → "")
    if start and not re.match(r'^\d{4}-\d{2}-\d{2}$', start):
        start = ""
    if end and not re.match(r'^\d{4}-\d{2}-\d{2}$', end):
        end = ""

    return start, end

def extract_info_from_page(content):
    """페이지에서 정보 추출"""
    soup = BeautifulSoup(content, 'html.parser')

    # 제목
    h1 = soup.find('h1')
    title = h1.get_text(strip=True) if h1 else ""

    # 썸네일
    img = soup.find('img', class_='thumbnail')
    thumbnail = img.get('src', '') if img else ""

    # 지점
    branch = ""
    if 'songdo' in content.lower():
        branch = "송도"
    elif 'gimpo' in content.lower():
        branch = "김포"
    elif 'spaceone' in content.lower():
        branch = "스페이스원"

    # description
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    description = meta_desc.get('content', '') if meta_desc else title

    return title, description, thumbnail, branch

def generate_article_schema(title, description, thumbnail, update_date):
    """Article 스키마 생성"""
    schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": description,
        "image": thumbnail if thumbnail else "",
        "datePublished": update_date,
        "dateModified": update_date,
        "author": {
            "@type": "Organization",
            "name": "현대백화점"
        },
        "publisher": {
            "@type": "Organization",
            "name": "현대 프리미엄 아울렛",
            "url": "https://www.ehyundai.com"
        }
    }
    return f'<script type="application/ld+json">\n  {json.dumps(schema, ensure_ascii=False, indent=2)}\n  </script>'

def fix_page(filepath):
    """단일 페이지 수정"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    changes = []

    # 1. 날짜 추출
    start_date, end_date = extract_dates_from_jsonld(content)
    status = get_event_status(start_date, end_date)

    # 2. noindex 처리 (종료된 이벤트)
    has_noindex = 'name="robots" content="noindex' in content
    if status == "expired" and not has_noindex:
        # viewport 메타 태그 다음에 noindex 추가
        noindex_tag = '<meta name="robots" content="noindex, follow">'
        content = content.replace(
            '<meta name="viewport"',
            f'{noindex_tag}\n  <meta name="viewport"'
        )
        changes.append("noindex 추가")

    # 3. 잘못된 JSON-LD 수정 (빈 날짜, 비표준 형식)
    # Event 스키마가 있고 (종료됐거나 날짜가 없으면) Article로 교체
    if '"@type": "Event"' in content or '"@type":"Event"' in content:
        has_valid_dates = bool(start_date and end_date)

        if not has_valid_dates or status == "expired":
            title, description, thumbnail, branch = extract_info_from_page(content)
            update_date = datetime.today().strftime('%Y-%m-%d')

            # 기존 Event 스키마 제거 후 Article 스키마로 교체
            # JSON-LD 블록 찾기
            pattern = r'<script type="application/ld\+json">\s*\{[^}]*"@type"\s*:\s*"Event"[^<]*</script>'
            new_schema = generate_article_schema(title, description, thumbnail, update_date)

            if re.search(pattern, content, re.DOTALL):
                content = re.sub(pattern, new_schema, content, flags=re.DOTALL)
                changes.append("Event→Article 스키마 전환")

    # 4. 잘못된 endDate 형식 수정 (예: "2025-09-7까지")
    bad_date_pattern = r'"endDate"\s*:\s*"[^"]*까지"'
    if re.search(bad_date_pattern, content):
        content = re.sub(bad_date_pattern, '"endDate": ""', content)
        changes.append("잘못된 endDate 형식 수정")

    # 변경사항 있으면 저장
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return changes
    return []

def main():
    print("🔧 기존 페이지 SEO 문제 일괄 수정 시작...")

    fixed_count = 0
    noindex_count = 0
    schema_count = 0

    pages = [f for f in os.listdir(PAGES_DIR) if f.endswith('.html')]
    total = len(pages)

    for i, filename in enumerate(pages, 1):
        filepath = os.path.join(PAGES_DIR, filename)
        changes = fix_page(filepath)

        if changes:
            fixed_count += 1
            if "noindex 추가" in changes:
                noindex_count += 1
            if "Event→Article 스키마 전환" in changes:
                schema_count += 1
            print(f"  [{i}/{total}] {filename}: {', '.join(changes)}")

    print(f"\n✅ 완료!")
    print(f"   - 수정된 파일: {fixed_count}개")
    print(f"   - noindex 추가: {noindex_count}개")
    print(f"   - 스키마 전환: {schema_count}개")

if __name__ == "__main__":
    main()
