from flask import Flask, render_template, request, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_, func
from datetime import datetime, date
from reportlab.pdfgen import canvas
import os
import pandas as pd

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# -----------------------------
# Database Model
# -----------------------------
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_no = db.Column(db.String(20), unique=True)
    customer_name = db.Column(db.String(100))
    items = db.Column(db.String(500))
    amount = db.Column(db.Float)
    date = db.Column(db.DateTime, default=datetime.utcnow)

def generate_invoice_no():
    last = Transaction.query.order_by(Transaction.id.desc()).first()
    if not last:
        return "INV-0001"
    return f"INV-{last.id + 1:04d}"

# -----------------------------
# Routes
# -----------------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    total_sales = db.session.query(func.sum(Transaction.amount)).scalar() or 0
    today = date.today()
    today_sales = db.session.query(func.sum(Transaction.amount)).filter(
        func.date(Transaction.date) == today
    ).scalar() or 0
    now = datetime.now()
    month_sales = db.session.query(func.sum(Transaction.amount)).filter(
        func.extract('month', Transaction.date) == now.month,
        func.extract('year', Transaction.date) == now.year
    ).scalar() or 0
    total_customers = db.session.query(func.count(func.distinct(Transaction.customer_name))).scalar() or 0
    recent_transactions = Transaction.query.order_by(Transaction.date.desc()).limit(5).all()

    return render_template('dashboard.html',
                           total_sales=total_sales,
                           today_sales=today_sales,
                           month_sales=month_sales,
                           total_customers=total_customers,
                           recent_transactions=recent_transactions)

@app.route('/add', methods=['GET', 'POST'])
def add_transaction():
    if request.method == 'POST':
        customer = request.form['customer'].strip()
        items = request.form['items'].strip()
        amount = float(request.form['amount'])
        invoice_no = generate_invoice_no()
        t = Transaction(invoice_no=invoice_no, customer_name=customer, items=items, amount=amount)
        db.session.add(t)
        db.session.commit()
        return redirect(url_for('transactions'))
    return render_template('add_transaction.html')

@app.route('/transactions')
def transactions():
    query = request.args.get('q')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    q = Transaction.query

    if query:
        like = f"%{query}%"
        q = q.filter(or_(Transaction.invoice_no.ilike(like),
                         Transaction.customer_name.ilike(like),
                         Transaction.items.ilike(like)))

    if start_date and end_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            # include whole end day
            end = end.replace(hour=23, minute=59, second=59)
            q = q.filter(Transaction.date.between(start, end))
        except ValueError:
            pass

    all_transactions = q.order_by(Transaction.date.desc()).all()
    return render_template('transactions.html',
                           transactions=all_transactions,
                           query=query,
                           start_date=start_date,
                           end_date=end_date)

@app.route('/receipt/<int:transaction_id>')
def receipt(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    filename = f"receipt_{transaction.id}.pdf"
    filepath = os.path.join("static", filename)

    c = canvas.Canvas(filepath, pagesize=(400, 600))

    # Logo (computer.png if present)
    logo_path = os.path.join("static", "computer.png")
    if os.path.exists(logo_path):
        c.drawImage(logo_path, 30, 530, width=60, height=60, preserveAspectRatio=True)

    # Business Info (edit to your details)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(110, 570, "My Business Name Ltd.")
    c.setFont("Helvetica", 10)
    c.drawString(110, 555, "123 Business Street, Lagos, Nigeria")
    c.drawString(110, 540, "Phone: +234 XXX XXX XXXX | Email: info@business.com")

    # Divider
    c.line(20, 520, 380, 520)

    # Invoice Details
    c.setFont("Helvetica-Bold", 14)
    c.drawString(140, 500, "INVOICE / RECEIPT")

    c.setFont("Helvetica", 12)
    c.drawString(30, 470, f"Invoice No: {transaction.invoice_no}")
    c.drawString(30, 450, f"Customer: {transaction.customer_name}")
    c.drawString(30, 430, f"Items: {transaction.items}")
    c.drawString(30, 410, f"Amount: ₦{transaction.amount}")
    c.drawString(30, 390, f"Date: {transaction.date.strftime('%Y-%m-%d %H:%M:%S')}")

    # Divider
    c.line(20, 370, 380, 370)

    # Footer
    c.setFont("Helvetica-Oblique", 11)
    c.drawString(110, 350, "Thank you for your business!")
    c.drawString(80, 335, "Powered by Digital Receipt & Invoice System")

    c.save()
    return send_file(filepath, as_attachment=True)

# -------- Exports --------
@app.route('/export/csv')
def export_csv():
    transactions = Transaction.query.order_by(Transaction.date.desc()).all()
    data = [{
        "Invoice No": t.invoice_no,
        "Customer": t.customer_name,
        "Items": t.items,
        "Amount": t.amount,
        "Date": t.date.strftime('%Y-%m-%d %H:%M')
    } for t in transactions]
    df = pd.DataFrame(data)
    path = os.path.join("static", "transactions.csv")
    df.to_csv(path, index=False, encoding="utf-8-sig")
    return send_file(path, as_attachment=True)

@app.route('/export/excel')
def export_excel():
    transactions = Transaction.query.order_by(Transaction.date.desc()).all()
    data = [{
        "Invoice No": t.invoice_no,
        "Customer": t.customer_name,
        "Items": t.items,
        "Amount": t.amount,
        "Date": t.date.strftime('%Y-%m-%d %H:%M')
    } for t in transactions]
    df = pd.DataFrame(data)
    path = os.path.join("static", "transactions.xlsx")
    df.to_excel(path, index=False, engine="openpyxl")
    return send_file(path, as_attachment=True)

# -----------------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
