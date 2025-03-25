from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# Initialize database
def init_db():
    conn = sqlite3.connect('tournament.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    player1 TEXT,
                    player2 TEXT,
                    player3 TEXT,
                    player4 TEXT,
                    player5 TEXT,
                    player6 TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS balances (
                    player TEXT PRIMARY KEY,
                    balance INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS debts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    debtor TEXT,
                    creditor TEXT,
                    amount INTEGER)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    players = [request.form[f'player{i}'] for i in range(1, 7)]
    date = request.form['date']

    conn = sqlite3.connect('tournament.db')
    c = conn.cursor()
    c.execute("INSERT INTO results (date, player1, player2, player3, player4, player5, player6) VALUES (?, ?, ?, ?, ?, ?, ?)", 
              (date, *players))

    transactions = [
        (players[5], players[0], 300),  # 6th pays 1st
        (players[4], players[1], 200),  # 5th pays 2nd
        (players[3], players[2], 100)   # 4th pays 3rd
    ]

    for debtor, creditor, amount in transactions:
        c.execute("INSERT INTO debts (date, debtor, creditor, amount) VALUES (?, ?, ?, ?)",
                  (date, debtor, creditor, amount))
        c.execute("INSERT INTO balances (player, balance) VALUES (?, ?) ON CONFLICT(player) DO UPDATE SET balance = balance - ?",
                  (debtor, -amount, amount))
        c.execute("INSERT INTO balances (player, balance) VALUES (?, ?) ON CONFLICT(player) DO UPDATE SET balance = balance + ?",
                  (creditor, amount, amount))

    conn.commit()
    conn.close()
    return redirect(url_for('balances'))

@app.route('/balances')
def balances():
    conn = sqlite3.connect('tournament.db')
    c = conn.cursor()

    c.execute("SELECT * FROM balances")
    balances = c.fetchall()

    c.execute("SELECT debtor, creditor, SUM(amount) FROM debts GROUP BY debtor, creditor")
    debts = c.fetchall()

    conn.close()
    return render_template('balances.html', balances=balances, debts=debts)

# Route to clear all transactions
@app.route('/reset', methods=['POST'])
def reset():
    conn = sqlite3.connect('tournament.db')
    c = conn.cursor()
    c.execute("DELETE FROM results")
    c.execute("DELETE FROM balances")
    c.execute("DELETE FROM debts")
    conn.commit()
    conn.close()
    return redirect(url_for('balances'))

if __name__ == '__main__':
    app.run(debug=True)

