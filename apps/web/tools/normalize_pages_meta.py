#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Normalize existing detail pages:
- Collapse newlines/extra spaces in <title>, <h1>, alt text
- Fill meta/OG/Twitter descriptions if empty (use 혜택 설명 → 기간/지점 fallback)
- Normalize JSON-LD 'name' and 'description'
- Normalize BreadcrumbList last item's name
"""

import os
import re
import json
from bs4 import BeautifulSoup

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # apps/web
PUBLIC = os.path.join(ROOT, 'public')
PAGES = os.path.join(PUBLIC, 'pages')

BRANCH_KO = {
    'songdo': '송도',
    'gimpo': '김포',
    'spaceone': '스페이스원',
}


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or '').replace('\r', ' ')).strip()


def main():
    changed = 0
    for fn in os.listdir(PAGES):
        if not fn.endswith('.html'):
            continue
        base = fn[:-5]
        if '-' not in base:
            continue
        branch_en = base.split('-', 1)[0]
        if branch_en not in BRANCH_KO:
            continue
        branch_ko = BRANCH_KO[branch_en]
        path = os.path.join(PAGES, fn)
        with open(path, 'r', encoding='utf-8') as f:
            html = f.read()
        soup = BeautifulSoup(html, 'html.parser')

        # Title / H1
        title_text = ''
        if soup.title and soup.title.string:
            title_text = norm(soup.title.string)
            soup.title.string.replace_with(title_text)
        h1 = soup.find('h1')
        if h1:
            h1_text = norm(h1.get_text(' ', strip=True))
            title_text = title_text or h1_text
            h1.clear(); h1.append(h1_text)

        # Period / Desc
        period_el = soup.select_one('div.period')
        period = norm(period_el.get_text(' ', strip=True)) if period_el else ''
        desc_p = soup.select_one('div.description p')
        desc = norm(desc_p.get_text(' ', strip=True)) if desc_p else ''

        # Meta desc (fallbacks)
        if desc:
            meta_desc = f"{title_text} | {desc}"
        else:
            fallback = period if period else f"현대 프리미엄 아울렛 {branch_ko} 행사"
            meta_desc = f"{title_text} | {fallback}"

        # <meta> description
        mdesc = soup.find('meta', attrs={'name': 'description'})
        if not mdesc:
            mdesc = soup.new_tag('meta'); mdesc['name'] = 'description'; soup.head.append(mdesc)
        mdesc['content'] = meta_desc

        # OG/Twitter description
        ogd = soup.find('meta', attrs={'property': 'og:description'})
        if not ogd:
            ogd = soup.new_tag('meta'); ogd['property'] = 'og:description'; soup.head.append(ogd)
        ogd['content'] = desc or meta_desc

        twd = soup.find('meta', attrs={'name': 'twitter:description'})
        if not twd:
            twd = soup.new_tag('meta'); twd['name'] = 'twitter:description'; soup.head.append(twd)
        twd['content'] = desc or meta_desc

        # Alt texts normalization
        for img in soup.find_all('img'):
            if img.has_attr('alt'):
                img['alt'] = norm(img['alt'])

        # JSON-LD blocks
        for s in soup.find_all('script', attrs={'type': 'application/ld+json'}):
            try:
                data = json.loads(s.string)
            except Exception:
                continue
            updated = False
            objs = data.get('@graph') if isinstance(data, dict) and '@graph' in data else [data]
            for o in objs:
                if not isinstance(o, dict):
                    continue
                if o.get('@type') == 'Event':
                    if 'name' in o:
                        o['name'] = norm(o['name'])
                        updated = True
                    if not norm(o.get('description', '')):
                        o['description'] = desc or meta_desc
                        updated = True
                if o.get('@type') == 'BreadcrumbList':
                    try:
                        items = o.get('itemListElement') or []
                        if items:
                            last = items[-1]
                            if isinstance(last, dict) and 'name' in last:
                                last['name'] = norm(last['name'])
                                updated = True
                    except Exception:
                        pass
            if updated:
                s.string.replace_with(json.dumps(data, ensure_ascii=False))

        new_html = str(soup)
        if new_html != html:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_html)
            changed += 1

    print(f"Normalized {changed} page(s)")


if __name__ == '__main__':
    main()

