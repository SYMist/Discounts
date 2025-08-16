#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
from bs4 import BeautifulSoup

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
        print(f"❌ {html_file_path} 파일 읽기 실패: {e}")
        return None, None

def generate_redirect_rules():
    """기존 이벤트 파일들을 분석하여 리다이렉트 규칙을 생성합니다."""
    
    pages_dir = "pages"
    if not os.path.exists(pages_dir):
        print(f"❌ {pages_dir} 디렉토리를 찾을 수 없습니다.")
        return
    
    # 지점명을 영문으로 매핑
    branch_mapping = {
        "송도": "songdo",
        "김포": "gimpo", 
        "스페이스원": "spaceone"
    }
    
    redirect_rules = []
    
    # pages 디렉토리의 모든 HTML 파일 처리
    for filename in os.listdir(pages_dir):
        if filename.startswith('event-') and filename.endswith('.html'):
            filepath = os.path.join(pages_dir, filename)
            title, branch = extract_event_info(filepath)
            
            if title and branch:
                # 제목을 URL 친화적으로 변환
                title_slug = re.sub(r'[^\w\s가-힣]', '', title)
                title_slug = re.sub(r'\s+', '-', title_slug.strip())
                title_slug = title_slug.lower()
                
                branch_en = branch_mapping.get(branch, "unknown")
                
                # 리다이렉트 규칙 생성
                old_url = f"pages/{filename}"
                new_url = f"{branch_en}/{title_slug}"
                
                redirect_rules.append({
                    'old_url': old_url,
                    'new_url': new_url,
                    'title': title,
                    'branch': branch
                })
                
                print(f"✅ {old_url} → {new_url}")
    
    return redirect_rules

def update_htaccess(redirect_rules):
    """htaccess 파일에 리다이렉트 규칙을 추가합니다."""
    
    htaccess_file = ".htaccess"
    
    if not os.path.exists(htaccess_file):
        print(f"❌ {htaccess_file} 파일을 찾을 수 없습니다.")
        return
    
    # 기존 htaccess 파일 읽기
    with open(htaccess_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 리다이렉트 규칙 섹션 찾기
    redirect_section = "# 2. 기존 pages/event-*.html 파일들을 새로운 구조로 리다이렉트 (301 리다이렉트)"
    
    if redirect_section in content:
        # 기존 주석 처리된 부분을 실제 규칙으로 교체
        new_rules = []
        new_rules.append("# 2. 기존 pages/event-*.html 파일들을 새로운 구조로 리다이렉트 (301 리다이렉트)")
        
        for rule in redirect_rules:
            new_rules.append(f"RewriteRule ^{rule['old_url']}$ /{rule['new_url']} [R=301,L]")
        
        new_rules.append("")
        
        # 기존 주석 처리된 부분 교체
        old_pattern = r"# 2\. 기존 pages/event-.*?RewriteRule.*?새로운-제목.*?\]\n"
        new_content = re.sub(old_pattern, '\n'.join(new_rules), content, flags=re.DOTALL)
        
        # 파일에 쓰기
        with open(htaccess_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✅ {htaccess_file} 파일이 업데이트되었습니다.")
        
        # 백업 파일 생성
        backup_file = ".htaccess.backup"
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ 백업 파일 {backup_file}이 생성되었습니다.")
        
    else:
        print(f"❌ {htaccess_file}에서 리다이렉트 섹션을 찾을 수 없습니다.")

def main():
    print("🔄 리다이렉트 규칙 생성 중...")
    
    # 리다이렉트 규칙 생성
    redirect_rules = generate_redirect_rules()
    
    if redirect_rules:
        print(f"\n📊 총 {len(redirect_rules)}개의 리다이렉트 규칙이 생성되었습니다.")
        
        # htaccess 파일 업데이트
        update_htaccess(redirect_rules)
        
        print("\n🎉 리다이렉트 규칙 생성 완료!")
        print("이제 기존 URL로 접근하면 새로운 URL로 자동 리다이렉트됩니다.")
        
    else:
        print("❌ 리다이렉트 규칙을 생성할 수 없습니다.")

if __name__ == "__main__":
    main() 