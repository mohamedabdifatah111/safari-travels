# Safari Travels: Backend

Django REST Framework API for the Safari Travels website. It serves destinations and travel packages, and accepts booking requests. Staff manage everything in Django Admin.

- **Source of truth for the API:** [`docs/api-contract.md`](../docs/api-contract.md)
- **Database:** PostgreSQL only. There is no SQLite configuration anywhere, including tests.
- **Stack:** Python 3.13, Django 5.2, Django REST Framework, django-filter, django-cors-headers, django-environ, psycopg 3, Pillow

## Quick start (Windows, Command Prompt)

All commands run from the `backend` folder unless stated otherwise.

### 1. Requirements

- Python 3.12 or newer (developed on 3.13)
- PostgreSQL 14 or newer, running locally
- Git

### 2. Create the database

Open **SQL Shell (psql)** and log in as `postgres` (press Enter to accept the defaults, then type the postgres password). Run:

```sql
CREATE USER safari_user WITH PASSWORD 'choose-a-strong-password' CREATEDB;
CREATE DATABASE safari_travels OWNER safari_user;
```

- Avoid single quotes and backslashes in the password.
- `CREATEDB` lets Django create a temporary `test_safari_travels` database when running tests.
- The app uses `safari_user`, never the `postgres` superuser.

### 3. Install

```bat
cd backend
python -m venv venv
venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements\dev.txt
```

Your prompt should start with `(venv)`.

### 4. Configure environment variables

```bat
copy .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Open `backend\.env`, paste the generated key as `SECRET_KEY`, and set `DB_PASSWORD` to the password from step 2. **Never commit `.env`.** It is listed in `.gitignore`.

### 5. Create tables and start

```bat
python manage.py migrate
python manage.py createcachetable
python manage.py createsuperuser
python manage.py runserver
```

- `migrate` creates the database tables.
- `createcachetable` creates the table used by the booking rate limiter. **Run it once per database.** Without it, `POST /api/bookings/` fails.
- `createsuperuser` creates your admin login.

Open:
- API: <http://localhost:8000/api/destinations/>
- Admin: <http://localhost:8000/admin/>

### 6. Optional: sample data

```bat
python manage.py seed_sample_data
```

Creates sample destinations and packages for development. It refuses to run when `DEBUG` is off, and is safe to run repeatedly. The sample "Closed" items are inactive on purpose, to demonstrate that inactive records are hidden.

## Environment variables

Read from the process environment, or from `backend/.env` in development. See `.env.example`.

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `SECRET_KEY` | Yes | none | Django secret key |
| `DB_NAME` | Yes | none | PostgreSQL database name |
| `DB_USER` | Yes | none | PostgreSQL user |
| `DB_PASSWORD` | Yes | none | PostgreSQL password |
| `DB_HOST` | No | `localhost` | Database host |
| `DB_PORT` | No | `5432` | Database port |
| `DB_SSLMODE` | No | `prefer` | PostgreSQL SSL mode |
| `DB_CONN_MAX_AGE` | No | `60` | Connection reuse (seconds) |
| `ALLOWED_HOSTS` | Prod: yes | `localhost,127.0.0.1` (dev) | Comma-separated, no spaces |
| `CORS_ALLOWED_ORIGINS` | Prod: yes | `http://localhost:5173` | Comma-separated frontend origins |
| `TIME_ZONE` | No | `Africa/Nairobi` | Also decides what "today" means for booking dates |
| `LOG_LEVEL` | No | `INFO` | Logging level |
| `BOOKING_THROTTLE_RATE` | No | `5/hour` | Booking limit per client IP (`number/second\|minute\|hour\|day`) |
| `NUM_PROXIES` | No | `0` | Reverse proxies in front of Django. See "Production notes" |
| `CSRF_TRUSTED_ORIGINS` | Prod | empty | HTTPS origins for admin forms |
| `SECURE_SSL_REDIRECT` | Prod | `True` | Redirect HTTP to HTTPS |
| `SECURE_HSTS_SECONDS` | Prod | `3600` | HSTS duration. Raise once HTTPS is confirmed |
| `USE_PROXY_SSL_HEADER` | Prod | `False` | Trust `X-Forwarded-Proto` from your proxy |

Missing required variables stop Django with a clear error. There is no fallback database.

## Settings modules

| Module | Used by | Notes |
|---|---|---|
| `config.settings.dev` | `manage.py` (default) | `DEBUG=True`, browsable API, serves uploaded media |
| `config.settings.prod` | `wsgi.py`, `asgi.py` | `DEBUG=False`, HTTPS and secure cookies, WhiteNoise static files |
| `config.settings.test` | tests | Still PostgreSQL. In-memory cache for throttle counters, temp media folder |

Switching settings in a terminal window with `set DJANGO_SETTINGS_MODULE=...` lasts only for that window. If the API behaves strangely, run
`python manage.py shell -c "from django.conf import settings; print(settings.DEBUG, settings.SETTINGS_MODULE)"`
to see which settings are active.

## Project structure

```
backend/
├── manage.py
├── .env.example
├── requirements/        base.txt, dev.txt, prod.txt
├── config/              settings/, urls.py, views.py (JSON errors), wsgi.py, asgi.py
└── apps/
    ├── destinations/    Destination model, API, admin, tests
    ├── packages/        TravelPackage + ItineraryDay, filters, API, admin, tests, seed command
    ├── bookings/        Booking model, create-only API, throttle, admin, tests
    └── factories.py     helpers used only by tests
```

## API

Base URL: `http://localhost:8000/api/`. JSON only. Endpoints end with a trailing slash. Detail URLs use integer IDs. The full specification is in `docs/api-contract.md`. Behavior below is what the backend implements.

| Method and path | Purpose |
|---|---|
| `GET /api/destinations/` | Active destinations (paginated) |
| `GET /api/destinations/{id}/` | One destination, adds `description` |
| `GET /api/packages/` | Active packages (paginated, filterable) |
| `GET /api/packages/{id}/` | One package with itinerary |
| `POST /api/bookings/` | Submit a booking request |

There are no public endpoints to list or read bookings. `GET /api/bookings/` returns `405`.

### Conventions

- Field names are `snake_case`. Prices are strings with two decimals (`"850.00"`). Dates are `YYYY-MM-DD`. Timestamps are ISO 8601.
- `image` is an absolute URL, or `null` if no image was uploaded.
- Lists are paginated at 12 per page: `{"count", "next", "previous", "results"}`. Use `?page=2`.
- Lists have a fixed order: destinations by name, packages by id.
- A page number past the end returns `404`.

### Destinations

`GET /api/destinations/`

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Maasai Mara",
      "country": "Kenya",
      "slug": "maasai-mara",
      "short_description": "Wildlife and the Great Migration.",
      "image": "http://localhost:8000/media/destinations/mara.jpg",
      "package_count": 2
    }
  ]
}
```

`package_count` counts only active packages. The detail endpoint returns the same fields plus `description`.

### Packages

`GET /api/packages/`. Optional query parameters:

| Parameter | Example | Behavior |
|---|---|---|
| `destination` | `destination=1` | Destination ID (whole number) |
| `featured` | `featured=true` | `true` or `false`. Other values are ignored |
| `min_price` | `min_price=100` | Inclusive |
| `max_price` | `max_price=1000` | Inclusive |
| `page` | `page=2` | Page number |

Invalid numbers (`min_price=abc`) return `400` with the parameter name as the key. Only active packages in active destinations are returned.

```json
{
  "id": 1,
  "title": "3-Day Maasai Mara Safari",
  "slug": "3-day-maasai-mara-safari",
  "destination": { "id": 1, "name": "Maasai Mara" },
  "price": "850.00",
  "currency": "USD",
  "duration_days": 3,
  "image": null,
  "short_description": "A short summary.",
  "is_featured": true
}
```

`GET /api/packages/{id}/` adds:

```json
{
  "description": "Full description.",
  "includes": ["Park fees", "Accommodation"],
  "excludes": ["International flights"],
  "itinerary": [
    { "day": 1, "title": "Arrival", "description": "Welcome." }
  ],
  "max_group_size": 8
}
```

`includes` and `excludes` are arrays of strings. Staff enter them one per line in the admin. `itinerary` is ordered by day.

### Bookings

`POST /api/bookings/` with `Content-Type: application/json`:

```json
{
  "package": 1,
  "full_name": "Amina Hassan",
  "email": "amina@example.com",
  "phone": "+254700000000",
  "travel_date": "2026-12-10",
  "number_of_travelers": 2,
  "message": "We would like a vegetarian meal option."
}
```

**Success: `201 Created`**

```json
{
  "id": 1,
  "package": 1,
  "full_name": "Amina Hassan",
  "email": "amina@example.com",
  "phone": "+254700000000",
  "travel_date": "2026-12-10",
  "number_of_travelers": 2,
  "message": "We would like a vegetarian meal option.",
  "status": "pending",
  "total_price": "1700.00",
  "created_at": "2026-11-03T09:10:01.492334+03:00"
}
```

**Validation rules** (all enforced on the server):

| Field | Rule |
|---|---|
| `package` | Required. Must be an active package in an active destination |
| `full_name` | Required, max 120 characters |
| `email` | Required, valid email |
| `phone` | Required, max 20 characters |
| `travel_date` | Required, `YYYY-MM-DD`, strictly after today (in `TIME_ZONE`) |
| `number_of_travelers` | Required, at least 1, at most the package's `max_group_size` |
| `message` | Optional, max 1000 characters |

**The server decides money and status.** `total_price` is the package price at submission time multiplied by `number_of_travelers` (prices are per person). The price and currency are copied onto the booking, so later price changes never alter old bookings. `status`, `total_price`, `id`, and `created_at` in a request body are ignored. A new booking is always `pending`. A booking request is **not** a confirmed booking or a payment.

**Errors:** `400` returns field-keyed arrays, with `non_field_errors` for errors that don't belong to a field:

```json
{ "email": ["Enter a valid email address."] }
```

### Status codes

| Code | Meaning |
|---|---|
| `200` | Successful GET |
| `201` | Booking request created |
| `400` | Invalid request (validation or filter error) |
| `404` | Not found (unknown ID, inactive item, page out of range) |
| `405` | Method not allowed (for example `GET /api/bookings/`) |
| `429` | Too many booking requests. Check the `Retry-After` header |
| `500` | Unexpected server error |

`/api/...` errors are always JSON, for example `{"detail": "Not found."}`.

### Example requests (Command Prompt)

```bat
curl http://localhost:8000/api/packages/?featured=true&min_price=500
curl -i -X POST http://localhost:8000/api/bookings/ -H "Content-Type: application/json" -d "{\"package\": 1, \"full_name\": \"Amina Hassan\", \"email\": \"amina@example.com\", \"phone\": \"+254700000000\", \"travel_date\": \"2026-12-10\", \"number_of_travelers\": 2}"
```

In Command Prompt, put the URL in quotes if it contains `&`.

## Booking protection

- **Server-side validation:** every rule in the table above. The frontend's checks are conveniences only.
- **Rate limiting:** `POST /api/bookings/` is limited per client IP (default `5/hour`, setting `BOOKING_THROTTLE_RATE`). Every POST counts, including invalid ones. GET requests are not counted. Counters live in a PostgreSQL cache table (`createcachetable`).
- **Group size:** the limit is the package's `max_group_size`. There is no per-date capacity tracking, because the contract does not define one.
- **No duplicate-booking rules** are applied. The contract does not define any.
- **Privacy:** bookings cannot be read through the public API.

To reset your own rate-limit counter during development:

```bat
python manage.py shell -c "from django.core.cache import cache; cache.clear()"
```

## Django Admin (for staff)

Open <http://localhost:8000/admin/> and log in.

**Destinations:** add and edit places. The slug fills in from the name. Upload an image on the destination's own page. The list shows thumbnails and an **Active** tick box. Untick **Active** to hide a destination without deleting it.

**Travel packages:** pricing, group size, descriptions, images, and the itinerary are all on one page. Add itinerary days in the rows at the bottom (one row per day number). Type **Includes** and **Excludes** one item per line. Prices are per person. Changing a price does not change existing bookings.

**Bookings:** search by name, email, or phone. Filter by status, travel date, or package. Open a booking to see the customer and trip details. **Only the status can be changed.** The price fields are read-only. Use the actions menu on the list page to confirm or cancel several bookings at once. You cannot add bookings in the admin (they come from the website). Only superusers can delete bookings.

**Staff accounts:** create users under **Users**, tick **Staff status**, and grant only the permissions they need (for example "Can view booking" and "Can change booking"). A staff user with no permissions sees nothing, which is the secure default.

**Deleting:** destinations with packages, and packages with bookings, cannot be deleted, so history is never lost. Untick **Active** instead.

## Images

Images are uploaded in the admin and stored under `backend/media/destinations/` and `backend/media/packages/`. In development (`DEBUG=True`) Django serves them at `/media/...`, and the API returns absolute URLs such as `http://localhost:8000/media/destinations/mara.jpg`. `backend/media/` is git-ignored, so uploaded files are not shared through Git.

Production image storage is **not decided yet**. The Django admin and API are already written against Django's storage setting, so a persistent or cloud backend can be added later without changing the API.

## Tests

```bat
python manage.py check
python manage.py test --settings=config.settings.test --noinput
```

- Tests run against PostgreSQL. Django creates a temporary `test_safari_travels` database and deletes it afterward, so your data is untouched. This needs the `CREATEDB` permission from the setup step.
- Expected: `Ran 112 tests ... OK`.
- Verbose output: add `-v 2`. One app: `python manage.py test apps.bookings --settings=config.settings.test --noinput`.
- Messages like "Bad Request", "Not Found", "Forbidden", and Django `PermissionDenied` tracebacks in the output are normal. Those tests send bad requests on purpose.

The suite covers models and constraints, serializers, every endpoint, pagination, filters, validation rules, price calculation and snapshots, the rate limit, public access restrictions, admin permissions, CORS, JSON errors, and that PostgreSQL is the only database.

## Frontend integration

- Base URL in development: `http://localhost:8000/api/`. CORS allows `http://localhost:5173`. Other origins are blocked. To add one, extend `CORS_ALLOWED_ORIGINS` in `.env`.
- **Do not hard-code IDs.** IDs come from each person's own database. Fetch lists from the API and use the returned IDs. Use `slug` for display or routing if wanted. Detail endpoints take integer IDs only.
- `image` can be `null`. Show a placeholder.
- Display `total_price` and `currency` from the server. Never calculate prices in the frontend for submission. The booking response does not include the currency. Use the package's `currency`.
- Handle `400` by showing the messages under each field key (and `non_field_errors` as a general message). Handle `429` with a friendly "please try again later" message.
- Send `Content-Type: application/json`. No cookies or tokens are needed for the public API.
- Treat a `201` as "request received", not "booking confirmed" or "payment taken".

## Production notes

- Install `requirements\prod.txt`, set all required variables in the server environment (not in a committed file), and use `config.settings.prod`.
- Run `python manage.py migrate`, `python manage.py createcachetable`, and `python manage.py collectstatic --noinput` on deploy.
- Serve with a production WSGI server such as gunicorn behind HTTPS. Never use `runserver` in production.
- **Set `NUM_PROXIES` correctly.** It is the number of reverse proxies in front of Django. At `0`, every visitor behind a proxy shares one rate limit. If set too high, clients can fake their IP to bypass the limit.
- If HTTPS is terminated by a proxy, set `USE_PROXY_SSL_HEADER=True` only if the proxy sets `X-Forwarded-Proto`. Raise `SECURE_HSTS_SECONDS` once HTTPS is confirmed.
- Production does not serve uploaded media. Configure persistent storage for `MEDIA_ROOT` or an external storage backend before launch.
- Run `python manage.py check --deploy` with production settings before release.

## Troubleshooting

| Problem | Fix |
|---|---|
| `ImproperlyConfigured: Set the SECRET_KEY...` or `DB_*` | A variable is missing from `backend\.env` |
| `password authentication failed` | `DB_PASSWORD` does not match the PostgreSQL user |
| `relation "django_cache_table" does not exist` | Run `python manage.py createcachetable` |
| `permission denied to create database` (tests) | In psql as `postgres`: `ALTER USER safari_user CREATEDB;` |
| `Found 0 tests` or discovery crash | A folder is missing `__init__.py` (check `apps\`) |
| Admin looks unstyled or error `500` | Production settings are active in your terminal. Clear `DJANGO_SETTINGS_MODULE` or open a fresh window |
| Every booking returns `429` | You hit the limit. Clear the cache (see "Booking protection") |
| Port 8000 already in use | `netstat -ano \| findstr :8000`, then `taskkill /PID <number> /F` |
| `No module named 'django'` | The virtual environment is not active. Run `venv\Scripts\activate.bat` |

## Decisions still open (with the frontend developer)

1. Per-person pricing: assumed.
2. Initial currency: the field exists and defaults to `USD` as a placeholder.
3. Detail URLs: integer IDs, as assumed in the contract.
4. Production image storage: undecided.
5. Booking response: contains the package ID only, with no title or currency.
6. Contract amendments needed: add `429` to the status codes and state the rate limit. State that `includes` and `excludes` are arrays of strings. State the list ordering.