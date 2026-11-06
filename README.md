# Quebenix Technology — POS (Streamlit Edition)

This folder is the Streamlit conversion of the original Flask POS project. It provides:
- Login with hashed passwords and Admin/Staff roles
- Dashboard KPIs and monthly revenue chart
- POS checkout with service quantities, discount, tax, payment status and invoice summary
- Clients and service catalog management
- Sales history and CSV invoice/sales export
- Projects and status tracking
- Expense tracking and CSV export
- Reports, staff management and company settings
- Change Password page

## Run locally (Windows)

1. Install Python 3.10 or newer.
2. Extract this folder and open it in VS Code.
3. In Terminal:

```powershell
py -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
streamlit run app.py
```

4. Open the local URL printed in the terminal (usually http://localhost:8501).

## Demo admin login

- Email: `admin@quebenix.com`
- Password: `Admin@123`

**Immediately sign in and use Change Password before publishing.** Also set a strong Streamlit app password / access control if this is for internal company use. The demo credentials are public in this README and must never remain active on a public business system.

## Deploy publicly with Streamlit Community Cloud

1. Create a GitHub repository, e.g. `Quebenix-POS-Streamlit`.
2. Upload the contents of this folder to the repository root (not the parent folder).
3. Push/commit the project to GitHub.
4. Open https://share.streamlit.io/ and sign in with GitHub.
5. Choose **Create app** → select your repository, branch (`main`) and file path (`app.py`).
6. Click **Deploy**. Streamlit will install packages from `requirements.txt`.
7. Your public URL will look like `https://your-app-name.streamlit.app`.

## Important: data persistence and security

This conversion currently uses SQLite (`quebenix_pos.db`) to make the app easy to run and demonstrate. Streamlit Community Cloud's local filesystem is not a reliable permanent database for business records; app rebuilds/restarts or redeployments can cause local-file data to be lost or reset. For real customer/sales data, migrate to a hosted PostgreSQL database (for example Supabase) and configure credentials through Streamlit **App → Settings → Secrets**. Do not commit database files containing real customer information, passwords, or invoices to GitHub.

Before production use, add CSRF-equivalent protections appropriate to Streamlit, stronger role/permission rules, audit logging, backups, password reset, and hosted database persistence. Payment methods are recorded manually; no online payment gateway is connected.

## Original Flask version

The original Flask project is not needed to run this Streamlit edition. This version uses native Streamlit widgets rather than Flask routes/Jinja templates.
"# Quebenix" 
