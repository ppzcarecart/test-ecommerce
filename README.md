# test-ecommerce — LiveBoutique

A Django 5 luxury e-commerce storefront with a session-based cart, Stripe
payment-intent checkout, a seeded admin user + sample products, and an
installable mobile-first PWA front-end.

## Features

- **Catalog** — Categories, products, and variants (size/colour/SKU/inventory).
- **Cart** — Session-backed guest cart with add / update / remove.
- **Checkout** — Order capture form, Stripe PaymentIntent (auto-stubs in dev).
- **Admin** — Django admin pre-wired for catalog + orders, seeded superuser.
- **PWA** — Web manifest, service worker, offline page, install prompt hook.
- **Luxury UI** — Dark editorial palette, serif display type, mobile-first.

## Stack

- Django 5, Python 3.12
- PostgreSQL (SQLite fallback for local dev via `USE_SQLITE=1`)
- Stripe Python SDK (used live when keys are real, stubbed otherwise)
- WhiteNoise for static asset serving
- Vanilla JS service worker (no build step)

## Run locally (SQLite, fastest path)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # adjust as needed; USE_SQLITE=1 keeps it zero-deps

python manage.py migrate
python manage.py seed_demo
python manage.py createsuperuser_seed   # creates admin / ChangeMe123!
python manage.py runserver
```

Visit:

- Storefront — http://localhost:8000/
- Boutique — http://localhost:8000/shop/
- Cart — http://localhost:8000/cart/
- Admin — http://localhost:8000/admin/  (`admin` / `ChangeMe123!`)

## Run with Docker (Postgres)

```bash
docker compose up --build
```

Then in a second shell:

```bash
docker compose exec web python manage.py seed_demo
docker compose exec web python manage.py createsuperuser_seed
```

## Environment variables

| Var | Purpose | Default |
|---|---|---|
| `DJANGO_SECRET_KEY` | Django signing key | dev placeholder |
| `DJANGO_DEBUG` | Debug mode | `1` |
| `DJANGO_ALLOWED_HOSTS` | CSV of allowed hosts | `localhost,127.0.0.1` |
| `USE_SQLITE` | Use SQLite instead of `DATABASE_URL` | `1` |
| `DATABASE_URL` | Postgres URL | `postgres://shop:shop@localhost:5432/shop` |
| `DJANGO_ADMIN_EMAIL` / `_USERNAME` / `_PASSWORD` | Seeded superuser | `admin@example.com` / `admin` / `ChangeMe123!` |
| `STRIPE_PUBLIC_KEY` / `STRIPE_SECRET_KEY` | Stripe API keys | `pk_test_stub` / `sk_test_stub` (auto-stub) |
| `DEFAULT_CURRENCY` | Display currency | `USD` |

When `STRIPE_SECRET_KEY` ends with `stub` or `replace_me`, the checkout never
contacts Stripe — it mints a fake PaymentIntent so the UI keeps working
end-to-end without network access. Replace with your real test/live keys to
exercise live payments.

## PWA

- Manifest: `/manifest.webmanifest`
- Service worker: `/sw.js` (network-first for HTML, cache-first for assets, `/offline/` fallback)
- Install: triggered via the browser's native prompt; `window.LiveBoutique.promptInstall()` is exposed for a custom button.

## License

MIT — see `LICENSE` (add as needed).
