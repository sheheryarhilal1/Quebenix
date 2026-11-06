from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, date
from io import BytesIO
import os, sqlite3, csv
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

def db():
    if app.config["DB_TYPE"] == "mysql":
        import pymysql
        return pymysql.connect(host=app.config["MYSQL_HOST"], user=app.config["MYSQL_USER"],
            password=app.config["MYSQL_PASSWORD"], database=app.config["MYSQL_DATABASE"],
            cursorclass=pymysql.cursors.DictCursor, autocommit=True)
    conn = sqlite3.connect(app.config["SQLITE_PATH"])
    conn.row_factory = sqlite3.Row
    return conn

def execute(cur, sql, params=()):
    if app.config["DB_TYPE"] == "sqlite":
        sql = sql.replace("%s", "?")
    return cur.execute(sql, params)

def executemany(cur, sql, rows):
    if app.config["DB_TYPE"] == "sqlite":
        sql = sql.replace("%s", "?")
    return cur.executemany(sql, rows)

def query(sql, params=(), one=False, write=False):
    conn = db()
    try:
        cur = conn.cursor()
        execute(cur, sql, params)
        if write:
            if app.config["DB_TYPE"] == "sqlite":
                conn.commit()
            return cur.lastrowid if app.config["DB_TYPE"] == "sqlite" else cur.lastrowid
        rows = cur.fetchall()
        return (dict(rows[0]) if rows else None) if one else [dict(r) for r in rows]
    finally:
        conn.close()

def init_db():
    schema = [
    """CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name VARCHAR(120), email VARCHAR(160) UNIQUE, password VARCHAR(255), role VARCHAR(30) DEFAULT 'Staff', active INTEGER DEFAULT 1, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE TABLE IF NOT EXISTS clients (id INTEGER PRIMARY KEY AUTOINCREMENT, name VARCHAR(160) NOT NULL, company VARCHAR(160), email VARCHAR(160), phone VARCHAR(60), address TEXT, notes TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE TABLE IF NOT EXISTS services (id INTEGER PRIMARY KEY AUTOINCREMENT, name VARCHAR(160) NOT NULL, category VARCHAR(100), price DECIMAL(12,2) DEFAULT 0, description TEXT, active INTEGER DEFAULT 1)""",
    """CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY AUTOINCREMENT, invoice_no VARCHAR(60) UNIQUE, client_id INTEGER, subtotal DECIMAL(12,2), discount DECIMAL(12,2), tax DECIMAL(12,2), total DECIMAL(12,2), payment_method VARCHAR(50), status VARCHAR(30) DEFAULT 'Paid', notes TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE TABLE IF NOT EXISTS sale_items (id INTEGER PRIMARY KEY AUTOINCREMENT, sale_id INTEGER, service_id INTEGER, description VARCHAR(255), qty INTEGER, unit_price DECIMAL(12,2), line_total DECIMAL(12,2))""",
    """CREATE TABLE IF NOT EXISTS projects (id INTEGER PRIMARY KEY AUTOINCREMENT, client_id INTEGER, title VARCHAR(180), service VARCHAR(120), status VARCHAR(40) DEFAULT 'Planning', start_date DATE, due_date DATE, budget DECIMAL(12,2) DEFAULT 0, notes TEXT)""",
    """CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY AUTOINCREMENT, title VARCHAR(180), category VARCHAR(100), amount DECIMAL(12,2), expense_date DATE, notes TEXT)""",
    """CREATE TABLE IF NOT EXISTS settings (id INTEGER PRIMARY KEY, company_name VARCHAR(180), email VARCHAR(180), phone VARCHAR(80), address TEXT, currency VARCHAR(10), tax_rate DECIMAL(6,2), logo_url TEXT)"""
    ]
    conn = db()
    try:
        cur = conn.cursor()
        for s in schema:
            if app.config["DB_TYPE"] == "mysql": s = s.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "INT AUTO_INCREMENT PRIMARY KEY")
            execute(cur, s)
        if app.config["DB_TYPE"] == "sqlite": conn.commit()
        count = cur.execute("SELECT COUNT(*) AS n FROM users").fetchone()
        n = count["n"] if isinstance(count, dict) else count[0]
        if n == 0:
            execute(cur, "INSERT INTO users (name,email,password,role) VALUES (%s,%s,%s,%s)",
                ("Quebenix Admin","admin@quebenix.com",generate_password_hash("Admin@123"),"Admin"))
        c = cur.execute("SELECT COUNT(*) AS n FROM services").fetchone()
        n = c["n"] if isinstance(c, dict) else c[0]
        if n == 0:
            seeds = [
            ("Website Development","Web Development",75000,"Business websites, landing pages and eCommerce"),
            ("Mobile App Development","Mobile Apps",150000,"Android and iOS application development"),
            ("Power BI Dashboard","Data Analytics",45000,"Interactive BI dashboards and reporting"),
            ("Data Analysis","Data Analytics",30000,"SQL, Python, Excel analysis and insights"),
            ("QA Testing","Quality Assurance",20000,"Manual testing, automation, API and performance testing"),
            ("SEO","SEO",22000,"Technical SEO, on-page optimization and content strategy"),
            ("Digital Marketing","Digital Marketing",25000,"Social media, campaigns and performance marketing"),
            ("Data Science","Data Science",60000,"Data modeling, predictive analytics and machine learning solutions"),
            ("UI/UX Design","Design",35000,"User research, wireframes and interface design")
            ]
            executemany(cur, "INSERT INTO services (name,category,price,description) VALUES (%s,%s,%s,%s)", seeds)
        c = cur.execute("SELECT COUNT(*) AS n FROM settings").fetchone()
        n = c["n"] if isinstance(c, dict) else c[0]
        if n == 0:
            execute(cur, "INSERT INTO settings (id,company_name,email,phone,address,currency,tax_rate,logo_url) VALUES (1,%s,%s,%s,%s,%s,%s,%s)",
                ("Quebenix Technology","quebenixtechnology4@gmail.com","+92 300 0000000","Karachi, Pakistan","PKR",0,"/static/img/quebenix-logo.jpg"))
        if app.config["DB_TYPE"] == "sqlite": conn.commit()
    finally: conn.close()

def login_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"): return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapped

def admin_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if session.get("role") != "Admin":
            flash("Admin permission required.", "error")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return wrapped

@app.context_processor
def common():
    s = query("SELECT * FROM settings WHERE id=1", one=True) or {}
    return {"company":s, "current_user":session.get("user_name"), "role":session.get("role"),
            "currency":s.get("currency","PKR")}

@app.route("/")
def home():
    return redirect(url_for("dashboard") if session.get("user_id") else url_for("login"))

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = query("SELECT * FROM users WHERE email=%s AND active=1", (request.form.get("email",""),), one=True)
        if u and check_password_hash(u["password"], request.form.get("password","")):
            session.update(user_id=u["id"], user_name=u["name"], role=u["role"])
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.", "error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear(); return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    stats = {
      "revenue": query("SELECT COALESCE(SUM(total),0) v FROM sales WHERE status='Paid'",one=True)["v"],
      "sales": query("SELECT COUNT(*) v FROM sales",one=True)["v"],
      "clients": query("SELECT COUNT(*) v FROM clients",one=True)["v"],
      "projects": query("SELECT COUNT(*) v FROM projects WHERE status NOT IN ('Completed','Cancelled')",one=True)["v"],
      "expenses": query("SELECT COALESCE(SUM(amount),0) v FROM expenses",one=True)["v"]
    }
    recent = query("""SELECT s.*, c.name client_name FROM sales s LEFT JOIN clients c ON c.id=s.client_id ORDER BY s.id DESC LIMIT 7""")
    monthly = query("""SELECT substr(created_at,1,7) month, SUM(total) total FROM sales WHERE created_at >= date('now','-5 months') GROUP BY substr(created_at,1,7) ORDER BY month""") if app.config["DB_TYPE"]=="sqlite" else query("SELECT DATE_FORMAT(created_at,'%Y-%m') month, SUM(total) total FROM sales WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 5 MONTH) GROUP BY month ORDER BY month")
    return render_template("dashboard.html", stats=stats, recent=recent, monthly=monthly)

@app.route("/clients", methods=["GET","POST"])
@login_required
def clients():
    if request.method=="POST":
        query("INSERT INTO clients(name,company,email,phone,address,notes) VALUES(%s,%s,%s,%s,%s,%s)",
          tuple(request.form.get(k,"") for k in ["name","company","email","phone","address","notes"]),write=True)
        flash("Client added successfully.","success"); return redirect(url_for("clients"))
    rows=query("SELECT * FROM clients ORDER BY id DESC")
    return render_template("clients.html", clients=rows)

@app.route("/clients/delete/<int:id>", methods=["POST"])
@login_required
def delete_client(id):
    query("DELETE FROM clients WHERE id=%s",(id,),write=True); flash("Client deleted.","success")
    return redirect(url_for("clients"))

@app.route("/services", methods=["GET","POST"])
@login_required
def services():
    if request.method=="POST":
        query("INSERT INTO services(name,category,price,description) VALUES(%s,%s,%s,%s)",
          (request.form["name"],request.form["category"],request.form["price"],request.form.get("description","")),write=True)
        flash("Service added.","success"); return redirect(url_for("services"))
    return render_template("services.html", services=query("SELECT * FROM services ORDER BY category,name"))

@app.route("/services/delete/<int:id>",methods=["POST"])
@login_required
def delete_service(id):
    query("UPDATE services SET active=0 WHERE id=%s",(id,),write=True); flash("Service archived.","success")
    return redirect(url_for("services"))

@app.route("/pos")
@login_required
def pos():
    return render_template("pos.html", services=query("SELECT * FROM services WHERE active=1 ORDER BY category,name"),
                           clients=query("SELECT * FROM clients ORDER BY name"))

@app.route("/checkout",methods=["POST"])
@login_required
def checkout():
    import json, uuid
    try:
        items=json.loads(request.form.get("items","[]"))
        if not items: raise ValueError("Add at least one service.")
        client_id=request.form.get("client_id") or None
        discount=max(0,float(request.form.get("discount",0) or 0))
        tax_rate=float((query("SELECT tax_rate FROM settings WHERE id=1",one=True) or {}).get("tax_rate") or 0)
        subtotal=0; normalized=[]
        for item in items:
            service=query("SELECT * FROM services WHERE id=%s AND active=1",(int(item["id"]),),one=True)
            if not service: continue
            qty=max(1,int(item.get("qty",1))); price=float(service["price"])
            line=qty*price; subtotal+=line
            normalized.append((service,qty,price,line))
        if not normalized: raise ValueError("No valid services selected.")
        discount=min(discount,subtotal); tax=(subtotal-discount)*tax_rate/100; total=subtotal-discount+tax
        invoice="QBX-"+datetime.now().strftime("%y%m%d")+"-"+uuid.uuid4().hex[:6].upper()
        sale_id=query("INSERT INTO sales(invoice_no,client_id,subtotal,discount,tax,total,payment_method,status,notes) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)",
          (invoice,client_id,subtotal,discount,tax,total,request.form.get("payment_method","Cash"),request.form.get("status","Paid"),request.form.get("notes","")),write=True)
        for service,qty,price,line in normalized:
            query("INSERT INTO sale_items(sale_id,service_id,description,qty,unit_price,line_total) VALUES(%s,%s,%s,%s,%s,%s)",
              (sale_id,service["id"],service["name"],qty,price,line),write=True)
        flash("Sale completed. Invoice "+invoice,"success")
        return redirect(url_for("invoice",id=sale_id))
    except Exception as e:
        flash(str(e),"error"); return redirect(url_for("pos"))

@app.route("/sales")
@login_required
def sales():
    rows=query("SELECT s.*,c.name client_name FROM sales s LEFT JOIN clients c ON c.id=s.client_id ORDER BY s.id DESC")
    return render_template("sales.html", sales=rows)

@app.route("/invoice/<int:id>")
@login_required
def invoice(id):
    sale=query("SELECT s.*,c.name client_name,c.company,c.email,c.phone,c.address FROM sales s LEFT JOIN clients c ON c.id=s.client_id WHERE s.id=%s",(id,),one=True)
    if not sale: return "Invoice not found",404
    items=query("SELECT * FROM sale_items WHERE sale_id=%s",(id,))
    return render_template("invoice.html",sale=sale,items=items)

@app.route("/projects",methods=["GET","POST"])
@login_required
def projects():
    if request.method=="POST":
        query("INSERT INTO projects(client_id,title,service,status,start_date,due_date,budget,notes) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",
          (request.form.get("client_id") or None,request.form["title"],request.form["service"],request.form["status"],request.form.get("start_date") or None,request.form.get("due_date") or None,request.form.get("budget") or 0,request.form.get("notes","")),write=True)
        flash("Project created.","success"); return redirect(url_for("projects"))
    rows=query("SELECT p.*,c.name client_name FROM projects p LEFT JOIN clients c ON c.id=p.client_id ORDER BY p.id DESC")
    return render_template("projects.html",projects=rows,clients=query("SELECT * FROM clients ORDER BY name"))

@app.route("/projects/status/<int:id>",methods=["POST"])
@login_required
def project_status(id):
    query("UPDATE projects SET status=%s WHERE id=%s",(request.form["status"],id),write=True)
    flash("Project status updated.","success"); return redirect(url_for("projects"))

@app.route("/expenses",methods=["GET","POST"])
@login_required
def expenses():
    if request.method=="POST":
        query("INSERT INTO expenses(title,category,amount,expense_date,notes) VALUES(%s,%s,%s,%s,%s)",
          (request.form["title"],request.form["category"],request.form["amount"],request.form["expense_date"],request.form.get("notes","")),write=True)
        flash("Expense recorded.","success"); return redirect(url_for("expenses"))
    return render_template("expenses.html",expenses=query("SELECT * FROM expenses ORDER BY expense_date DESC"))

@app.route("/reports")
@login_required
def reports():
    totals=query("SELECT COUNT(*) sales,COALESCE(SUM(total),0) revenue,COALESCE(SUM(discount),0) discounts,COALESCE(SUM(tax),0) tax FROM sales",one=True)
    by_service=query("SELECT description, SUM(qty) quantity, SUM(line_total) revenue FROM sale_items GROUP BY description ORDER BY revenue DESC")
    return render_template("reports.html",totals=totals,by_service=by_service)

@app.route("/settings",methods=["GET","POST"])
@login_required
@admin_required
def settings():
    if request.method=="POST":
        query("UPDATE settings SET company_name=%s,email=%s,phone=%s,address=%s,currency=%s,tax_rate=%s,logo_url=%s WHERE id=1",
          tuple(request.form.get(k,"") for k in ["company_name","email","phone","address","currency","tax_rate","logo_url"]),write=True)
        flash("Settings saved.","success"); return redirect(url_for("settings"))
    return render_template("settings.html",settings=query("SELECT * FROM settings WHERE id=1",one=True))

@app.route("/staff",methods=["GET","POST"])
@login_required
@admin_required
def staff():
    if request.method=="POST":
        query("INSERT INTO users(name,email,password,role) VALUES(%s,%s,%s,%s)",
          (request.form["name"],request.form["email"],generate_password_hash(request.form["password"]),request.form["role"]),write=True)
        flash("Staff account created.","success"); return redirect(url_for("staff"))
    return render_template("staff.html",staff=query("SELECT id,name,email,role,active,created_at FROM users ORDER BY id DESC"))

@app.route("/staff/toggle/<int:id>",methods=["POST"])
@login_required
@admin_required
def staff_toggle(id):
    query("UPDATE users SET active=CASE WHEN active=1 THEN 0 ELSE 1 END WHERE id=%s AND role!='Admin'",(id,),write=True)
    return redirect(url_for("staff"))

@app.route("/export/sales.csv")
@login_required
def export_sales():
    rows=query("SELECT invoice_no,created_at,client_id,subtotal,discount,tax,total,payment_method,status FROM sales ORDER BY id DESC")
    output=BytesIO()
    import io
    s=io.StringIO(); w=csv.writer(s); w.writerow(["Invoice","Date","Client ID","Subtotal","Discount","Tax","Total","Payment","Status"])
    for r in rows: w.writerow(list(r.values()))
    return app.response_class(s.getvalue(),mimetype="text/csv",headers={"Content-Disposition":"attachment;filename=quebenix-sales.csv"})


if __name__ == "__main__":
    init_db()

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False,
        use_reloader=False
    )
