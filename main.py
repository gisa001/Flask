from flask import Flask, render_template, request, redirect, url_for, flash, make_response, session
import json
import uuid
import os
import csv
from io import StringIO

app = Flask(__name__)
DATA_FILE = 'data.json'

def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

@app.route('/')
def index():
    transactions = load_data()
    
    # Calculate statistics
    total_income = sum(txn['amount'] for txn in transactions if txn['type'] == 'Income')
    total_expenses = sum(txn['amount'] for txn in transactions if txn['type'] == 'Expense')
    
    # Sort transactions by date (most recent first)
    transactions.sort(key=lambda x: x['date'], reverse=True)
    
    return render_template('index.html', 
                         transactions=transactions,
                         total_income=total_income,
                         total_expenses=total_expenses)

@app.route('/home')
def home():
    return redirect(url_for('index'))

@app.route('/add', methods=['GET', 'POST'])
def add_transaction():
    if request.method == 'POST':
        new_txn = {
            'id': str(uuid.uuid4()),
            'date': request.form['date'],
            'description': request.form['description'],
            'amount': float(request.form['amount']),
            'type': request.form['type']
        }
        data = load_data()
        data.append(new_txn)
        save_data(data)
        flash("Transaction added successfully!", "success")
        return redirect(url_for('index'))
    return render_template('add.html')

app.secret_key = 'capable-secret'

@app.route('/edit/<txn_id>', methods=['GET', 'POST'])
def edit_transaction(txn_id):
    data = load_data()
    transaction = next((t for t in data if t['id'] == txn_id), None)

    if not transaction:
        flash("Transaction not found!", "danger")
        return redirect(url_for('index'))

    if request.method == 'POST':
        transaction['date'] = request.form['date']
        transaction['description'] = request.form['description']
        transaction['amount'] = float(request.form['amount'])
        transaction['type'] = request.form['type']
        save_data(data)
        flash("Transaction updated!", "success")
        return redirect(url_for('index'))

    return render_template('edit.html', txn=transaction)

@app.route('/delete/<txn_id>')
def delete_transaction(txn_id):
    data = load_data()
    new_data = [t for t in data if t['id'] != txn_id]
    save_data(new_data)
    flash("Transaction deleted!", "warning")
    return redirect(url_for('index'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/export-csv')
def export_csv():
    transactions = load_data()
    
    # Create CSV content
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Date', 'Description', 'Amount', 'Type'])
    
    # Write transactions
    for txn in transactions:
        writer.writerow([txn['date'], txn['description'], txn['amount'], txn['type']])
    
    # Create response
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=transactions.csv'
    
    return response

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Simple demo login - in production, use proper authentication
        username = request.form['username']
        password = request.form['password']
        
        # Demo credentials
        if username == 'admin' and password == 'password':
            session['user'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials!', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/reports')
def reports():
    transactions = load_data()
    
    # Monthly reports
    monthly_reports = {}
    for txn in transactions:
        month = txn['date'][:7]  # YYYY-MM
        if month not in monthly_reports:
            monthly_reports[month] = {'income': 0, 'expenses': 0, 'transactions': []}
        
        if txn['type'] == 'Income':
            monthly_reports[month]['income'] += txn['amount']
        else:
            monthly_reports[month]['expenses'] += txn['amount']
        
        monthly_reports[month]['transactions'].append(txn)
    
    return render_template('reports.html', monthly_reports=monthly_reports)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
