# Healthcare Backend API

A simple Django REST API for managing patients, doctors, and patient–doctor assignments. Built with Django, Django REST Framework, PostgreSQL, and JWT authentication.

## Requirements

- Python 3.10+
- PostgreSQL (e.g. [Neon](https://neon.tech/) hosted database)

## PostgreSQL setup

Create a PostgreSQL database on Neon (or another host) and copy the connection string into `.env` as `DATABASE_URL`. Neon connection strings look like:

`postgresql://user:password@host/dbname?sslmode=require`

## Environment variables

1. Copy the example file:

```bash
copy .env.example .env
```

On Linux/macOS: `cp .env.example .env`

2. Edit `.env` and set `SECRET_KEY` and `DATABASE_URL` (your Neon PostgreSQL connection string).

Never commit `.env` to version control.

## Installation

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

On Linux/macOS: `source venv/bin/activate`

## Migrations

```bash
python manage.py migrate
```

Run tests:

```bash
python manage.py test api
```

Optional superuser for Django admin:

```bash
python manage.py createsuperuser
```

## Run the server

```bash
python manage.py runserver
```

API base URL: `http://127.0.0.1:8000/api/`

## Authentication flow

1. **Register** — `POST /api/auth/register/` with `name`, `email`, `password` (no token required).
2. **Login** — `POST /api/auth/login/` with `email`, `password`. Response includes `access` and `refresh` JWT tokens.
3. **Protected routes** — Send header: `Authorization: Bearer <access_token>`.

## API endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/register/` | No | Register a new user |
| POST | `/api/auth/login/` | No | Obtain JWT tokens |
| GET, POST | `/api/patients/` | Yes | List/create patients (own patients only) |
| GET, PUT, DELETE | `/api/patients/<id>/` | Yes | Retrieve/update/delete own patient |
| GET, POST | `/api/doctors/` | Yes | List/create doctors |
| GET, PUT, DELETE | `/api/doctors/<id>/` | Yes | Retrieve/update/delete doctor |
| GET, POST | `/api/mappings/` | Yes | List/create mappings (own patients) |
| GET | `/api/mappings/<patient_id>/` | Yes | Doctors assigned to a patient |
| DELETE | `/api/mappings/<id>/` | Yes | Delete a mapping by mapping id |

**Note:** `GET` and `DELETE` on `/api/mappings/<pk>/` use the same URL pattern: `GET` treats `pk` as **patient id**; `DELETE` treats `pk` as **mapping id**.

## Example requests

### Register

```bash
curl -X POST http://127.0.0.1:8000/api/auth/register/ ^
  -H "Content-Type: application/json" ^
  -d "{\"name\": \"John Doe\", \"email\": \"john@example.com\", \"password\": \"password123\"}"
```

### Login

```bash
curl -X POST http://127.0.0.1:8000/api/auth/login/ ^
  -H "Content-Type: application/json" ^
  -d "{\"email\": \"john@example.com\", \"password\": \"password123\"}"
```

### Create patient

```bash
curl -X POST http://127.0.0.1:8000/api/patients/ ^
  -H "Content-Type: application/json" ^
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" ^
  -d "{\"name\": \"Jane Patient\", \"age\": 30, \"gender\": \"F\", \"address\": \"123 Main St\", \"phone\": \"555-0100\"}"
```

Gender: `M`, `F`, or `O` (or `Male`, `Female`, `Other` — stored as `M`/`F`/`O` in responses).

### List patients

```bash
curl http://127.0.0.1:8000/api/patients/ ^
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Create doctor

```bash
curl -X POST http://127.0.0.1:8000/api/doctors/ ^
  -H "Content-Type: application/json" ^
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" ^
  -d "{\"name\": \"Dr. Smith\", \"specialization\": \"Cardiology\", \"phone\": \"555-0200\", \"email\": \"smith@clinic.com\"}"
```

### Assign doctor to patient

```bash
curl -X POST http://127.0.0.1:8000/api/mappings/ ^
  -H "Content-Type: application/json" ^
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" ^
  -d "{\"patient\": 1, \"doctor\": 1}"
```

### Get doctors for a patient (patient_id = 1)

```bash
curl http://127.0.0.1:8000/api/mappings/1/ ^
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Delete mapping (mapping_id = 1)

```bash
curl -X DELETE http://127.0.0.1:8000/api/mappings/1/ ^
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Error responses

- **401** — Missing/invalid token or invalid login credentials
- **400** — Validation errors (missing fields, duplicate email, duplicate mapping)
- **404** — Patient, doctor, or mapping not found (or patient not owned by user)

Errors are returned as JSON, e.g. `{"detail": "..."}` or field errors from serializers.
