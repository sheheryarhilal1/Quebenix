QUEBENIX TECHNOLOGY POS SYSTEM

WINDOWS QUICK START (PowerShell)
1. Open this folder in VS Code.
2. Create virtual environment:
   py -m venv venv
3. If PowerShell blocks activation, use this temporary setting for this terminal only:
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
4. Activate:
   .\venv\Scripts\Activate.ps1
5. Install packages:
   python -m pip install -r requirements.txt
6. Start:
   python app.py
7. Open http://127.0.0.1:5000

ALTERNATIVE WITHOUT POWERSHELL ACTIVATION
You can skip activation entirely and run:
   py -m venv venv
   .\venv\Scripts\python.exe -m pip install -r requirements.txt
   .\venv\Scripts\python.exe app.py

ALTERNATIVE USING COMMAND PROMPT (CMD)
Open CMD terminal instead of PowerShell:
   venv\Scripts\activate.bat

DEMO LOGIN
Email: admin@quebenix.com
Password: Admin@123

DATABASE NOTE
SQLite is the default. The app converts %s placeholders to ? for SQLite.
The settings seed query uses 8 columns: id plus 7 parameter placeholders.
If you have an existing database, back it up before making changes.

SECURITY
Change the default admin password and SECRET_KEY before production deployment.
