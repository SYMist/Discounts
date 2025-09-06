#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Regenerate sitemap.xml with pretty URLs (non-www, extensionless) from existing pages.

Usage:
  python3 outlet-web/generate_sitemap_only.py
"""

import os
import sys
from datetime import datetime


def generate_sitemap(pages_dir: str, base_url: str, output_path: str) -> None:
    urls = []
    today = datetime.today().strftime('%Y-%m-%d')
    site_root = base_url.rstrip('/') + '/'
    urls.append((site_root, today))
    urls.append((site_root + 'privacy.html', today))

    for filename in os.listdir(pages_dir):
        if filename.endswith('.html') and '-' in filename and not filename.startswith('index'):
            filepath = os.path.join(pages_dir, filename)
            lastmod = datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d')
            name = filename[:-5]
            if name.startswith('songdo-'):
                url_path = name.replace('songdo-', 'songdo/')
            elif name.startswith('gimpo-'):
                url_path = name.replace('gimpo-', 'gimpo/')
            elif name.startswith('spaceone-'):
                url_path = name.replace('spaceone-', 'spaceone/')
            else:
                continue
            urls.append((f"{site_root}{url_path}", lastmod))

    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, lastmod in urls:
        lines += [
            '  <url>',
            f'    <loc>{loc}</loc>',
            f'    <lastmod>{lastmod}</lastmod>',
            '    <changefreq>weekly</changefreq>',
            '    <priority>0.8</priority>',
            '  </url>'
        ]
    lines.append('</urlset>')

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f'✅ Wrote {output_path} with {len(urls)} URLs')


if __name__ == '__main__':
    BASE = os.path.dirname(os.path.abspath(__file__))
    generate_sitemap(
        pages_dir=os.path.join(BASE, 'pages'),
        base_url='https://discounts.deluxo.co.kr',
        output_path=os.path.join(BASE, 'sitemap.xml'),
    )

