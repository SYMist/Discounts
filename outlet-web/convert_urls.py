#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import shutil
from bs4 import BeautifulSoup
from urllib.parse import quote

def extract_event_info(html_file_path):
    """HTML 파일에서 이벤트 정보를 추출합니다."""
    try:
        with open(html_file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html')
        
        # 제목 추출
        title_elem = soup.find('h1')
        title = title_elem.text.strip() if title_elem else "Unknown Event"
        
        # 지점명 추출 (JSON-LD에서)
        script_elem = soup.find('script', type='application/ld+json')
        branch = "송도"  # 기본값
        
        if script_elem:
            script_text = script_elem.string
            if '"name": "현대 프리미엄 아울렛 송도"' in script_text:
                branch = "송도"
            elif '"name": "현대 프리미엄 아울렛 김포"' in script_text:
                branch = "김포"
            elif '"name": "현대 프리미엄 아울렛 스페이스원"' in script_text:
                branch = "스페이스원"
        
        return title, branch
    except Exception as e:
        print(f"❌ 파일 읽기 실패 {html_file_path}: {e}")
        return None, None

def generate_seo_url(title, branch):
    """SEO 친화적인 URL을 생성합니다."""
    branch_mapping = {
        "송도": "songdo",
        "김포": "gimpo", 
        "스페이스원": "spaceone"
    }
    
    branch_en = branch_mapping.get(branch, "unknown")
    
    def slugify(text):
        # 한글을 유지하면서 특수문자 제거
        text = re.sub(r'[^\w\s가-힣]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        text = text.replace(' ', '-')
        text = re.sub(r'-+', '-', text)
        text = text.strip('-')
        return text.lower()
    
    title_slug = slugify(title)
    return f"{branch_en}/{title_slug}"

def convert_file_to_new_structure(old_file_path, new_dir):
    """파일을 새로운 구조로 변환합니다."""
    title, branch = extract_event_info(old_file_path)
    
    if not title or not branch:
        return None
    
    # 새 URL 경로 생성
    url_path = generate_seo_url(title, branch)
    new_file_path = os.path.join(new_dir, f"{url_path.replace('/', '-')}.html")
    
    # 새 디렉토리 생성
    os.makedirs(os.path.dirname(new_file_path), exist_ok=True)
    
    # 파일 복사
    shutil.copy2(old_file_path, new_file_path)
    
    # 새 파일 내용 수정 (링크 업데이트)
    update_file_content(new_file_path, url_path)
    
    return url_path

def update_file_content(file_path, url_path):
    """파일 내용을 새로운 URL 구조에 맞게 업데이트합니다."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 상대 경로 링크를 새 구조로 업데이트
        content = content.replace('href="../index.html"', 'href="/"')
        content = content.replace('onclick="if(history.length>1){history.back()}else{location.href=\'../index.html\'}"', 
                                'onclick="if(history.length>1){history.back()}else{location.href=\'/\'}"')
        
        # canonical URL 업데이트
        new_canonical = f"https://discounts.deluxo.co.kr/{url_path}"
        content = re.sub(r'<link rel="canonical" href="[^"]*" />', 
                        f'<link rel="canonical" href="{new_canonical}" />', content)
        
        # og:url 업데이트
        content = re.sub(r'<meta property="og:url" content="[^"]*"', 
                        f'<meta property="og:url" content="{new_canonical}"', content)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
    except Exception as e:
        print(f"❌ 파일 내용 업데이트 실패 {file_path}: {e}")

def create_redirect_file(old_filename, new_url_path, redirect_dir):
    """기존 파일에 대한 301 리다이렉트 HTML 파일을 생성합니다."""
    redirect_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>페이지가 이동되었습니다</title>
    <meta http-equiv="refresh" content="0; url=/{new_url_path}">
    <link rel="canonical" href="https://discounts.deluxo.co.kr/{new_url_path}" />
</head>
<body>
    <p>페이지가 <a href="/{new_url_path}">새로운 주소</a>로 이동되었습니다.</p>
    <script>window.location.href = "/{new_url_path}";</script>
</body>
</html>"""
    
    redirect_file = os.path.join(redirect_dir, old_filename)
    with open(redirect_file, 'w', encoding='utf-8') as f:
        f.write(redirect_html)

def main():
    """메인 변환 프로세스"""
    pages_dir = "pages"
    new_base_dir = "."
    
    if not os.path.exists(pages_dir):
        print(f"❌ {pages_dir} 디렉토리를 찾을 수 없습니다.")
        return
    
    print("🔄 URL 구조 변환 시작...")
    print("=" * 60)
    
    converted_files = []
    
    # 기존 이벤트 파일들 처리
    for filename in os.listdir(pages_dir):
        if filename.startswith("event-") and filename.endswith(".html"):
            old_file_path = os.path.join(pages_dir, filename)
            print(f"📄 처리 중: {filename}")
            
            # 새 구조로 변환
            new_url_path = convert_file_to_new_structure(old_file_path, new_base_dir)
            
            if new_url_path:
                converted_files.append((filename, new_url_path))
                print(f"✅ 변환 완료: {new_url_path}")
            else:
                print(f"❌ 변환 실패: {filename}")
    
    # 리다이렉트 파일 생성
    print("\n🔄 리다이렉트 파일 생성 중...")
    redirect_dir = "redirects"
    os.makedirs(redirect_dir, exist_ok=True)
    
    for old_filename, new_url_path in converted_files:
        create_redirect_file(old_filename, new_url_path, redirect_dir)
        print(f"✅ 리다이렉트 생성: {old_filename} → {new_url_path}")
    
    print(f"\n🎉 변환 완료! 총 {len(converted_files)}개 파일이 처리되었습니다.")
    print(f"📁 새 파일들은 {new_base_dir} 디렉토리에 생성되었습니다.")
    print(f"🔄 리다이렉트 파일들은 {redirect_dir} 디렉토리에 생성되었습니다.")

if __name__ == "__main__":
    main() 