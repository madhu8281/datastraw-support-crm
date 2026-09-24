# DataStraw Support CRM

A full-stack customer support CRM built with FastAPI, PostgreSQL/Neon, and vanilla HTML, CSS, and JavaScript.

The project was developed as a hiring assignment for DataStraw Technologies. It allows customers to raise support tickets and gives the support team a dashboard to manage, search, filter, and update tickets.

## Live Demo

https://datastraw-support-crm3.vercel.app/

## Features

* Create customer support tickets
* Automatic ticket IDs such as `TKT-001`
* Dashboard with ticket statistics
* Search tickets by ID, customer, email, subject, or description
* Filter tickets by status and priority
* View ticket details
* Admin password protection for ticket updates
* Update ticket status and priority
* Add ticket notes/history
* Responsive frontend
* Server-side and client-side validation
* Health check endpoint at `/api/health`

## Tech Stack

**Frontend**

* HTML5
* CSS3
* JavaScript

**Backend**

* Python
* FastAPI
* SQLAlchemy
* Pydantic

**Database**

* PostgreSQL with Neon for production
* SQLite for local development

**Deployment**

* Vercel
* GitHub

## Project Structure

```text
support-crm/
│
├── app.py
│
├── backend/
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── crud.py
│   └── main.py
│
├── frontend/
│   ├── index.html
│   ├── create-ticket.html
│   ├── ticket.html
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── api.js
│       ├── app.js
│       ├── create-ticket.js
│       └── ticket.js
│
├── .env.example
├── .gitignore
├── .python-version
├── requirements.txt
└── README.md
```

## How It Works

Customers can create a support ticket by entering their details and explaining the issue.

The support team can then use the dashboard to:

* View tickets
* Search and filter tickets
* Check ticket status and priority
* Open ticket details
* Update ticket information
* Add notes

Ticket status follows a simple workflow:

```text
Open → In Progress → Closed
```

## Database

For local development, the application can use SQLite.

For production, the application uses Neon PostgreSQL because Vercel uses serverless functions and does not provide persistent storage for SQLite files.

Ticket IDs are generated from the database ID, which prevents duplicate ticket numbers when multiple requests are made at the same time.

## Environment Variables

Create a `.env` file for local development when required.

```env
DATABASE_URL=
ADMIN_PASSWORD=
APP_NAME=DataStraw Support
APP_ENV=development
ALLOWED_ORIGINS=*
```

For Vercel production, `DATABASE_URL` should contain the Neon PostgreSQL connection string and `ADMIN_PASSWORD` should contain the admin password.

Do not commit `.env` to GitHub.

## Run Locally

Clone the repository:

```bash
git clone https://github.com/madhu8281/datastraw-support-crm.git
cd datastraw-support-crm
```

Create a virtual environment:

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the application:

```bash
uvicorn app:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

## API

Main endpoints include:

```text
GET    /api/health
GET    /api/tickets
POST   /api/tickets
GET    /api/tickets/{ticket_id}
PUT    /api/tickets/{ticket_id}
```

Example:

```text
GET /api/tickets?status=Open
GET /api/tickets?priority=High
GET /api/tickets?search=login
```

The API documentation is disabled because it is not required for the assessment.

## Deployment

The application is deployed on Vercel with Neon PostgreSQL as the production database.

The frontend and backend use the same Vercel domain, so API requests are made through:

```text
/api/...
```

Before testing ticket creation after deployment, check:

```text
https://your-domain.vercel.app/api/health
```

A successful response should show that the database is connected.

## Future Improvements

* User authentication
* Support agent accounts
* Ticket assignment
* Email notifications
* Ticket comments
* File attachments
* Reports and analytics
* PostgreSQL-based production scaling
* Automated tests

## Developer

**Madhavi Lokhande**

GitHub: https://github.com/madhu8281

LinkedIn: https://linkedin.com/in/madhavilokhande

## License

This project was developed as a hiring assignment for DataStraw Technologies.
