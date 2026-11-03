# Safari Travels API Contract

**Status:** Draft v0.1  
**Backend:** Django REST Framework  
**Frontend:** React + Vite  
**Database:** PostgreSQL

## 1. Base URL

`http://localhost:8000/api/`

All requests and responses use JSON unless otherwise specified. API endpoints use trailing slashes.

## 2. General conventions

- IDs are integers.
- Field names use snake_case.
- Prices are returned as strings with two decimal places, such as `"850.00"`.
- Dates use `YYYY-MM-DD`.
- Timestamps use ISO 8601.
- Image fields return absolute URLs.
- List endpoints use Django REST Framework pagination with a page size of 12.
- CORS allows the frontend origin `http://localhost:5173`.
- PostgreSQL is the only supported database.

## 3. Destinations

### List destinations

`GET /api/destinations/`

Returns active destinations with pagination.

Each destination contains:
- `id`
- `name`
- `country`
- `slug`
- `short_description`
- `image`
- `package_count`

### Destination details

`GET /api/destinations/{id}/`

Returns the destination fields above, plus `description`.

## 4. Travel packages

### List packages

`GET /api/packages/`

Returns active packages with pagination.

Optional query parameters:
- `destination=1`
- `featured=true`
- `min_price=100`
- `max_price=1000`
- `page=2`

Each package contains:
- `id`
- `title`
- `slug`
- `destination`, containing `id` and `name`
- `price`
- `currency`
- `duration_days`
- `image`
- `short_description`
- `is_featured`

### Package details

`GET /api/packages/{id}/`

Returns the package fields above, plus:
- `description`
- `includes`
- `excludes`
- `itinerary`, an array of objects containing `day`, `title`, and `description`
- `max_group_size`

## 5. Bookings

### Submit a booking request

`POST /api/bookings/`

Request body:

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

Validation rules:
- `package` must identify an active package.
- `full_name` is required, with a maximum length of 120 characters.
- `email` is required and must be valid.
- `phone` is required, with a maximum length of 20 characters.
- `travel_date` is required and must be in the future.
- `number_of_travelers` must be at least 1 and no greater than the package's `max_group_size`.
- `message` is optional, with a maximum length of 1000 characters.

A successful request returns HTTP `201 Created`.

The backend calculates the total price. New bookings have status `pending`. Submitting a booking does not mean payment or travel has been confirmed.

The response includes:
- `id`
- `package`
- `full_name`
- `email`
- `phone`
- `travel_date`
- `number_of_travelers`
- `message`
- `status`
- `total_price`
- `created_at`

There are no public endpoints for listing or retrieving bookings. Staff manage bookings through the Django admin.

## 6. Error responses

Validation errors return HTTP `400 Bad Request`.

Example:

```json
{
  "email": ["Enter a valid email address."]
}
```

Use `non_field_errors` for errors that do not belong to a specific field.

Other expected status codes:
- `200`: Successful GET request
- `201`: Booking request created
- `400`: Invalid request
- `404`: Resource not found
- `500`: Unexpected server error

## 7. Pagination

List endpoints return:

```json
{
  "count": 12,
  "next": null,
  "previous": null,
  "results": []
}
```

The page size is 12.

## 8. Authentication and security

- Public destination and package endpoints require no authentication.
- Booking submission is public but must be validated and rate-limited.
- Django admin requires staff authentication.
- Never expose secrets or database credentials in API responses.
- Environment variables and real `.env` files must not be committed to Git.

## 9. Decisions to confirm before implementation

Both collaborators must agree on:
1. Whether package prices are per person or per group. The current assumption is per person.
2. Which currency to use for the initial release.
3. Whether API detail URLs use integer IDs, slugs, or both. The current assumption is integer IDs.
4. How uploaded images will be stored in production.
5. Whether booking responses include the package title and currency.

**Change policy:** This document is a draft until both collaborators approve it. Changes to the agreed contract require review through a pull request.