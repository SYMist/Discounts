#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Enhance existing detail pages with:
- Breadcrumb UI
- BreadcrumbList JSON-LD
- Related events (same branch) links (3-5 items)

This is a template-upgrade post-processor so we don't need to re-crawl.
"""

import os
import re
from html import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # apps/web
PUBLIC = os.path.join(ROOT, 'public')
PAGES = os.path.join(PUBLIC, 'pages')

SITE_BASE = 'https://discounts.deluxo.co.kr'
BRANCH_KO = {
    'songdo': '송도',
    'gimpo': '김포',
    'spaceone': '스페이스원',
}


def parse_title(html: str, fallback: str) -> str:
    m = re.search(r'<h1[^>]*>(.*?)</h1>', html, flags=re.S)
    if m:
        # drop tags inside h1
        inner = re.sub(r'<[^>]+>', '', m.group(1))
        return inner.strip() or fallback
    return fallback


def build_breadcrumb_jsonld(branch_en: str, branch_ko: str, slug: str, title: str) -> str:
    title_json = escape(title, quote=False)
    pretty = f"{SITE_BASE}/{branch_en}/{slug}"
    return (
        '<script type="application/ld+json">\n'
        '{\n'
        '  "@context": "https://schema.org",\n'
        '  "@type": "BreadcrumbList",\n'
        '  "itemListElement": [\n'
        '    {"@type":"ListItem","position":1,"name":"홈","item":"' + SITE_BASE + '/"},\n'
        '    {"@type":"ListItem","position":2,"name":"전체 보기","item":"' + SITE_BASE + '/events/"},\n'
        '    {"@type":"ListItem","position":3,"name":"' + branch_ko + '","item":"' + SITE_BASE + '/events/' + branch_en + '.html"},\n'
        '    {"@type":"ListItem","position":4,"name":"' + title_json + '","item":"' + pretty + '"}\n'
        '  ]\n'
        '}\n'
        '</script>\n'
    )


def build_breadcrumb_ui(branch_en: str, branch_ko: str, slug: str, title: str) -> str:
    return (
        '    <nav aria-label="Breadcrumb" style="margin:0 0 1rem 0; font-size:0.95rem; color:#555;">\n'
        '      <a href="/" style="color:#555; text-decoration:none;">홈</a>\n'
        '      <span style="margin:0 6px;">›</span>\n'
        '      <a href="/events/" style="color:#555; text-decoration:none;">전체 보기</a>\n'
        '      <span style="margin:0 6px;">›</span>\n'
        f'      <a href="/events/{branch_en}.html" style="color:#555; text-decoration:none;">{branch_ko}</a>\n'
        '      <span style="margin:0 6px;">›</span>\n'
        f'      <span aria-current="page" style="color:#333;">{escape(title, quote=False)}</span>\n'
        '    </nav>\n'
    )


def collect_related(branch_en: str, current_file: str) -> list:
    candidates = []
    prefix = branch_en + '-'
    for fn in os.listdir(PAGES):
        if not fn.endswith('.html'):
            continue
        if not fn.startswith(prefix):
            continue
        if fn == current_file:
            continue
        path = os.path.join(PAGES, fn)
        try:
            mtime = os.path.getmtime(path)
        except Exception:
            mtime = 0
        # title extraction
        try:
            with open(path, 'r', encoding='utf-8') as rf:
                html = rf.read()
            title = parse_title(html, fn[:-5])
        except Exception:
            title = fn[:-5]
        slug = fn[len(prefix):-5]
        candidates.append((mtime, slug, title))
    candidates.sort(key=lambda x: -x[0])
    return candidates[:5]


def inject_if_missing(html: str, marker: str, insertion: str, where: str = 'before_head_end') -> str:
    if marker in html:
        return html
    if where == 'before_head_end':
        pos = html.lower().find('</head>')
        if pos != -1:
            return html[:pos] + insertion + html[pos:]
    return html


def main():
    updated = 0
    for fn in os.listdir(PAGES):
        if not fn.endswith('.html'):
            continue
        base = fn[:-5]
        if '-' not in base:
            continue
        branch_en = base.split('-', 1)[0]
        if branch_en not in BRANCH_KO:
            continue
        slug = base[len(branch_en)+1:]
        branch_ko = BRANCH_KO[branch_en]
        path = os.path.join(PAGES, fn)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Title
        title = parse_title(content, slug)

        # Breadcrumb JSON-LD
        bjson = build_breadcrumb_jsonld(branch_en, branch_ko, slug, title)
        content2 = inject_if_missing(content, 'BreadcrumbList', bjson, 'before_head_end')

        # Breadcrumb UI: replace 기존 "목록으로 돌아가기" 블록 또는 <h1> 앞에 삽입
        ui = build_breadcrumb_ui(branch_en, branch_ko, slug, title)
        if 'aria-label="Breadcrumb"' not in content2:
            pattern = re.compile(r'<p[^>]*>\s*<!--\s*목록으로 돌아가기 링크\s*-->.*?</p>', re.S)
            if pattern.search(content2):
                content2 = pattern.sub(ui, content2, count=1)
            else:
                # insert before first <h1>
                content2 = re.sub(r'(<h1[^>]*>)', ui + r'\n\1', content2, count=1)

        # Related events block
        if '관련 행사' not in content2:
            related_items = collect_related(branch_en, fn)
            if related_items:
                lis = '\n'.join(
                    f'<li><a href="/{branch_en}/{slug}">{escape(title, quote=False)}</a></li>'
                    for _, slug, title in related_items
                )
                related_html = (
                    '\n    <section style="margin-top:2rem;">\n'
                    f'      <h2>관련 행사 ({branch_ko})</h2>\n'
                    '      <ul style="list-style:disc; margin-left:1.25rem;">\n'
                    f'        {lis}\n'
                    '      </ul>\n'
                    '    </section>\n'
                )
                marker = '<!-- 이벤트 공식 페이지 이동 배너 -->'
                idx = content2.find(marker)
                if idx != -1:
                    content2 = content2[:idx] + related_html + content2[idx:]
                else:
                    # fallback: append before footer
                    content2 = content2.replace('</footer>', related_html + '\n    </footer>')

        if content2 != content:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content2)
            updated += 1

    print(f"Enhanced {updated} page(s)")


if __name__ == '__main__':
    main()

