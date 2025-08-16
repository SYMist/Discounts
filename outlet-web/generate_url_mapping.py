#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
기존 HTML 파일들에서 event_id와 새로운 파일명의 매핑을 생성하는 스크립트
"""

import os
import re
import json
from bs4 import BeautifulSoup

def extract_event_id_from_html(html_content):
    """HTML 내용에서 event_id를 추출"""
    # canonical 링크에서 event ID 추출
    soup = BeautifulSoup(html_content, 'html.parser')
    canonical = soup.find('link', rel='canonical')
    if canonical and canonical.get('href'):
        href = canonical.get('href')
        # event-xxx.html 패턴에서 ID 추출
        match = re.search(r'event-([^.]+)\.html', href)
        if match:
            return match.group(1)
    return None

def generate_url_mapping():
    """pages 폴더의 모든 HTML 파일을 스캔하여 URL 매핑 생성"""
    pages_dir = "pages"
    url_mapping = {}
    
    if not os.path.exists(pages_dir):
        print(f"❌ {pages_dir} 폴더가 존재하지 않습니다.")
        return
    
    html_files = [f for f in os.listdir(pages_dir) if f.endswith('.html')]
    print(f"📂 {len(html_files)}개 HTML 파일 스캔 중...")
    
    for filename in html_files:
        file_path = os.path.join(pages_dir, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            event_id = extract_event_id_from_html(content)
            if event_id:
                url_mapping[event_id] = filename
                print(f"✅ {event_id} → {filename}")
            else:
                print(f"⚠️  {filename}에서 event_id를 찾을 수 없습니다.")
                
        except Exception as e:
            print(f"❌ {filename} 처리 중 오류: {e}")
    
    # JSON 파일로 저장
    mapping_file = "url-mapping.json"
    with open(mapping_file, 'w', encoding='utf-8') as f:
        json.dump(url_mapping, f, ensure_ascii=False, indent=2)
    
    print(f"\n🎉 URL 매핑 생성 완료!")
    print(f"📋 총 {len(url_mapping)}개 매핑 → {mapping_file}")
    
    return url_mapping

if __name__ == "__main__":
    generate_url_mapping()