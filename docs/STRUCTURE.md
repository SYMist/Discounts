# Project Structure

Reorganized into `apps/` with clear separation of crawler and web.

## Layout

```
apps/
  crawler/
    crawler_organized.py
    templates/
      template.html
      index.tpl.html
    requirements.txt
    README.md
    url_generator.py
    (credentials.json – not committed; see README)

  web/
    public/              # Web root to deploy
      (index.html, style.css, script.js, robots.txt, ads.txt, sitemap.xml, url-mapping.json)
      pages/             # Generated detailed pages
      images/
      .htaccess

    tools/
      build_redirects.py
      README.md

tools/
  sync_legacy_to_apps.py  # One-off helper to copy outlet-web/* into apps/web/public

legacy/
  outlet-web/ (kept in repo as `outlet-web/` folder; content unchanged)
```

## Notes
- Default outputs now target `apps/web/public`. Override via environment variables if needed (see `apps/crawler/README.md`).
- For existing content under `outlet-web/`, run `python3 tools/sync_legacy_to_apps.py` to copy into `apps/web/public` once.
- Server document root should point to `apps/web/public`.

