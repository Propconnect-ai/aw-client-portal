from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify
import sqlite3
import json
import datetime
import io
import os
from pdf_generator import generate_sacs_pdf, generate_tcc_pdf

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), 'database', 'portal.db')

# ─── DATABASE ────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            c1_name TEXT, c1_dob TEXT, c1_ssn TEXT,
            c2_name TEXT, c2_dob TEXT, c2_ssn TEXT,
            monthly_inflow REAL DEFAULT 0,
            monthly_outflow REAL DEFAULT 0,
            insurance_deductibles REAL DEFAULT 0,
            private_reserve_balance REAL DEFAULT 0,
            schwab_investment_balance REAL DEFAULT 0,
            last_report_date TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            account_type TEXT NOT NULL,
            owner TEXT,
            account_name TEXT NOT NULL,
            last_four TEXT,
            balance REAL DEFAULT 0,
            cash_balance REAL DEFAULT 0,
            interest_rate TEXT,
            property_address TEXT,
            sort_order INTEGER DEFAULT 0,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        );

        CREATE TABLE IF NOT EXISTS report_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            report_date TEXT NOT NULL,
            data_snapshot TEXT NOT NULL,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        );
    ''')
    conn.commit()

    # Seed demo client if empty
    cur = conn.execute("SELECT COUNT(*) FROM clients")
    if cur.fetchone()[0] == 0:
        conn.execute('''
            INSERT INTO clients (name, c1_name, c1_dob, c1_ssn, c2_name, c2_dob, c2_ssn,
                monthly_inflow, monthly_outflow, insurance_deductibles, private_reserve_balance,
                schwab_investment_balance, last_report_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('Andrew & Rebecca Smith', 'Andrew Smith', '1975-06-15', '4321',
              'Rebecca Smith', '1978-03-22', '8765',
              15000, 11000, 5000, 42000, 187500, '2026-01-15'))
        client_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        accounts = [
            (client_id, 'retirement', 'client1', 'Schwab Traditional IRA', '1234', 11162.47, 316.00, None, None, 1),
            (client_id, 'retirement', 'client1', 'Schwab Roth IRA', '5678', 15000.00, 0, None, None, 2),
            (client_id, 'retirement', 'client2', 'Employer 401(k)', '9012', 45000.00, 0, None, None, 1),
            (client_id, 'retirement', 'client2', 'Roth IRA', '3344', 12000.00, 0, None, None, 2),
            (client_id, 'retirement', 'client2', 'Pension Plan', '7788', 8500.00, 0, None, None, 3),
            (client_id, 'non_retirement', 'joint', 'Schwab Brokerage (Joint)', '3456', 50000.00, 2100.00, None, None, 1),
            (client_id, 'non_retirement', 'joint', 'Pinnacle Checking (Inflow)', '1111', 15000.00, 0, None, None, 2),
            (client_id, 'non_retirement', 'joint', 'Pinnacle Spending (Outflow)', '2222', 11000.00, 0, None, None, 3),
            (client_id, 'trust', 'joint', 'Primary Residence', None, 450000.00, 0, None, '123 Financial Peace Way, Atlanta, GA 30301', 1),
            (client_id, 'liability', 'joint', 'Primary Mortgage', None, 200000.00, 0, '4.5%', None, 1),
            (client_id, 'liability', 'joint', 'Auto Loan', None, 18500.00, 0, '6.2%', None, 2),
        ]
        conn.executemany('''
            INSERT INTO accounts (client_id, account_type, owner, account_name, last_four,
                balance, cash_balance, interest_rate, property_address, sort_order)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', accounts)
        conn.commit()
    conn.close()

def get_client_full(client_id):
    conn = get_db()
    client = conn.execute("SELECT * FROM clients WHERE id=?", (client_id,)).fetchone()
    accounts = conn.execute(
        "SELECT * FROM accounts WHERE client_id=? ORDER BY account_type, sort_order",
        (client_id,)
    ).fetchall()
    conn.close()
    if not client:
        return None, []
    return dict(client), [dict(a) for a in accounts]

def calculate_totals(client, accounts):
    c1_ret = sum(a['balance'] for a in accounts if a['account_type'] == 'retirement' and a['owner'] == 'client1')
    c2_ret = sum(a['balance'] for a in accounts if a['account_type'] == 'retirement' and a['owner'] == 'client2')
    non_ret = sum(a['balance'] for a in accounts if a['account_type'] == 'non_retirement')
    trust = sum(a['balance'] for a in accounts if a['account_type'] == 'trust')
    liabilities = sum(a['balance'] for a in accounts if a['account_type'] == 'liability')
    net_worth = c1_ret + c2_ret + non_ret + trust
    excess = client['monthly_inflow'] - client['monthly_outflow']
    reserve_target = (6 * client['monthly_outflow']) + client['insurance_deductibles']
    return {
        'c1_retirement': c1_ret,
        'c2_retirement': c2_ret,
        'non_retirement': non_ret,
        'trust': trust,
        'liabilities': liabilities,
        'net_worth': net_worth,
        'excess': excess,
        'reserve_target': reserve_target
    }

def calc_age(dob_str):
    if not dob_str:
        return ''
    try:
        birth_year = int(dob_str.split('-')[0])
        return datetime.date.today().year - birth_year
    except:
        return ''

# ─── ROUTES ──────────────────────────────────────────────────────────────────

@app.route('/')
def dashboard():
    conn = get_db()
    clients = conn.execute("SELECT * FROM clients ORDER BY name").fetchall()
    conn.close()
    return render_template('dashboard.html', clients=[dict(c) for c in clients])

@app.route('/client/new', methods=['GET', 'POST'])
def new_client():
    if request.method == 'POST':
        conn = get_db()
        conn.execute('''
            INSERT INTO clients (name, c1_name, c1_dob, c1_ssn, c2_name, c2_dob, c2_ssn,
                monthly_inflow, monthly_outflow, insurance_deductibles)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0, 0)
        ''', (
            request.form['name'],
            request.form['c1_name'], request.form['c1_dob'], request.form['c1_ssn'],
            request.form.get('c2_name', ''), request.form.get('c2_dob', ''), request.form.get('c2_ssn', '')
        ))
        new_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.commit()
        conn.close()
        return redirect(url_for('client_profile', client_id=new_id))
    return render_template('new_client.html')

@app.route('/client/<int:client_id>')
def client_profile(client_id):
    client, accounts = get_client_full(client_id)
    if not client:
        return redirect(url_for('dashboard'))
    totals = calculate_totals(client, accounts)
    return render_template('client_profile.html',
        client=client, accounts=accounts, totals=totals,
        age1=calc_age(client.get('c1_dob')),
        age2=calc_age(client.get('c2_dob')),
        ret_c1=[a for a in accounts if a['account_type']=='retirement' and a['owner']=='client1'],
        ret_c2=[a for a in accounts if a['account_type']=='retirement' and a['owner']=='client2'],
        non_ret=[a for a in accounts if a['account_type']=='non_retirement'],
        trust=[a for a in accounts if a['account_type']=='trust'],
        liabilities=[a for a in accounts if a['account_type']=='liability'],
    )

@app.route('/client/<int:client_id>/add-account', methods=['POST'])
def add_account(client_id):
    conn = get_db()
    conn.execute('''
        INSERT INTO accounts (client_id, account_type, owner, account_name, last_four,
            balance, cash_balance, interest_rate, property_address, sort_order)
        VALUES (?, ?, ?, ?, ?, 0, 0, ?, ?, 99)
    ''', (
        client_id,
        request.form['account_type'],
        request.form.get('owner', 'joint'),
        request.form['account_name'],
        request.form.get('last_four', ''),
        request.form.get('interest_rate', ''),
        request.form.get('property_address', '')
    ))
    conn.commit()
    conn.close()
    return redirect(url_for('client_profile', client_id=client_id))

@app.route('/client/<int:client_id>/delete-account/<int:account_id>', methods=['POST'])
def delete_account(client_id, account_id):
    conn = get_db()
    conn.execute("DELETE FROM accounts WHERE id=? AND client_id=?", (account_id, client_id))
    conn.commit()
    conn.close()
    return redirect(url_for('client_profile', client_id=client_id))

@app.route('/client/<int:client_id>/entry', methods=['GET', 'POST'])
def entry_form(client_id):
    client, accounts = get_client_full(client_id)
    if not client:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        conn = get_db()
        # Update client-level fields
        conn.execute('''
            UPDATE clients SET monthly_inflow=?, monthly_outflow=?,
            insurance_deductibles=?, private_reserve_balance=?,
            schwab_investment_balance=?, last_report_date=?
            WHERE id=?
        ''', (
            float(request.form.get('monthly_inflow', 0)),
            float(request.form.get('monthly_outflow', 0)),
            float(request.form.get('insurance_deductibles', 0)),
            float(request.form.get('private_reserve_balance', 0)),
            float(request.form.get('schwab_investment_balance', 0)),
            datetime.date.today().isoformat(),
            client_id
        ))
        # Update each account balance
        for acc in accounts:
            balance_key = f"balance_{acc['id']}"
            cash_key = f"cash_{acc['id']}"
            if balance_key in request.form:
                conn.execute(
                    "UPDATE accounts SET balance=?, cash_balance=? WHERE id=?",
                    (
                        float(request.form.get(balance_key, 0)),
                        float(request.form.get(cash_key, 0) or 0),
                        acc['id']
                    )
                )
        conn.commit()

        # Save report snapshot
        client_updated, accounts_updated = get_client_full(client_id)
        totals = calculate_totals(client_updated, accounts_updated)
        snapshot = json.dumps({'client': client_updated, 'accounts': accounts_updated, 'totals': totals})
        conn.execute(
            "INSERT INTO report_history (client_id, report_date, data_snapshot) VALUES (?, ?, ?)",
            (client_id, datetime.date.today().isoformat(), snapshot)
        )
        conn.commit()
        conn.close()
        return redirect(url_for('report_view', client_id=client_id))

    totals = calculate_totals(client, accounts)
    return render_template('entry_form.html',
        client=client, accounts=accounts, totals=totals,
        age1=calc_age(client.get('c1_dob')),
        age2=calc_age(client.get('c2_dob')),
        ret_c1=[a for a in accounts if a['account_type']=='retirement' and a['owner']=='client1'],
        ret_c2=[a for a in accounts if a['account_type']=='retirement' and a['owner']=='client2'],
        non_ret=[a for a in accounts if a['account_type']=='non_retirement'],
        trust=[a for a in accounts if a['account_type']=='trust'],
        liabilities=[a for a in accounts if a['account_type']=='liability'],
    )

@app.route('/client/<int:client_id>/report')
def report_view(client_id):
    client, accounts = get_client_full(client_id)
    if not client:
        return redirect(url_for('dashboard'))
    totals = calculate_totals(client, accounts)
    return render_template('report_view.html',
        client=client, accounts=accounts, totals=totals,
        age1=calc_age(client.get('c1_dob')),
        age2=calc_age(client.get('c2_dob')),
        ret_c1=[a for a in accounts if a['account_type']=='retirement' and a['owner']=='client1'],
        ret_c2=[a for a in accounts if a['account_type']=='retirement' and a['owner']=='client2'],
        non_ret=[a for a in accounts if a['account_type']=='non_retirement'],
        trust=[a for a in accounts if a['account_type']=='trust'],
        liabilities=[a for a in accounts if a['account_type']=='liability'],
        today=datetime.date.today().strftime('%B %d, %Y')
    )

@app.route('/client/<int:client_id>/pdf/sacs')
def download_sacs(client_id):
    client, accounts = get_client_full(client_id)
    totals = calculate_totals(client, accounts)
    pdf_bytes = generate_sacs_pdf(client, totals)
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"SACS_{client['name'].replace(' ','_')}_{datetime.date.today()}.pdf"
    )

@app.route('/client/<int:client_id>/pdf/tcc')
def download_tcc(client_id):
    client, accounts = get_client_full(client_id)
    totals = calculate_totals(client, accounts)
    ret_c1 = [a for a in accounts if a['account_type']=='retirement' and a['owner']=='client1']
    ret_c2 = [a for a in accounts if a['account_type']=='retirement' and a['owner']=='client2']
    non_ret = [a for a in accounts if a['account_type']=='non_retirement']
    trust = [a for a in accounts if a['account_type']=='trust']
    liabilities = [a for a in accounts if a['account_type']=='liability']
    pdf_bytes = generate_tcc_pdf(client, accounts, totals, ret_c1, ret_c2, non_ret, trust, liabilities)
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"TCC_{client['name'].replace(' ','_')}_{datetime.date.today()}.pdf"
    )

@app.route('/client/<int:client_id>/history')
def report_history(client_id):
    client, _ = get_client_full(client_id)
    conn = get_db()
    history = conn.execute(
        "SELECT id, report_date FROM report_history WHERE client_id=? ORDER BY report_date DESC",
        (client_id,)
    ).fetchall()
    conn.close()
    return render_template('history.html', client=client, history=[dict(h) for h in history])

@app.route('/api/calc', methods=['POST'])
def api_calc():
    data = request.json
    inflow = float(data.get('inflow', 0))
    outflow = float(data.get('outflow', 0))
    deductibles = float(data.get('deductibles', 0))
    excess = inflow - outflow
    reserve_target = (6 * outflow) + deductibles
    return jsonify({'excess': excess, 'reserve_target': reserve_target})

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
