#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Basic SEO sanity checks for apps/web/public:
- sitemap.xml exists and contains site root and privacy.html
- url-mapping.json loads and has entries
- pages directory has at least N files
"""

import os
import json
import xml.etree.ElementTree as ET

BASE = os.path.join(os.path.dirname(__file__), '..', 'public')

def main():
    sitemap = os.path.join(BASE, 'sitemap.xml')
    mapping = os.path.join(BASE, 'url-mapping.json')
    pages = os.path.join(BASE, 'pages')

    # sitemap
    assert os.path.exists(sitemap), 'sitemap.xml missing'
    tree = ET.parse(sitemap)
    locs = [e.text for e in tree.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
    assert any(loc.endswith('/') for loc in locs), 'site root not found in sitemap'
    assert any(loc.endswith('/privacy.html') for loc in locs), 'privacy.html not found in sitemap'

    # mapping
    assert os.path.exists(mapping), 'url-mapping.json missing'
    data = json.load(open(mapping, encoding='utf-8'))
    assert isinstance(data, dict) and len(data) > 0, 'url-mapping.json empty'

    # pages
    count = 0
    for root, _, files in os.walk(pages):
        for f in files:
            if f.endswith('.html'):
                count += 1
    assert count >= 100, f'pages html too few: {count}'

    print('✅ SEO sanity checks passed:')
    print(f'  - sitemap URLs: {len(locs)}')
    print(f'  - url-mapping entries: {len(data)}')
    print(f'  - pages html count: {count}')

if __name__ == '__main__':
    main()

