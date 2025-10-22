#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generate Cloudflare Pages _redirects file from url-mapping.json and
add pretty-URL internal rewrites.

Writes to: apps/web/public/_redirects

Rules included:
- 200 rewrites for /{branch}/{slug} -> /pages/{branch}-{slug}.html
- 301 normalization for /pages/{branch}-{slug}.html -> /{branch}/{slug}
- 301 mapping for /pages/event-<id>.html -> /{branch}/{slug}
"""

import os
import json
from typing import Dict, Tuple

BASE = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.abspath(os.path.join(BASE, '..', 'public'))
MAPPING_PATH = os.path.join(PUBLIC_DIR, 'url-mapping.json')
OUTPUT = os.path.join(PUBLIC_DIR, '_redirects')


def filename_to_pretty(filename: str) -> Tuple[str, str]:
    name = filename[:-5] if filename.endswith('.html') else filename
    if name.startswith('songdo-'):
        return 'songdo', name.replace('songdo-', 'songdo/')
    if name.startswith('gimpo-'):
        return 'gimpo', name.replace('gimpo-', 'gimpo/')
    if name.startswith('spaceone-'):
        return 'spaceone', name.replace('spaceone-', 'spaceone/')
    return '', ''


def main():
    # Load mapping
    mapping: Dict[str, str] = json.load(open(MAPPING_PATH, encoding='utf-8'))

    lines = []

    # 200 rewrites (pretty URL -> physical file)
    lines.append('/songdo/*    /pages/songdo-:splat.html   200')
    lines.append('/gimpo/*     /pages/gimpo-:splat.html    200')
    lines.append('/spaceone/*  /pages/spaceone-:splat.html 200')

    # 301 normalization (physical -> pretty)
    lines.append('/pages/songdo-:splat.html   /songdo/:splat   301')
    lines.append('/pages/gimpo-:splat.html    /gimpo/:splat    301')
    lines.append('/pages/spaceone-:splat.html /spaceone/:splat 301')

    # 301 event mapping (old event ids -> pretty)
    for event_id, filename in sorted(mapping.items(), key=lambda x: x[0]):
        branch, pretty = filename_to_pretty(filename)
        if not branch:
            continue
        old = f'/pages/event-{event_id}.html'
        new = f'/{pretty}'
        lines.append(f'{old}   {new}   301')

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    print(f'✅ Wrote {OUTPUT} with {len(lines)} rules')


if __name__ == '__main__':
    main()

