# Samwa Bakery - Digital Menu + WhatsApp Ordering

A reusable Django template for "digital menu + WhatsApp order" sites for
small Zimbabwean businesses. No cart/checkout/payment gateway in the
database sense - customers build an order in the browser and it becomes a
single pre-filled WhatsApp message. Built to be cloned per business by
editing `.env` and one `BakeryInfo` row in `/admin/`.

## Features

- Mobile-first menu with HTMX category filtering + search (no full reloads)
- Product detail pages with a 1-tap "Order on WhatsApp" button
- **v2.1** Quantity picker per product before adding to cart
- **v2.2** "Currently closed" banner computed from `opening_hours`
- **v2.3** Multi-item cart (localStorage) that becomes one WhatsApp message
- **v2.4** PWA - "Add to Home Screen", offline-cached app shell
- Django admin: product photo thumbnails, quick price/availability edit,
  singleton `BakeryInfo` for all branding (name, WhatsApp number, address,
  hours, logo, brand color)
- Split settings (`base.py` / `dev.py` / `prod.py`), all secrets via
  `python-decouple` and `.env` - nothing sensitive hardcoded or committed
- WhiteNoise for compressed static files; root `urls.py` also serves
  `/media/` in production - required on cPanel subdomains (see below)

## Project layout

```
samwa/
├── manage.py
├── passenger_wsgi.py        # cPanel Passenger entry point
├── requirements.txt
├── .env.example
├── samwa/
│   ├── settings/
│   │   ├── base.py           # shared settings
│   │   ├── dev.py            # local development
│   │   └── prod.py           # cPanel production, whitelist-only
│   ├── urls.py                # root urlconf + media serving fix
│   └── wsgi.py
├── core/                      # BakeryInfo, base.html, static assets
├── products/                   # Category, Product, menu + detail views
└── pages/                      # homepage
```

## Local development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # edit SECRET_KEY at minimum
python manage.py migrate
python manage.py createsuperuser
python manage.py loaddata demo_products.json   # optional demo data
python manage.py runserver
```

Visit `http://127.0.0.1:8000/admin/` and fill in the `BakeryInfo` row
(WhatsApp number, address, opening hours, brand color) - or run
`python manage.py seed_bakery_info` to create a starting row from the
`BUSINESS_NAME` / `WHATSAPP_NUMBER` / etc values already in `.env`.

## Why static/media need special handling on a cPanel subdomain

On a normal shared-hosting root domain, Apache's `public_html` serves
`/static/` and `/media/` directly - Django never sees those requests. A
cPanel **subdomain** set up via "Setup Python App" doesn't work that way:
**every** request to that subdomain, including static and media files, is
routed through Passenger into this Django process. If you deploy code
written for a root-domain setup, uploaded product photos (and sometimes
CSS/JS) 404 in production even though the files exist on disk - because
nothing is configured to serve them from inside the Python app.

This project handles both halves of that:

- **STATIC_URL** (`/static/...`) is served by WhiteNoise, wired into
  `MIDDLEWARE` in `settings/base.py`. WhiteNoise runs as part of the
  Django app itself, so it works identically whether Apache fronts a
  subdomain or a root domain.
- **MEDIA_URL** (`/media/...`, i.e. uploaded product photos) has no
  built-in Django equivalent to WhiteNoise. `samwa/urls.py` adds an
  explicit `static()` route for `MEDIA_ROOT` **unconditionally** (not
  gated behind `if DEBUG`), because on a cPanel subdomain there genuinely
  is no other server available to serve it in "production" either. See
  the comment in `samwa/urls.py` for the full explanation.

If you ever move to a root-domain deployment where Apache's `public_html`
really does serve `/media/`, you can safely remove that line from
`urls.py` and point `MEDIA_ROOT` at `public_html/media` instead.

## Deploying to cPanel (subdomain, shared hosting)

1. **Push code to GitHub** (or upload as a zip via cPanel File Manager).
2. **cPanel → Setup Python App**
   - Python version: 3.10+ if available
   - Application root: e.g. `samwa` (outside `public_html`)
   - Application URL: your subdomain, e.g. `shop.yourdomain.co.zw`
   - Application startup file: `passenger_wsgi.py`
   - Application Entry point: `application`
   - Environment variable: `DJANGO_SETTINGS_MODULE=samwa.settings.prod`
3. **Create `.env`** in the application root (never commit this):
   ```
   SECRET_KEY=<random 50+ char string>
   DEBUG=False
   ALLOWED_HOSTS=shop.yourdomain.co.zw,www.shop.yourdomain.co.zw
   CSRF_TRUSTED_ORIGINS=https://shop.yourdomain.co.zw
   SECURE_SSL_REDIRECT=False   # keep False until SSL is confirmed working, then True
   BUSINESS_NAME=Samwa Bakery
   BUSINESS_LOCATION=Mvurwi, Mashonaland Central
   WHATSAPP_NUMBER=+263771234567
   BRAND_COLOR=#d97706
   ```
4. **Install + initialise**, via cPanel's "Run Pip Install" or its terminal:
   ```bash
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py collectstatic --noinput
   python manage.py createsuperuser
   python manage.py seed_bakery_info   # optional quick-start
   ```
5. Once cPanel's AutoSSL / "Force HTTPS Redirect" is confirmed working for
   the subdomain, set `SECURE_SSL_REDIRECT=True` in `.env` and restart the
   Python app.
6. Log into `/admin/`, fill in `BakeryInfo` fully, add categories/products
   with photos (keep photos under ~200KB, ~800px wide - this targets
   2G/3G networks).

### Common cPanel error: `DisallowedHost` / 400 Bad Request

Means the exact hostname you're visiting isn't in `.env`'s
`ALLOWED_HOSTS`. Copy the hostname straight from the browser's address
bar into `.env` (comma-separated, no spaces, no scheme) and restart the
app. `prod.py` deliberately does **not** use `ALLOWED_HOSTS = ['*']` or a
redirect-everything middleware - if a request's Host header isn't
recognised, returning 400 is the correct, secure behaviour.

## Launching "Business #2"

1. Clone this repo.
2. `cp .env.example .env` and fill in the new business's values.
3. `python manage.py migrate`
4. Log into `/admin/`, add `BakeryInfo` + categories + products.
5. Deploy following the cPanel steps above with the new subdomain.

No template or Python code should need editing - every business-specific
value lives in `.env` and the `BakeryInfo` row.
