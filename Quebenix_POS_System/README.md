# Quebenix Technology — Service POS

A branded service-business POS and operations dashboard for Quebenix Technology. It includes client CRM, service catalog, checkout, invoice view/print, projects, expenses, reports, staff roles and company settings.

## Quick start (Windows)
1. Install Python 3.10+.
2. Extract the ZIP and open this folder in VS Code.
3. Open Terminal:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   python app.py
   ```
4. Open http://127.0.0.1:5000

## Demo admin
- Email: `admin@quebenix.com`
- Password: `Admin@123`

Change the demo password and `SECRET_KEY` before real deployment. Do not expose the development server publicly.

## Database
SQLite is the zero-configuration default. For MySQL:
1. Create database `quebenix_pos` (see `schema_mysql.sql`).
2. Copy `.env.example` values into your environment and set `DB_TYPE=mysql`, `MYSQL_*`.
3. Run `python app.py`. The application creates tables and seeds starter services.

## Main modules
- Dashboard KPIs and recent sales
- POS checkout with service quantities, discount, tax and payment method
- Client records
- Service catalog
- Invoice details and browser print/save as PDF
- Projects and status tracking
- Expenses
- Revenue/service reports and CSV export
- Admin settings and staff account management

## Important
This starter is designed for a single-company internal workflow. Before production use, add HTTPS, secure secrets, database backups, CSRF protection, audit logging, password reset, stronger validation, and a production WSGI server. Online payment processing is not connected; payment methods are recorded manually.
