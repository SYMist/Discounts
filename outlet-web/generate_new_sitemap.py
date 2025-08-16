#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from datetime import datetime

def generate_new_sitemap():
    """새로운 URL 구조에 맞는 사이트맵을 생성합니다."""
    
    base_url = "https://discounts.deluxo.co.kr"
    today = datetime.today().strftime('%Y-%m-%d')
    
    # 사이트맵 시작
    sitemap = ['<?xml version="1.0" encoding="UTF-8"?>']
    sitemap.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    
    # 1. 메인 페이지
    sitemap.append("  <url>")
    sitemap.append(f"    <loc>{base_url}/</loc>")
    sitemap.append(f"    <lastmod>{today}</lastmod>")
    sitemap.append("    <changefreq>daily</changefreq>")
    sitemap.append("    <priority>1.0</priority>")
    sitemap.append("  </url>")
    
    # 2. 정적 페이지들
    static_pages = [
        "privacy.html",
        "robots.txt"
    ]
    
    for page in static_pages:
        if os.path.exists(page):
            sitemap.append("  <url>")
            sitemap.append(f"    <loc>{base_url}/{page}</loc>")
            sitemap.append(f"    <lastmod>{today}</lastmod>")
            sitemap.append("    <changefreq>monthly</changefreq>")
            sitemap.append("    <priority>0.6</priority>")
            sitemap.append("  </url>")
    
    # 3. 새로운 SEO 친화적인 이벤트 페이지들
    event_files = []
    for filename in os.listdir('.'):
        if filename.endswith('.html') and '-' in filename and not filename.startswith('index'):
            event_files.append(filename)
    
    # 파일명을 URL 경로로 변환
    for filename in sorted(event_files):
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
        
        # 파일 수정 시간 가져오기
        file_path = filename
        if os.path.exists(file_path):
            file_time = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d')
        else:
            file_time = today
        
        sitemap.append("  <url>")
        sitemap.append(f"    <loc>{base_url}/{url_path}</loc>")
        sitemap.append(f"    <lastmod>{file_time}</lastmod>")
        sitemap.append("    <changefreq>weekly</changefreq>")
        sitemap.append("    <priority>0.8</priority>")
        sitemap.append("  </url>")
    
    sitemap.append('</urlset>')
    
    # 사이트맵 파일 저장
    with open('sitemap_new.xml', 'w', encoding='utf-8') as f:
        f.write('\n'.join(sitemap))
    
    print(f"✅ 새로운 사이트맵이 생성되었습니다: sitemap_new.xml")
    print(f"📊 총 {len(event_files)}개의 이벤트 페이지가 포함되었습니다.")
    
    # 샘플 URL들 출력
    print("\n🔗 샘플 URL 구조:")
    sample_count = 0
    for filename in sorted(event_files)[:5]:
        name_without_ext = filename.replace('.html', '')
        if name_without_ext.startswith('songdo-'):
            url_path = name_without_ext.replace('songdo-', 'songdo/')
        elif name_without_ext.startswith('gimpo-'):
            url_path = name_without_ext.replace('gimpo-', 'gimpo/')
        elif name_without_ext.startswith('spaceone-'):
            url_path = name_without_ext.replace('spaceone-', 'spaceone/')
        else:
            continue
        
        print(f"  {base_url}/{url_path}")
        sample_count += 1
        if sample_count >= 5:
            break

if __name__ == "__main__":
    generate_new_sitemap() 