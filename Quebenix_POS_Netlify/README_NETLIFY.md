# Quebenix POS — Netlify Edition

## Deploy to Netlify
1. Extract this ZIP.
2. Open https://app.netlify.com/ and sign in.
3. Choose **Add new site → Deploy manually**.
4. Drag the extracted `Quebenix_POS_Netlify` folder (the folder containing `index.html` and `netlify.toml`) into the deploy area.
5. Netlify will publish the site and provide a public `*.netlify.app` URL.

## Demo login
- Email: `admin@quebenix.com`
- Password: `Admin@123`

## Included
- Existing Quebenix POS visual theme, logo, CSS and responsive layout.
- Dashboard, POS checkout, clients, service catalog, sales/invoices, projects, expenses, reports, staff and company settings.
- Local browser persistence through `localStorage`.
- Invoice print / Save as PDF and sales CSV export.
- Netlify SPA redirect configuration.

## Important data and security notes
This is a static frontend deployment. Data is stored in the browser's `localStorage` on the device/browser where it is entered. It is not a shared online database and does not automatically sync between different users, devices or browsers. Clearing browser storage can erase the saved records. Browser-side login and stored passwords are suitable only for a demo/internal prototype, not secure production authentication. For multi-user access, shared data, secure roles and backups, connect a hosted backend/database such as Supabase or Firebase.

The original Flask/Python server, SQLite database and virtual environment are intentionally not included because Netlify static hosting does not execute Flask applications.
