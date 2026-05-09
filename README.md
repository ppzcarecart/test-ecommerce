# test-ecommerce — LiveBoutique

A Django 5 luxury e-commerce storefront with full Stripe checkout, customer
accounts (email + Google OAuth), full-text search, db-backed carts that merge
on login, an admin theme that matches the brand, structured logs, sentry, and
a PWA front-end with background-sync queued cart adds.

## Features

- **Catalog** — categories, products, variants (size/colour/SKU/inventory),
  multiple product images per PDP, related products on the PDP, soft-delete.
- **Search + filters** — top-bar search (Postgres `SearchVector`, sqlite
  `icontains` fallback), price range filter, sort by price/newest/featured.
- **Cart** — session-backed for guests, persisted to the DB for users; the
  guest cart is merged on login automatically.
- **Checkout** — Stripe PaymentIntent (auto-stubs without real keys), webhook
  with signature verification + idempotency log, flat-rate shipping table per
  country with free-shipping thresholds, destination-based tax estimate (or
  Stripe Tax with `STRIPE_TAX_ENABLED=True`).
- **Order email** — HTML + text receipt sent from the webhook (not the success
  page), idempotent so retries don't double-send.
- **Inventory** — variant stock decrements on `payment_intent.succeeded`;
  PDP shows "Sold out" / "Only N left" pills.
- **Accounts** — django-allauth (email + Google), persistent past-orders list,
  saved addresses, wishlist, login-merging cart middleware.
- **Admin** — django-unfold theme, Stock badge column, soft-delete actions,
  CSV product import, CSV orders export.
- **Analytics** — optional PostHog snippet emits `add_to_cart`,
  `begin_checkout`, `purchase` events.
- **SEO** — per-page `<title>` / meta description / canonical / OpenGraph /
  Twitter card; sitemap.xml, robots.txt; `schema.org/Product` JSON-LD on PDPs.
- **Performance** — `cache_page` on the home + shop, `WhiteNoise` with
  `CompressedManifestStaticFilesStorage` (1y immutable in prod), explicit
  width/height + `loading="lazy"` on product imagery.
- **Security** — `django-csp` with a strict policy, HSTS + secure cookies in
  prod, env-only secrets via `django-environ` (refuses to start in prod with
  the dev fallback secret).
- **Observability** — JSON logs to stdout, Sentry SDK auto-initialised when
  `SENTRY_DSN` is set.
- **PWA** — manifest, service worker that pre-caches the offline page + the
  first 12 product images, real 180×180 apple-touch-icon, IndexedDB-backed
  background sync queue for cart adds while offline.
- **Tests** — `pytest-django` covers cart add/update/remove, checkout creates
  an order with shipping + tax, the Stripe webhook flips status to paid (and
  is idempotent on replay), every seeded product PDP renders 200.
- **CI** — GitHub Actions: ruff lint, pytest, Docker build.

## Stack

- Django 5.2, Python 3.12+
- PostgreSQL (SQLite fallback via `USE_SQLITE=True`)
- django-allauth, django-unfold, django-csp, django-environ
- Stripe Python SDK (used live when keys are real, stubbed otherwise)
- WhiteNoise for static asset serving
- Vanilla-JS service worker (no build step)

## Run locally (SQLite, fastest path)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # USE_SQLITE=True keeps it zero-deps

python manage.py migrate
python manage.py loaddata seed/products.json
python manage.py createsuperuser_seed   # admin / ChangeMe123!
python manage.py runserver
```

Visit:

- Storefront — http://localhost:8000/
- Boutique — http://localhost:8000/shop/
- Search — http://localhost:8000/shop/search/?q=tote
- Sign in — http://localhost:8000/accounts/login/
- Account dashboard — http://localhost:8000/account/
- Admin — http://localhost:8000/admin/  (`admin` / `ChangeMe123!`)

## Run tests

```bash
pytest -q
```

## Run with Docker (Postgres)

```bash
docker compose up --build
docker compose exec web python manage.py loaddata seed/products.json
docker compose exec web python manage.py createsuperuser_seed
```

## Environment variables

The full list is in `.env.example`. Key ones:

| Var | Purpose | Default |
|---|---|---|
| `DJANGO_SECRET_KEY` | Django signing key | dev placeholder (refused in prod) |
| `DJANGO_DEBUG` | Debug mode | `True` |
| `DJANGO_ALLOWED_HOSTS` | CSV of allowed hosts | `localhost,127.0.0.1` |
| `SITE_BASE_URL` | Used for canonical / og / sitemap URLs | `http://localhost:8000` |
| `USE_SQLITE` | Use SQLite instead of `DATABASE_URL` | `True` |
| `DATABASE_URL` | Postgres URL | `postgres://shop:shop@localhost:5432/shop` |
| `STRIPE_PUBLIC_KEY` / `STRIPE_SECRET_KEY` / `STRIPE_WEBHOOK_SECRET` | Stripe | stub keys (auto-faked) |
| `STRIPE_TAX_ENABLED` | Skip our flat tax estimate, let Stripe Tax do it | `False` |
| `EMAIL_BACKEND` | Console in dev, SMTP in prod | console |
| `GOOGLE_OAUTH_CLIENT_ID` / `_SECRET` | Optional Google sign-in | empty |
| `SENTRY_DSN` | Production error reporting | empty |
| `POSTHOG_API_KEY` / `POSTHOG_HOST` | Optional analytics | empty |

When `STRIPE_SECRET_KEY` ends with `_stub` or `_replace_me`, checkout never
contacts Stripe — it mints a fake PaymentIntent so the UI keeps working
end-to-end without network access. Drop in a real test key to exercise live
payments and webhooks.

## Production hardening

- `DEBUG=False` flips on `SECURE_SSL_REDIRECT`, HSTS (1 year), secure session
  + CSRF cookies, and refuses to start if the dev secret key is still in use.
- `django-csp` ships a strict default policy — extend `CONTENT_SECURITY_POLICY`
  in `shop/settings.py` if you add new hosts.
- Static files are fingerprinted via `CompressedManifestStaticFilesStorage`
  with a 1-year `Cache-Control` header.

## Stripe webhook

Point Stripe at `POST /checkout/webhook/`. Signature is verified against
`STRIPE_WEBHOOK_SECRET`. Each event id is recorded in `payments_stripeevent`
so retries are idempotent. The handler updates order status, decrements
variant inventory **once**, and triggers the confirmation email.

## License

MIT — see `LICENSE` (add as needed).
