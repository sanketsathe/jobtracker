# PWA Foundation

## Manifest
- File: `tracker/static/tracker/manifest.webmanifest`
- Linked in `base_app.html` and `base_auth.html`.
- Icons:
  - `tracker/static/tracker/icons/icon-192.png`
  - `tracker/static/tracker/icons/icon-512.png`

## Installability
- `start_url` points to `/applications/`.
- `display` is `standalone`.
- No service worker in this milestone.

## Future work
- Add a service worker for offline caching.
- Add a richer icon set (maskable, monochrome).
