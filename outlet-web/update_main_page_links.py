#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import os

def update_main_page_links():
    """메인 페이지의 링크들을 새로운 URL 구조로 업데이트합니다."""
    
    index_file = "index.html"
    
    if not os.path.exists(index_file):
        print(f"❌ {index_file} 파일을 찾을 수 없습니다.")
        return
    
    # 파일 읽기
    with open(index_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 기존 링크 패턴 찾기
    old_pattern = r'href="pages/event-([^"]+)\.html"'
    
    # 변환된 파일들의 매핑 생성
    conversion_map = {}
    
    # 변환된 파일들에서 매핑 정보 추출
    for filename in os.listdir('.'):
        if filename.endswith('.html') and '-' in filename and not filename.startswith('index'):
            # 파일명에서 확장자 제거
            name_without_ext = filename.replace('.html', '')
            
            # 하이픈을 슬래시로 변환하여 URL 경로 생성
            if name_without_ext.startswith('songdo-'):
                url_path = name_without_ext.replace('songdo-', 'songdo/')
            elif name_without_ext.startswith('gimpo-'):
                url_path = name_without_ext.replace('gimpo-', 'gimpo/')
            elif name_without_ext.startswith('spaceone-'):
                url_path = name_without_ext.replace('spaceone-', 'spaceone/')
            else:
                continue
            
            # 원본 파일명 추출 (파일 내용에서 제목 확인)
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                    # 제목 추출
                    title_match = re.search(r'<h1[^>]*>([^<]+)</h1>', file_content)
                    if title_match:
                        title = title_match.group(1).strip()
                        # 제목을 기반으로 원본 파일명 추측
                        # 이 부분은 실제 데이터와 매칭이 필요할 수 있음
                        conversion_map[filename] = url_path
            except:
                continue
    
    print(f"📊 변환된 파일 수: {len(conversion_map)}")
    
    # 링크 업데이트
    def replace_link(match):
        old_filename = match.group(1)
        old_path = f"pages/event-{old_filename}.html"
        
        # 새로운 URL 경로 찾기
        for new_filename, new_url_path in conversion_map.items():
            # 파일 내용에서 제목이 일치하는지 확인
            try:
                with open(new_filename, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                    # 제목 추출
                    title_match = re.search(r'<h1[^>]*>([^<]+)</h1>', file_content)
                    if title_match:
                        title = title_match.group(1).strip()
                        # 원본 파일에서도 제목 확인
                        old_file_path = f"pages/event-{old_filename}.html"
                        if os.path.exists(old_file_path):
                            with open(old_file_path, 'r', encoding='utf-8') as f2:
                                old_content = f2.read()
                                old_title_match = re.search(r'<h1[^>]*>([^<]+)</h1>', old_content)
                                if old_title_match and old_title_match.group(1).strip() == title:
                                    return f'href="{new_url_path}"'
            except:
                continue
        
        # 매칭되지 않으면 원본 유지
        return match.group(0)
    
    # 링크 업데이트 실행
    updated_content = re.sub(old_pattern, replace_link, content)
    
    # 업데이트된 내용 저장
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print(f"✅ {index_file} 파일의 링크가 업데이트되었습니다.")
    
    # 샘플 변환 결과 출력
    print("\n🔗 샘플 링크 변환:")
    sample_count = 0
    for new_filename, new_url_path in list(conversion_map.items())[:5]:
        print(f"  → {new_url_path}")
        sample_count += 1
        if sample_count >= 5:
            break

if __name__ == "__main__":
    update_main_page_links() 