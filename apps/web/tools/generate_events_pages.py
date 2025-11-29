#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generate visible events hub pages for better internal linking and crawlability.

Outputs (under apps/web/public):
  - events/index.html         (all branches grouped)
  - events/songdo.html        (songdo only)
  - events/gimpo.html         (gimpo only)
  - events/spaceone.html      (spaceone only)

The script scans apps/web/public/pages for files named
  {branch}-{slug}.html  where branch in {songdo,gimpo,spaceone}
and reads the <h1> title to use as anchor text.
"""

import os
from bs4 import BeautifulSoup
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # apps/web
PUBLIC = os.path.join(BASE, 'public')
PAGES = os.path.join(PUBLIC, 'pages')
EVENTS_DIR = os.path.join(PUBLIC, 'events')


def load_events():
    items = []
    if not os.path.isdir(PAGES):
        return items
    for fn in sorted(os.listdir(PAGES)):
        if not fn.endswith('.html'):
            continue
        name = fn[:-5]
        if name.startswith('songdo-'):
            branch = 'songdo'
            slug = name.replace('songdo-', '')
        elif name.startswith('gimpo-'):
            branch = 'gimpo'
            slug = name.replace('gimpo-', '')
        elif name.startswith('spaceone-'):
            branch = 'spaceone'
            slug = name.replace('spaceone-', '')
        else:
            continue
        path = os.path.join(PAGES, fn)
        title = slug
        try:
            with open(path, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f, 'html.parser')
                h1 = soup.find('h1')
                if h1 and h1.get_text(strip=True):
                    title = h1.get_text(strip=True)
        except Exception:
            pass
        mtime = os.path.getmtime(path)
        items.append({
            'branch': branch,
            'slug': slug,
            'title': title,
            'pretty': f"/{branch}/{slug}",
            'mtime': mtime,
        })
    # 최신순 정렬
    items.sort(key=lambda x: (-x['mtime'], x['title']))
    return items


def render_page(title, items, canonical_href):
    head = f"""<!DOCTYPE html>
<html lang=\"ko\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <title>{title}</title>
  <link rel=\"canonical\" href=\"{canonical_href}\" />
  <meta name=\"description\" content=\"현대 프리미엄 아울렛 행사 모음 – 지점별 최신 행사 한곳에서 보기\" />
  <link rel=\"stylesheet\" href=\"/style.css\" />
</head>
<body>
  <div class=\"container\">
    <h1>{title}</h1>
    <p>현대 프리미엄 아울렛(송도·김포·스페이스원)의 최신 행사 링크 모음입니다.</p>
"""
    lis = []
    for it in items:
        lis.append(f"<li><a href=\"{it['pretty']}\">[{it['branch']}] {it['title']}</a></li>")
    body = f"<ul class=\"events-grid\">\n{os.linesep.join(lis)}\n</ul>"
    foot = """
    <p style="margin-top:1rem"><a href="/">메인으로</a></p>
  </div>
</body>
</html>
"""
    return head + body + foot


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def main():
    items = load_events()
    ensure_dir(EVENTS_DIR)

    # 전체 페이지
    with open(os.path.join(EVENTS_DIR, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(render_page('아울렛 행사 전체 보기',
                            items,
                            'https://discounts.deluxo.co.kr/events/'))

    # 지점별 페이지
    for branch in ['songdo', 'gimpo', 'spaceone']:
        subset = [it for it in items if it['branch'] == branch]
        with open(os.path.join(EVENTS_DIR, f'{branch}.html'), 'w', encoding='utf-8') as f:
            f.write(
                render_page(
                    f'[{branch}] 행사 모음',
                    subset,
                    f'https://discounts.deluxo.co.kr/events/{branch}.html',
                )
            )

    print(f"✅ generated events hub: {len(items)} items")


if __name__ == '__main__':
    main()
