# DataStraw Support CRM — Vercel-ready

A full-stack customer support CRM built with **FastAPI + PostgreSQL/Neon + vanilla HTML/CSS/JavaScript**.

## Why this version fixes the Vercel problem

The earlier version used SQLite as the production database. SQLite is a file, while Vercel functions run on an ephemeral/serverless filesystem. A ticket POST can therefore fail when the function cannot reliably write the SQLite file, and even a successful write should not be treated as permanent production storage.

This version uses:

- **Neon PostgreSQL for Vercel production**
- **SQLite only for local development**
- Lazy database initialization — importing the FastAPI app never tries to create a database file
- Database-generated integer IDs, then `TKT-001`, `TKT-002`, etc. This avoids two simultaneous Vercel requests generating the same ticket number
- Clear database/configuration errors in the API instead of a generic unexplained 500
- Current Vercel zero-config FastAPI deployment: no custom `vercel.json` build configuration is required
- Same-origin frontend and `/api/...` backend

## Project structure

```text
support-crm/
├── app.py
├── backend/
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── crud.py
│   └── main.py
├── frontend/
│   ├── index.html
│   ├── create-ticket.html
│   ├── ticket.html
│   ├── css/style.css
│   └── js/
│       ├── api.js
│       ├── app.js
│       ├── create-ticket.js
│       └── ticket.js
├── .env.example
├── .gitignore
├── .python-version
├── requirements.txt
└── README.md
```

## Features

- Customer ticket creation
- Automatic ticket IDs
- Dashboard with total/open/in-progress/closed counts
- High-priority count
- Search by ticket ID, customer, email, subject and description
- Status and priority filters
- Ticket detail page
- Admin password protection for ticket updates
- Status/priority updates
- Ticket notes/history
- Responsive frontend
- Validation on browser and server
- Health endpoint: `/api/health`
- API documentation disabled because it is not required for the assessment

---

# DEPLOY TO VERCEL

## Step 1 — Put this project in GitHub

Create a new repository, for example:

```text
datastraw-support-crm
```

Upload the **contents of this folder**, not the ZIP file itself.

Your GitHub repository root should contain:

```text
app.py
backend/
frontend/
requirements.txt
.python-version
.env.example
.gitignore
README.md
```

Do not upload `.env`.

---

## Step 2 — Create a Neon PostgreSQL database

Vercel's current Marketplace provides a Neon PostgreSQL integration.

In Vercel:

1. Open your Vercel dashboard.
2. Open the project.
3. Go to **Storage / Marketplace integrations**.
4. Add **Neon**.
5. Create a new Neon database.
6. Allow the integration to add the database environment variable.

Vercel's Neon integration provides a managed PostgreSQL database and supports a Free Plan. The connection string is normally exposed as `DATABASE_URL`.

If Vercel gives you a connection string manually, it should look similar to:

```text
postgresql://USER:PASSWORD@HOST/DATABASE?sslmode=require
```

Do not paste your real password into GitHub or into the source code.

---

## Step 3 — Add the admin password

In:

**Vercel → Project → Settings → Environment Variables**

add:

```text
ADMIN_PASSWORD
```

Example:

```text
ADMIN_PASSWORD=your-strong-admin-password
```

Use your own password.

The browser never contains this password in the source code. The admin enters it in the dashboard and the backend verifies it.

---

## Step 4 — Redeploy

After connecting Neon and adding `ADMIN_PASSWORD`:

1. Go to **Deployments**
2. Redeploy the latest commit

There is intentionally **no old `vercel.json`** in this version. Current Vercel FastAPI support can detect a FastAPI application directly, and `app.py` is the explicit root entrypoint.

---

# Step 5 — Test the deployment BEFORE opening the ticket form

Suppose Vercel gives you:

```text
https://your-project.vercel.app
```

Open:

```text
https://your-project.vercel.app/api/health
```

You should get:

```json
{
  "status": "ok",
  "database": "connected",
  "app": "DataStraw Support"
}
```

### If `/api/health` says database unavailable

Do not test ticket creation yet.

Check:

**Vercel → Settings → Environment Variables**

and confirm:

```text
DATABASE_URL
ADMIN_PASSWORD
```

exist for the **Production** environment.

Then redeploy.

---

# Step 6 — Test ticket creation

Open:

```text
https://your-project.vercel.app/create-ticket.html
```

Fill in:

- Customer name
- Email
- Subject
- Description
- Priority

Click **Create ticket**.

Expected result:

```text
Ticket TKT-001 created.
```

Then the ticket detail page should open.

Create another:

```text
TKT-002
```

The ticket IDs are generated from the database row ID, so simultaneous Vercel requests cannot both calculate the same next ticket number.

---

# Step 7 — Test the dashboard

Open:

```text
https://your-project.vercel.app/
```

You should see the ticket.

Test:

- Search
- Status filter
- Priority filter
- Ticket details
- Admin unlock
- Status update
- Priority update
- Add note

---

# Local development

You do NOT need PostgreSQL just to run the project locally.

If `DATABASE_URL` is empty, the application automatically uses:

```text
support_crm.db
```

locally.

Create a virtual environment:

### Windows

```powershell
python -m venv venv
venv\Scripts\activate
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Copy the example environment:

```powershell
copy .env.example .env
```

Run:

```powershell
uvicorn app:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

The local SQLite database is intentionally only a development convenience. Production must use PostgreSQL.

---

# Environment variables

| Variable | Local | Vercel |
|---|---|---|
| `DATABASE_URL` | Optional; empty = SQLite | **Required; Neon PostgreSQL** |
| `ADMIN_PASSWORD` | Optional fallback | **Required/recommended** |
| `APP_NAME` | Optional | Optional |
| `APP_ENV` | Optional | Optional |
| `ALLOWED_ORIGINS` | `*` | Usually `*` because frontend/API share the same domain |

---

# Database design

## tickets

| Column | Purpose |
|---|---|
| `id` | Database-generated primary key |
| `ticket_id` | Public ID such as `TKT-001` |
| `customer_name` | Customer |
| `customer_email` | Customer email |
| `subject` | Ticket subject |
| `description` | Problem description |
| `status` | Open / In Progress / Closed |
| `priority` | Low / Medium / High |
| `created_at` | UTC creation time |
| `updated_at` | UTC update time |

## notes

| Column | Purpose |
|---|---|
| `id` | Note primary key |
| `ticket_id` | Related ticket |
| `note_text` | Agent note |
| `created_at` | UTC note time |

---

# API

### Health

```http
GET /api/health
```

### Create ticket

```http
POST /api/tickets
```

Example:

```json
{
  "customer_name": "Madhavi Lokhande",
  "customer_email": "madhavi@example.com",
  "subject": "Unable to login",
  "description": "I cannot access my account.",
  "priority": "High"
}
```

### List tickets

```http
GET /api/tickets
```

Filters:

```text
/api/tickets?status=Open
/api/tickets?priority=High
/api/tickets?search=login
```

### Ticket detail

```http
GET /api/tickets/TKT-001
```

### Admin update

```http
PUT /api/tickets/TKT-001
```

Header:

```text
X-Admin-Password: your-password
```

Body:

```json
{
  "status": "In Progress",
  "priority": "High",
  "notes": "Customer has been contacted."
}
```

---

# Important Vercel rule

Do not change production back to:

```text
sqlite:///...
```

Vercel is not a persistent SQLite server.

Use:

```text
DATABASE_URL=postgresql://...
```

with Neon for the deployed application.

The frontend does not need a separate backend URL. It continues using:

```javascript
/api/tickets
```

because both the frontend and FastAPI backend are deployed under the same Vercel domain.

---

# Troubleshooting

## "Something went wrong on the server" when raising a ticket

Open:

```text
/api/health
```

If it does not say:

```json
"database": "connected"
```

fix `DATABASE_URL` first.

If health is OK but ticket creation still fails:

1. Open Vercel → Deployments
2. Open the latest deployment
3. Open **Functions / Runtime Logs**
4. Look for a database error
5. Make sure the Neon database has not been deleted or disconnected

The new backend logs the actual server-side exception while returning a safe message to the customer.

## "DATABASE_URL is not configured"

Add `DATABASE_URL` to the Vercel project Environment Variables and redeploy.

## Admin update returns 401

The `ADMIN_PASSWORD` in Vercel must exactly match the password entered in the dashboard.

After changing the password, reload the browser and unlock admin again.

## Frontend opens but API does not work

Test:

```text
/api/health
```

If that endpoint works, the backend is running and the issue is likely a frontend request or browser cache. Hard refresh the page.

---

# Why PostgreSQL is used here

The assessment requires a deployed full-stack CRM where tickets must persist.

SQLite is excellent for a small local application, but its database is a file. A serverless deployment should use a real persistent database service.

Neon PostgreSQL gives this project:

- Persistent ticket data
- Safe concurrent writes
- No dependency on the Vercel function filesystem
- Database access through `DATABASE_URL`
- Easy Vercel integration
- A path that can grow beyond a demo

For this assessment, this keeps the architecture simple:

```text
Browser
   ↓
Vercel
   ↓
FastAPI
   ↓
Neon PostgreSQL
```


## Vercel routing fix

This version includes `api/index.py` as the explicit Vercel FastAPI entrypoint.
The API routes intentionally include `/api` (for example `/api/tickets`).
After deployment verify:

```text
https://YOUR-DOMAIN.vercel.app/api/health
https://YOUR-DOMAIN.vercel.app/api/tickets
```

Use `vercel dev` locally to test the same routing Vercel uses.
