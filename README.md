# Computer-Based Digital Receipt & Invoice Printing System (Flask)

A ready-to-run Flask project for managing transactions, printing branded PDF receipts, exporting records, and viewing quick sales stats.

## Features
- Add transactions (customer, items/what they did, amount).
- Auto-generated Invoice Numbers (INV-0001, INV-0002, ...).
- Printable PDF receipts with your **computer logo** (place `static/computer.png`).
- Transaction list with **search** and **date filters**.
- Export **CSV** and **Excel (.xlsx)**.
- Dashboard with **Total Sales, Today’s Sales, This Month’s Sales, Total Customers**, and **Recent Transactions**.

## Setup (PyCharm or Terminal)
1. Create a virtual environment (recommended).
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the app:
   ```bash
   python app.py
   ```
4. Open http://127.0.0.1:5000 in your browser.

## Notes
- The SQLite database (`database.db`) is created automatically on first run.
- To show a logo on receipts, add your image at `static/computer.png`.
- Business info on the receipt can be edited in `app.py` inside the `/receipt` route.
