import os, sqlite3, uuid, csv, io
from contextlib import closing
from datetime import datetime, date
import pandas as pd
import streamlit as st
from werkzeug.security import check_password_hash, generate_password_hash

st.set_page_config(page_title="Quebenix POS", page_icon="💼", layout="wide", initial_sidebar_state="expanded")
DB_PATH = os.getenv("SQLITE_PATH", "quebenix_pos.db")
DEFAULT_ADMIN_EMAIL = "admin@quebenix.com"
DEFAULT_ADMIN_PASSWORD = "Admin@123"

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] {font-family:'DM Sans',sans-serif;}
.stApp {background:linear-gradient(135deg,#06111f 0%,#081a2e 55%,#06111f 100%);color:#eaf4ff;}
[data-testid="stSidebar"] {background:#071321;border-right:1px solid #16324c;}
[data-testid="stMetric"] {background:#0d2033;border:1px solid #1b3b57;padding:16px;border-radius:14px;}
[data-testid="stMetricValue"] {color:#20c7ff;}
h1,h2,h3 {color:#f2f8ff;}
.stButton>button, .stDownloadButton>button {background:#079cff;color:white;border:0;border-radius:9px;font-weight:700;}
.stButton>button:hover,.stDownloadButton>button:hover {background:#20c7ff;color:#03111e;}
div[data-testid="stForm"] {background:#0b1d30;border:1px solid #1b3b57;padding:18px;border-radius:14px;}
[data-testid="stDataFrame"] {border:1px solid #1b3b57;border-radius:10px;}
.small-muted {color:#91a9bd;font-size:13px;}
</style>
""", unsafe_allow_html=True)

def connect():
    conn=sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory=sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def run(sql, params=(), fetch="none"):
    with closing(connect()) as con:
        cur=con.execute(sql,params)
        if fetch=="one":
            r=cur.fetchone()
            return dict(r) if r else None
        if fetch=="all":
            return [dict(x) for x in cur.fetchall()]
        con.commit()
        return cur.lastrowid

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
    with closing(connect()) as con:
        for sql in schema: con.execute(sql)
        if con.execute("SELECT COUNT(*) FROM users").fetchone()[0]==0:
            con.execute("INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)",
                ("Quebenix Admin",DEFAULT_ADMIN_EMAIL,generate_password_hash(DEFAULT_ADMIN_PASSWORD),"Admin"))
        if con.execute("SELECT COUNT(*) FROM services").fetchone()[0]==0:
            seeds=[
            ("Website Development","Web Development",75000,"Business websites, landing pages and eCommerce"),
            ("Mobile App Development","Mobile Apps",150000,"Android and iOS application development"),
            ("Power BI Dashboard","Data Analytics",45000,"Interactive BI dashboards and reporting"),
            ("Data Analysis","Data Analytics",30000,"SQL, Python, Excel analysis and insights"),
            ("QA Testing","Quality Assurance",20000,"Manual testing, automation, API and performance testing"),
            ("SEO","SEO",22000,"Technical SEO, on-page optimization and content strategy"),
            ("Digital Marketing","Digital Marketing",25000,"Social media, campaigns and performance marketing"),
            ("Data Science","Data Science",60000,"Data modeling, predictive analytics and machine learning solutions"),
            ("UI/UX Design","Design",35000,"User research, wireframes and interface design")]
            con.executemany("INSERT INTO services(name,category,price,description) VALUES(?,?,?,?)",seeds)
        if con.execute("SELECT COUNT(*) FROM settings").fetchone()[0]==0:
            con.execute("INSERT INTO settings(id,company_name,email,phone,address,currency,tax_rate,logo_url) VALUES(1,?,?,?,?,?,?,?)",
                ("Quebenix Technology","quebenixtechnology4@gmail.com","+92 300 0000000","Karachi, Pakistan","PKR",0,"static/quebenix-logo.jpg"))
        con.commit()
init_db()

def money(v):
    s=run("SELECT currency FROM settings WHERE id=1",fetch="one") or {}
    return f"{s.get('currency','PKR')} {float(v or 0):,.2f}"

def df(sql, params=()):
    rows=run(sql,params,fetch="all")
    return pd.DataFrame(rows) if rows else pd.DataFrame()

def login_screen():
    left,right=st.columns([1.2,1])
    with left:
        if os.path.exists("static/quebenix-logo.jpg"):
            st.image("static/quebenix-logo.jpg",width=180)
        st.markdown("# Quebenix Technology")
        st.markdown("### Service POS & Business Management")
        st.write("Manage clients, services, sales, invoices, projects, expenses and reports from one workspace.")
        st.markdown("<p class='small-muted'>Innovate · Develop · Grow</p>",unsafe_allow_html=True)
    with right:
        st.markdown("## Sign in")
        with st.form("login_form"):
            email=st.text_input("Email",placeholder="name@company.com")
            password=st.text_input("Password",type="password")
            ok=st.form_submit_button("Login",use_container_width=True)
        if ok:
            user=run("SELECT * FROM users WHERE lower(email)=lower(?) AND active=1",(email.strip(),), "one")
            if user and check_password_hash(user["password"],password):
                st.session_state.user={"id":user["id"],"name":user["name"],"email":user["email"],"role":user["role"]}
                st.rerun()
            else: st.error("Invalid email or password.")
        st.caption("Demo login: admin@quebenix.com / Admin@123")
        st.warning("Change the demo password before sharing this app publicly.")

def header(title,subtitle=""):
    st.title(title)
    if subtitle: st.caption(subtitle)

if "user" not in st.session_state:
    login_screen()
    st.stop()

user=st.session_state.user
settings=run("SELECT * FROM settings WHERE id=1",fetch="one") or {}
with st.sidebar:
    if os.path.exists("static/quebenix-logo.jpg"): st.image("static/quebenix-logo.jpg",width=145)
    st.markdown("## Quebenix POS")
    st.caption(f"{user['name']} · {user['role']}")
    pages=["Dashboard","POS / New Sale","Sales & Invoices","Clients","Services","Projects","Expenses","Reports","Change Password"]
    if user["role"]=="Admin": pages += ["Staff Management","Company Settings"]
    page=st.radio("NAVIGATION",pages,label_visibility="collapsed")
    st.divider()
    if st.button("Logout",use_container_width=True):
        st.session_state.pop("user",None); st.rerun()

currency=settings.get("currency","PKR")
if page=="Dashboard":
    header("Business Dashboard","Overview of Quebenix Technology operations")
    stats=[
      ("Revenue",run("SELECT COALESCE(SUM(total),0) v FROM sales WHERE status='Paid'",fetch="one")["v"]),
      ("Total Sales",run("SELECT COUNT(*) v FROM sales",fetch="one")["v"]),
      ("Clients",run("SELECT COUNT(*) v FROM clients",fetch="one")["v"]),
      ("Active Projects",run("SELECT COUNT(*) v FROM projects WHERE status NOT IN ('Completed','Cancelled')",fetch="one")["v"]),
      ("Expenses",run("SELECT COALESCE(SUM(amount),0) v FROM expenses",fetch="one")["v"])]
    cols=st.columns(5)
    for c,(label,value) in zip(cols,stats):
        c.metric(label,money(value) if label in ("Revenue","Expenses") else f"{int(value):,}")
    a,b=st.columns([1.15,1])
    with a:
        st.subheader("Monthly Revenue")
        monthly=df("SELECT substr(created_at,1,7) month,SUM(total) revenue FROM sales WHERE status='Paid' GROUP BY substr(created_at,1,7) ORDER BY month")
        if not monthly.empty: st.bar_chart(monthly.set_index("month")["revenue"])
        else: st.info("Sales revenue will appear here after your first checkout.")
    with b:
        st.subheader("Recent Sales")
        recent=df("SELECT s.invoice_no,s.created_at,c.name client,s.total,s.status FROM sales s LEFT JOIN clients c ON c.id=s.client_id ORDER BY s.id DESC LIMIT 8")
        if recent.empty: st.info("No sales recorded yet.")
        else: st.dataframe(recent,hide_index=True,use_container_width=True)

elif page=="Clients":
    header("Clients","Create and manage your customer records")
    with st.expander("＋ Add New Client",expanded=False):
        with st.form("client_add"):
            n=st.text_input("Client name *"); company=st.text_input("Company"); email=st.text_input("Email"); phone=st.text_input("Phone")
            address=st.text_area("Address"); notes=st.text_area("Notes")
            if st.form_submit_button("Save Client"):
                if n.strip():
                    run("INSERT INTO clients(name,company,email,phone,address,notes) VALUES(?,?,?,?,?,?)",(n,company,email,phone,address,notes)); st.success("Client added."); st.rerun()
                else: st.error("Client name is required.")
    clients=df("SELECT id,name,company,email,phone,address,notes,created_at FROM clients ORDER BY id DESC")
    st.dataframe(clients,hide_index=True,use_container_width=True)
    if not clients.empty:
        cid=st.selectbox("Select client to delete",clients.id.tolist(),format_func=lambda x:f"#{x} · {clients.loc[clients.id==x,'name'].iloc[0]}")
        if st.button("Delete selected client"):
            run("DELETE FROM clients WHERE id=?",(int(cid),)); st.success("Client deleted."); st.rerun()

elif page=="Services":
    header("Service Catalog","Manage the services available at checkout")
    with st.expander("＋ Add Service"):
        with st.form("service_add"):
            n=st.text_input("Service name *"); cat=st.text_input("Category"); price=st.number_input("Price",min_value=0.0,step=500.0); desc=st.text_area("Description")
            if st.form_submit_button("Save Service"):
                if n.strip():
                    run("INSERT INTO services(name,category,price,description) VALUES(?,?,?,?)",(n,cat,price,desc)); st.success("Service added."); st.rerun()
                else: st.error("Service name is required.")
    services=df("SELECT id,name,category,price,description,active FROM services ORDER BY category,name")
    st.dataframe(services,hide_index=True,use_container_width=True)
    active=services[services.active==1] if not services.empty else services
    if not active.empty:
        sid=st.selectbox("Archive service",active.id.tolist(),format_func=lambda x:f"#{x} · {active.loc[active.id==x,'name'].iloc[0]}")
        if st.button("Archive selected service"):
            run("UPDATE services SET active=0 WHERE id=?",(int(sid),)); st.rerun()

elif page=="POS / New Sale":
    header("Point of Sale","Select services, apply a discount and complete checkout")
    services=run("SELECT * FROM services WHERE active=1 ORDER BY category,name",fetch="all")
    clients=run("SELECT * FROM clients ORDER BY name",fetch="all")
    if not services: st.warning("Add an active service before creating a sale.")
    else:
        service_map={f"{s['name']} · {money(s['price'])}":s for s in services}
        with st.form("checkout"):
            client_options={"Walk-in Customer":None}
            client_options.update({f"{c['name']} ({c.get('company') or 'Individual'})":c["id"] for c in clients})
            client_label=st.selectbox("Client",list(client_options))
            chosen=st.multiselect("Services",list(service_map))
            quantities={}
            if chosen:
                qcols=st.columns(min(3,len(chosen)))
                for i,label in enumerate(chosen):
                    with qcols[i%len(qcols)]: quantities[label]=st.number_input(f"Qty · {service_map[label]['name']}",1,100,1,key=f"qty_{service_map[label]['id']}")
            discount=st.number_input("Discount (amount)",min_value=0.0,step=500.0)
            payment=st.selectbox("Payment method",["Cash","Bank Transfer","Card","JazzCash","EasyPaisa","Other"])
            status=st.selectbox("Payment status",["Paid","Pending","Partially Paid"])
            notes=st.text_area("Notes")
            submitted=st.form_submit_button("Complete Sale",use_container_width=True)
        if submitted:
            if not chosen: st.error("Select at least one service.")
            else:
                subtotal=sum(float(service_map[x]["price"])*quantities[x] for x in chosen)
                discount=min(discount,subtotal); tax_rate=float(settings.get("tax_rate") or 0); tax=(subtotal-discount)*tax_rate/100; total=subtotal-discount+tax
                invoice="QBX-"+datetime.now().strftime("%y%m%d")+"-"+uuid.uuid4().hex[:6].upper()
                sid=run("INSERT INTO sales(invoice_no,client_id,subtotal,discount,tax,total,payment_method,status,notes) VALUES(?,?,?,?,?,?,?,?,?)",
                    (invoice,client_options[client_label],subtotal,discount,tax,total,payment,status,notes))
                for label in chosen:
                    s=service_map[label]; qty=quantities[label]; line=qty*float(s["price"])
                    run("INSERT INTO sale_items(sale_id,service_id,description,qty,unit_price,line_total) VALUES(?,?,?,?,?,?)",(sid,s["id"],s["name"],qty,s["price"],line))
                st.session_state.last_invoice=sid
                st.success(f"Sale saved successfully · {invoice}")
                st.rerun()
    if st.session_state.get("last_invoice"):
        sid=st.session_state.last_invoice
        inv=run("SELECT * FROM sales WHERE id=?",(sid,),"one")
        if inv:
            st.subheader("Latest Invoice")
            st.write(f"**{inv['invoice_no']}** · {inv['created_at']} · {inv['status']}")
            st.metric("Invoice Total",money(inv["total"]))
            items=df("SELECT description,qty,unit_price,line_total FROM sale_items WHERE sale_id=?",(sid,))
            st.dataframe(items,hide_index=True,use_container_width=True)
            st.download_button("Download invoice CSV",items.to_csv(index=False).encode(),f"{inv['invoice_no']}.csv","text/csv")

elif page=="Sales & Invoices":
    header("Sales & Invoices","Review transactions and export sales records")
    sales=df("SELECT s.id,s.invoice_no,s.created_at,c.name client,s.subtotal,s.discount,s.tax,s.total,s.payment_method,s.status FROM sales s LEFT JOIN clients c ON c.id=s.client_id ORDER BY s.id DESC")
    st.dataframe(sales,hide_index=True,use_container_width=True)
    if not sales.empty:
        st.download_button("Export Sales CSV",sales.to_csv(index=False).encode("utf-8"),"quebenix-sales.csv","text/csv")
        sid=st.selectbox("View invoice",sales.id.tolist(),format_func=lambda x:sales.loc[sales.id==x,"invoice_no"].iloc[0])
        inv=run("SELECT s.*,c.name client,c.email,c.phone,c.address FROM sales s LEFT JOIN clients c ON c.id=s.client_id WHERE s.id=?",(int(sid),),"one")
        items=df("SELECT description,qty,unit_price,line_total FROM sale_items WHERE sale_id=?",(int(sid),))
        st.markdown(f"### Invoice {inv['invoice_no']}")
        st.write(f"Client: {inv.get('client') or 'Walk-in'} · Date: {inv['created_at']} · Payment: {inv['payment_method']} · Status: {inv['status']}")
        st.dataframe(items,hide_index=True,use_container_width=True)
        st.metric("Total",money(inv["total"]))
        invoice_csv=items.to_csv(index=False)+"\n"+f"Subtotal,{inv['subtotal']}\nDiscount,{inv['discount']}\nTax,{inv['tax']}\nTotal,{inv['total']}"
        st.download_button("Download Invoice CSV",invoice_csv.encode(),f"{inv['invoice_no']}.csv","text/csv")

elif page=="Projects":
    header("Projects","Track client work, delivery dates and budgets")
    clients=run("SELECT id,name FROM clients ORDER BY name",fetch="all")
    client_opts={"No linked client":None}; client_opts.update({c["name"]:c["id"] for c in clients})
    with st.expander("＋ Create Project"):
        with st.form("project_add"):
            title=st.text_input("Project title *"); service=st.text_input("Service"); client=st.selectbox("Client",list(client_opts))
            status=st.selectbox("Status",["Planning","In Progress","On Hold","Completed","Cancelled"])
            start=st.date_input("Start date",value=date.today()); due=st.date_input("Due date",value=date.today()); budget=st.number_input("Budget",min_value=0.0,step=1000.0); notes=st.text_area("Notes")
            if st.form_submit_button("Create Project"):
                if title.strip():
                    run("INSERT INTO projects(client_id,title,service,status,start_date,due_date,budget,notes) VALUES(?,?,?,?,?,?,?,?)",(client_opts[client],title,service,status,start.isoformat(),due.isoformat(),budget,notes)); st.success("Project created."); st.rerun()
                else: st.error("Project title is required.")
    projects=df("SELECT p.id,p.title,c.name client,p.service,p.status,p.start_date,p.due_date,p.budget,p.notes FROM projects p LEFT JOIN clients c ON c.id=p.client_id ORDER BY p.id DESC")
    st.dataframe(projects,hide_index=True,use_container_width=True)
    if not projects.empty:
        pid=st.selectbox("Update project status",projects.id.tolist(),format_func=lambda x:projects.loc[projects.id==x,"title"].iloc[0])
        new_status=st.selectbox("New status",["Planning","In Progress","On Hold","Completed","Cancelled"],key="project_status")
        if st.button("Update status"):
            run("UPDATE projects SET status=? WHERE id=?",(new_status,int(pid))); st.success("Status updated."); st.rerun()

elif page=="Expenses":
    header("Expenses","Record and monitor business expenses")
    with st.expander("＋ Record Expense"):
        with st.form("expense_add"):
            title=st.text_input("Expense title *"); cat=st.selectbox("Category",["Software","Marketing","Salaries","Operations","Travel","Office","Other"])
            amount=st.number_input("Amount",min_value=0.0,step=500.0); day=st.date_input("Expense date",value=date.today()); notes=st.text_area("Notes")
            if st.form_submit_button("Save Expense"):
                if title.strip():
                    run("INSERT INTO expenses(title,category,amount,expense_date,notes) VALUES(?,?,?,?,?)",(title,cat,amount,day.isoformat(),notes)); st.success("Expense saved."); st.rerun()
                else: st.error("Expense title is required.")
    expenses=df("SELECT * FROM expenses ORDER BY expense_date DESC")
    st.dataframe(expenses,hide_index=True,use_container_width=True)
    if not expenses.empty:
        st.metric("Total Expenses",money(expenses.amount.sum()))
        st.download_button("Export Expenses CSV",expenses.to_csv(index=False).encode(),"quebenix-expenses.csv","text/csv")

elif page=="Reports":
    header("Business Reports","Sales, revenue, discounts, tax and service performance")
    totals=run("SELECT COUNT(*) sales,COALESCE(SUM(total),0) revenue,COALESCE(SUM(discount),0) discounts,COALESCE(SUM(tax),0) tax FROM sales",(), "one")
    a,b,c,d=st.columns(4)
    a.metric("Sales",totals["sales"]); b.metric("Revenue",money(totals["revenue"])); c.metric("Discounts",money(totals["discounts"])); d.metric("Tax",money(totals["tax"]))
    by_service=df("SELECT description service,SUM(qty) quantity,SUM(line_total) revenue FROM sale_items GROUP BY description ORDER BY revenue DESC")
    st.subheader("Revenue by Service")
    if not by_service.empty:
        st.bar_chart(by_service.set_index("service")["revenue"])
        st.dataframe(by_service,hide_index=True,use_container_width=True)
    else: st.info("Service performance will appear after sales are recorded.")

elif page=="Staff Management" and user["role"]=="Admin":
    header("Staff Management","Create and activate staff accounts")
    with st.form("staff_add"):
        name=st.text_input("Full name"); email=st.text_input("Email"); password=st.text_input("Temporary password",type="password"); role=st.selectbox("Role",["Staff","Admin"])
        if st.form_submit_button("Create Account"):
            if name.strip() and email.strip() and len(password)>=8:
                try:
                    run("INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)",(name,email,generate_password_hash(password),role)); st.success("Account created."); st.rerun()
                except sqlite3.IntegrityError: st.error("This email already exists.")
            else: st.error("Enter name, email and a password of at least 8 characters.")
    staff=df("SELECT id,name,email,role,active,created_at FROM users ORDER BY id DESC")
    st.dataframe(staff,hide_index=True,use_container_width=True)
    if not staff.empty:
        uid=st.selectbox("Select staff account",staff.id.tolist(),format_func=lambda x:staff.loc[staff.id==x,"email"].iloc[0])
        if uid!=user["id"] and st.button("Toggle Active / Inactive"):
            run("UPDATE users SET active=CASE WHEN active=1 THEN 0 ELSE 1 END WHERE id=? AND role!='Admin'",(int(uid),)); st.rerun()

elif page=="Company Settings" and user["role"]=="Admin":
    header("Company Settings","Update company information and tax configuration")
    with st.form("settings"):
        name=st.text_input("Company name",settings.get("company_name") or "")
        email=st.text_input("Company email",settings.get("email") or "")
        phone=st.text_input("Phone",settings.get("phone") or "")
        address=st.text_area("Address",settings.get("address") or "")
        currency=st.selectbox("Currency",["PKR","USD","GBP","EUR","AED"],index=["PKR","USD","GBP","EUR","AED"].index(settings.get("currency","PKR")) if settings.get("currency","PKR") in ["PKR","USD","GBP","EUR","AED"] else 0)
        tax=st.number_input("Tax rate (%)",min_value=0.0,max_value=100.0,value=float(settings.get("tax_rate") or 0),step=0.5)
        if st.form_submit_button("Save Settings"):
            run("UPDATE settings SET company_name=?,email=?,phone=?,address=?,currency=?,tax_rate=? WHERE id=1",(name,email,phone,address,currency,tax)); st.success("Settings updated."); st.rerun()
else:
    st.error("You do not have permission to access this page.")
st.markdown("---")
st.caption("© Quebenix Technology · Innovate | Develop | Grow")
