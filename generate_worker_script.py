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

def generate_worker_script():
    """클라우드플레어 Workers Script를 생성합니다."""
    
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
    
    url_mappings = {}
    
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
                
                # URL 매핑 생성
                old_url = f"/pages/{filename}"
                new_url = f"/{branch_en}/{title_slug}"
                
                url_mappings[old_url] = new_url
                
                print(f"✅ {old_url} → {new_url}")
    
    # Workers Script 생성
    worker_script = f"""// 클라우드플레어 Workers Script
// URL 리다이렉트 처리 - 자동 생성됨

addEventListener('fetch', event => {{
  event.respondWith(handleRequest(event.request))
}})

async function handleRequest(request) {{
  const url = new URL(request.url)
  const pathname = url.pathname
  
  // 기존 이벤트 URL 패턴 확인
  if (pathname.startsWith('/pages/event-') && pathname.endsWith('.html')) {{
    const newUrl = getNewUrl(pathname)
    if (newUrl) {{
      // 301 영구 리다이렉트
      return Response.redirect(newUrl, 301)
    }}
  }}
  
  // 리다이렉트가 아닌 경우 원래 요청 처리
  return fetch(request)
}}

function getNewUrl(oldPath) {{
  // URL 매핑 테이블 - 총 {len(url_mappings)}개 규칙
  const urlMappings = {{
"""
    
    # 매핑 데이터 추가
    for old_url, new_url in url_mappings.items():
        worker_script += f'    "{old_url}": "{new_url}",\n'
    
    worker_script += """  }
  
  return urlMappings[oldPath] || null
}
"""
    
    # 파일에 쓰기
    with open('cloudflare_worker_complete.js', 'w', encoding='utf-8') as f:
        f.write(worker_script)
    
    print(f"\n🎉 클라우드플레어 Workers Script 생성 완료!")
    print(f"📁 파일명: cloudflare_worker_complete.js")
    print(f"📊 총 {len(url_mappings)}개의 URL 매핑 규칙 포함")
    
    return url_mappings

def main():
    print("🔄 클라우드플레어 Workers Script 생성 중...")
    
    # Workers Script 생성
    url_mappings = generate_worker_script()
    
    if url_mappings:
        print("\n✅ 완료!")
        print("이제 cloudflare_worker_complete.js 파일을 클라우드플레어 Workers에 배포하세요.")
        
    else:
        print("❌ Workers Script를 생성할 수 없습니다.")

if __name__ == "__main__":
    main() 