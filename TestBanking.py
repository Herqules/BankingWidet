import requests
import sqlite3
import csv
import os
import calendar
import sys
import subprocess
from prettytable import PrettyTable
from getpass import getpass
from datetime import datetime
import time
from tabulate import tabulate
import keyboard
#import BillGenerator

ALPHA_VANTAGE_API_KEY = "YOUR API KEY HERE"
# GUI testing 
# Functions for GUI
def logout():
    global user
    user = None
    print("Logged out successfully.")

# Database setup
conn = sqlite3.connect('banking.db')
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    balance REAL DEFAULT 0
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    amount REAL,
    type TEXT,
    timestamp DATETIME,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
""")
conn.commit()

cursor.execute("""
CREATE TABLE IF NOT EXISTS savings_goals (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    goal_name TEXT NOT NULL,
    target_amount REAL NOT NULL,
    current_amount REAL DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users (id)
)
""")


# Functions
def transfer(user_id, receiver_username, amount):
    cursor.execute("SELECT balance FROM users WHERE id = ?", (user_id,))
    sender_balance = cursor.fetchone()[0]

    if amount > sender_balance:
        print("Insufficient balance.")
        return

    cursor.execute("SELECT id, balance FROM users WHERE username = ?", (receiver_username,))
    receiver_data = cursor.fetchone()
    
    if not receiver_data:
        print("Receiver not found.")
        return

    receiver_id, receiver_balance = receiver_data

    cursor.execute("UPDATE users SET balance = balance - ? WHERE id = ?", (amount, user_id))
    cursor.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amount, receiver_id))
    cursor.execute("INSERT INTO transactions (user_id, amount, type, timestamp) VALUES (?, ?, 'transfer out', ?)", (user_id, amount, datetime.now()))
    cursor.execute("INSERT INTO transactions (user_id, amount, type, timestamp) VALUES (?, ?, 'transfer in', ?)", (receiver_id, amount, datetime.now()))
    conn.commit()
    print(f"Successfully transferred ${amount:.2f} to {receiver_username}")
    save_all_transactions_to_csv()

def search_user_by_username(search_username):
    cursor.execute("SELECT id, username, balance FROM users WHERE username LIKE ?", (f"%{search_username}%",))
    search_results = cursor.fetchall()

    if not search_results:
        print("No users found with that username.")
        return

    table = PrettyTable()
    table.field_names = ["User ID", "Username", "Balance"]

    for search_result in search_results:
        user_id, username, balance = search_result
        table.add_row([user_id, username, f"${balance:.2f}"])

    print(table)

def display_all_data():
    cursor.execute("SELECT * FROM users")
    users_data = cursor.fetchall()

    if not users_data:
        print("No user data found.")
        return

    users_table = PrettyTable()
    users_table.field_names = ["User ID", "Username", "Password", "Balance"]

    for user_data in users_data:
        user_id, username, password, balance = user_data
        users_table.add_row([user_id, username, password, f"${balance:.2f}"])

    print("All Users Data:")
    print(users_table)

    transactions_data = get_all_transactions()

    if not transactions_data:
        print("No transactions found.")
        return

    transactions_table = PrettyTable()
    transactions_table.field_names = ["Transaction ID", "User ID", "Amount", "Type", "Timestamp"]

    for transaction_data in transactions_data:
        transaction_id, user_id, amount, trans_type, timestamp = transaction_data.values()
        transactions_table.add_row([transaction_id, user_id, f"${amount:.2f}", trans_type, timestamp])

    print("All Transactions Data:")
    print(transactions_table)

def save_transactions_to_csv(transactions):
    desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
    csvfile_path = os.path.join(desktop, 'SQLtransactions.csv')

    with open(csvfile_path, 'w', newline='') as csvfile:
        fieldnames = ['id', 'user_id', 'amount', 'type', 'timestamp']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for transaction in transactions:
            writer.writerow(transaction)

def get_all_transactions():
    cursor.execute("SELECT * FROM transactions")
    transactions = cursor.fetchall()

    transactions_list = []
    for transaction in transactions:
        id, user_id, amount, trans_type, timestamp = transaction
        transactions_list.append({
            'id': id,
            'user_id': user_id,
            'amount': amount,
            'type': trans_type,
            'timestamp': timestamp
        })

    return transactions_list

# Add this function to save transactions to CSV after any transaction
def save_all_transactions_to_csv():
    transactions = get_all_transactions()
    save_transactions_to_csv(transactions)

# Function to clear sqltransactions.csv when needed 
def clear_sql_transactions_file():
    # Open the file in write mode with the 'truncate' option to clear the contents
    if os.path.exists("sqltransactions.csv"):
        # Clear the file contents
        with open("sqltransactions.csv", "w") as f:
            f.write("")
        print("Successfully cleared sqltransactions.csv file.")
    else:
        print("sqltransactions.csv file does not exist.")

# Reflect changes in PrettyTable 
def clear_tables():
    cursor.execute("DELETE FROM users")
    cursor.execute("DELETE FROM transactions")
    conn.commit()
    print("Successfully cleared users and transactions tables.")


# Other functions are the same as before (register, login, deposit, withdraw, view_balance, view_transactions, get_stock_info)
def register(username, password):
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        print("User registered successfully.")
    except sqlite3.IntegrityError:
        print("Username is already taken.")

def login(username, password):
    cursor.execute("SELECT id, username, password, balance FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    if user:
        return user
    else:
        print("Invalid username or password.")

def deposit(user_id, amount):
    cursor.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amount, user_id))
    cursor.execute("INSERT INTO transactions (user_id, amount, type, timestamp) VALUES (?, ?, 'deposit', ?)", (user_id, amount, datetime.now()))
    conn.commit()
    print(f"Successfully deposited ${amount:.2f}")
    save_all_transactions_to_csv()

####################################### Admin Privledges #######################################
def get_all_users():
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    return users

def get_transact():
    cursor.execute("SELECT * FROM transactions")
    transactions = cursor.fetchall()
    return transactions

def generate_balance_report(users):
    username_index = 1  # Assuming the username is stored at index 1 in the user tuple
    balance_index = 3   # Assuming the balance is stored at index 3 in the user tuple
    data = [(user[username_index], user[balance_index]) for user in users]
    headers = ["Username", "Balance"]
    print(tabulate(data, headers=headers, tablefmt="grid"))

def top_users(users, n=10, highest=True):
    balance_index = 3  # Assuming the balance is stored at index 3 in the user tuple
    sorted_users = sorted(users, key=lambda user: user[balance_index], reverse=highest)
    top_n_users = sorted_users[:n]

    username_index = 1  # Assuming the username is stored at index 1 in the user tuple
    data = [(user[username_index], user[balance_index]) for user in top_n_users]
    headers = ["Username", "Balance"]
    print(tabulate(data, headers=headers, tablefmt="grid"))

def delete_user(user_id):
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    cursor.execute("DELETE FROM transactions WHERE user_id = ?", (user_id,))
    conn.commit()
    print(f"User with ID {user_id} has been deleted.")

def delete_transaction(transaction_id):
    cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
    conn.commit()
    print(f"Transaction with ID {transaction_id} has been deleted.")

def open_sql_csvfile():
    desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
    csvfile_path = os.path.join(desktop, 'SQLtransactions.csv')

    if sys.platform.startswith('darwin'):  # For macOS
        subprocess.run(('open', csvfile_path))
    elif os.name == 'posix':  # For Linux
        subprocess.run(('xdg-open', csvfile_path))
    else:
        print("Unsupported platform.")

def export_transactions_to_csv():
    cursor.execute("SELECT * FROM transactions")
    transactions = cursor.fetchall()

def add_money_to_account(user_id, amount):
    cursor.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amount, user_id))
    cursor.execute("INSERT INTO transactions (user_id, amount, type, timestamp) VALUES (?, ?, 'deposit', ?)", (user_id, amount, datetime.now()))
    conn.commit()
    print(f"Successfully deposited ${amount:.2f}")
    save_all_transactions_to_csv()

    
    # Fetch usernames for each user ID
    usernames = {}
    for transaction in transaction:
        user_id = transaction[1]
        if user_id not in usernames:
            cursor.execute("SELECT username FROM users WHERE id=?", (user_id,))
            username = cursor.fetchone()[0]
            usernames[user_id] = username

    desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
    csvfile_path = os.path.join(desktop, 'SQLtransactions.csv')

    with open(csvfile_path, mode='w', newline='') as csvfile:
        fieldnames = ["ID", "User ID", "Username", "Amount", "Type", "Timestamp"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for transaction in transaction:
            writer.writerow({"ID": transaction[0], "User ID": transaction[1], "Username": usernames[transaction[1]], "Amount": transaction[2], "Type": transaction[3], "Timestamp": transaction[4]})


def master_password_prompt():
    MASTER_PASSWORD = "MasterPass"
    clear_terminal()

    entered_password = getpass("Enter the master password: ")
    clear_terminal()
    if entered_password == MASTER_PASSWORD:
        while True:
            print("\nMaster options:")
            print("1. View all users")
            print("2. View all transactions")
            print("3. Delete a user")
            print("4. Delete a transaction")
            print("5. Generate balance report")
            print("6. View top users")
            print("7. Open CSV file ")
            print("8. Add money to account")
            print("9. Exit master mode")

            try:
                master_action = int(input("What would you like to do? "))
            except ValueError:
                print("Invalid option.")
                continue

            if master_action == 1:
                users = get_all_users()
                print(tabulate(users, headers=["ID", "Username", "Password", "Balance"], tablefmt="grid"))
            elif master_action == 2:
                transactions = get_transact()
                print(tabulate(transactions, headers=["ID", "User ID", "Amount", "Type", "Timestamp"], tablefmt="grid"))
            elif master_action == 3:
                user_id = int(input("Enter the user ID to delete: "))
                delete_user(user_id)
            elif master_action == 4:
                transaction_id = int(input("Enter the transaction ID to delete: "))
                delete_transaction(transaction_id)
            elif master_action == 5:
                users = get_all_users()
                generate_balance_report(users)
            elif master_action == 6:
                users = get_all_users()
                top_users(users)
            elif master_action == 7:
                export_transactions_to_csv()
                open_sql_csvfile()
            elif master_action == 8:
                user_id = int(input("Enter the user ID to add money to: "))
                amount = float(input("Enter the amount to add: "))
                add_money_to_account(user_id, amount)
            elif master_action == 9:
                clear_terminal(1)
                break
            else:
                print("Invalid option.")
                clear_terminal(1)
    else:
        print("Invalid master password.")
        clear_terminal(1)


####################################### End of Admin Privledges #######################################


def display_calendar():
    today = datetime.today()
    month, year = today.month, today.year

    while True:
        os.system("clear" if os.name == "posix" else "cls")
        print(calendar.month(year, month))

        # Code to print real time live clock under calendar
        now = datetime.now()
        print(now.strftime("%I:%M:%S %p"))

        print("\nPress 'n' for next month, 'p' for previous month, 'q' to quit.")
        action = input(">").lower()
        

        if action == 'n':
            if month == 12:
                month = 1
                year += 1
            else:
                month += 1
        elif action == 'p':
            if month == 1:
                month = 12
                year -= 1
            else:
                month -= 1
        elif action == 'q':
            clear_terminal(1)
            break
    today = datetime.today()
    month, year = today.month, today.year
    action = None


def withdraw(user_id, amount):
    cursor.execute("SELECT balance FROM users WHERE id = ?", (user_id,))
    balance = cursor.fetchone()[0]

    if amount > balance:
        print("Insufficient balance.")
        return

    cursor.execute("UPDATE users SET balance = balance - ? WHERE id = ?", (amount, user_id))
    cursor.execute("INSERT INTO transactions (user_id, amount, type, timestamp) VALUES (?, ?, 'withdrawal', ?)", (user_id, amount, datetime.now()))
    conn.commit()
    print(f"Successfully withdrew ${amount:.2f}")
    save_all_transactions_to_csv()

def view_balance(user_id):
    cursor.execute("SELECT balance FROM users WHERE id = ?", (user_id,))
    balance = cursor.fetchone()[0]
    print(f"Your current balance is: ${balance:.2f}")

def view_transactions(user_id):
    cursor.execute("SELECT amount, type, timestamp FROM transactions WHERE user_id = ? ORDER BY timestamp DESC", (user_id,))
    transactions = cursor.fetchall()

    if not transactions:
        print("No transactions found.")
        return

    table = PrettyTable()
    table.field_names = ["Amount", "Type", "Timestamp"]

    for transaction in transactions:
        amount, trans_type, timestamp = transaction
        table.add_row([f"${amount:.2f}", trans_type, timestamp])

    print(table)



conn = sqlite3.connect('banking.db')
cursor = conn.cursor()

def add_savings_goal(user_id, goal_name, target_amount):
    cursor.execute("INSERT INTO savings_goals (user_id, goal_name, target_amount, current_amount) VALUES (?, ?, ?, 0)",
                   (user_id, goal_name, target_amount))
    conn.commit()
    print("Savings goal added successfully!")

def view_savings_goals(user_id):
    cursor.execute("SELECT * FROM savings_goals WHERE user_id = ?", (user_id,))
    goals = cursor.fetchall()
    headers = ["ID", "Goal Name", "Target Amount", "Current Amount"]
    print(tabulate(goals, headers=headers, tablefmt="grid"))

def update_savings_goal(goal_id, amount):
    cursor.execute("UPDATE savings_goals SET current_amount = current_amount + ? WHERE id = ?", (amount, goal_id))
    conn.commit()
    print("Savings goal updated successfully!")

def savings_goal_menu(user_id):
    clear_terminal()
    while True:
        print("\nSavings, Goals, and Planner:")
        print("1. Add a savings goal")
        print("2. View savings goals")
        print("3. Update a savings goal")
        print("4. Exit savings goal menu")

        try:
            choice = int(input("What would you like to do? "))
        except ValueError:
            print("Invalid option. Please enter a number.")
            continue

        if choice == 1:
            goal_name = input("Enter the name of your savings goal: ")
            try:
                target_amount = float(input("Enter the target amount for your savings goal: "))
            except ValueError:
                print("Invalid amount. Please enter a valid number.")
                continue
            add_savings_goal(user_id, goal_name, target_amount)
        elif choice == 2:
            view_savings_goals(user_id)
        elif choice == 3:
            try:
                goal_id = int(input("Enter the ID of the savings goal you'd like to update: "))
                amount = float(input("Enter the amount you'd like to add to this savings goal: "))
            except ValueError:
                print("Invalid input. Please enter a valid number.")
                continue
            update_savings_goal(goal_id, amount)
        elif choice == 4:
            break
        else:
            clear_terminal(1)
            print("Invalid option. Please choose a valid option.")


def special_purchase(user_id, amount):
    cursor.execute("SELECT balance FROM users WHERE id = ?", (user_id,))
    balance = cursor.fetchone()[0]

    if amount > balance:
        print("Insufficient balance.")
        clear_terminal(1)
        return

    cursor.execute("UPDATE users SET balance = balance - ? WHERE id = ?", (amount, user_id))
    cursor.execute("INSERT INTO transactions (user_id, amount, type, timestamp) VALUES (?, ?, 'special purchase', ?)", (user_id, amount, datetime.now()))
    conn.commit()
    print(f"You are financially able to make that purchase of ${amount:.2f}")
    save_all_transactions_to_csv()

def budget_plan():
    print("Welcome to the Budget Plan Calculator!")
    print("This program will help you calculate your budget for the month.")
    print("Please enter your monthly income and expenses below...")

    income = float(input("Enter your monthly income: "))
    rent = float(input("Enter your rent: "))
    food = float(input("Enter your food expenses: "))
    utilities = float(input("Enter your utilities: "))
    transportation = float(input("Enter your transportation expenses: "))
    other = float(input("Enter your other expenses: "))

    total_expenses = rent + food + utilities + transportation + other
    savings = income - total_expenses
    savings_percent = (savings / income) * 100

    print(f"Total Expenses: ${total_expenses:.2f}")
    print(f"Savings: ${savings:.2f}")
    print(f"Savings Percent: {savings_percent:.2f}%")

    if savings_percent < 20:
        print("You should save more!")
    elif savings_percent > 50:
        print("You're doing great!")
    else:
        print("You're on the right track!")
    
def get_stock_info(symbol):
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={ALPHA_VANTAGE_API_KEY}"
    response = requests.get(url)
    data = response.json()

    if "Error Message" in data:
        print("Invalid symbol.")
        return

    stock_data = data.get("Global Quote", {})
    if not stock_data:
        print("Stock data not available.")
        return

    table = PrettyTable()
    table.field_names = ["Symbol", "Open", "High", "Low", "Price", "Volume", "Latest Trading Day", "Previous Close", "Change", "Change Percent"]

    symbol = stock_data["01. symbol"]
    open_price = stock_data["02. open"]
    high_price = stock_data["03. high"]
    low_price = stock_data["04. low"]
    price = stock_data["05. price"]
    volume = stock_data["06. volume"]
    latest_trading_day = stock_data["07. latest trading day"]
    prev_close = stock_data["08. previous close"]
    change = stock_data["09. change"]
    change_percent = stock_data["10. change percent"]

    table.add_row([symbol, open_price, high_price, low_price, price, volume, latest_trading_day, prev_close, change, change_percent])

    print(table)

def clear_terminal(delay=0):
    if delay:
        time.sleep(delay)
    os.system("cls" if os.name == "nt" else "clear")

    

# Main loop
user = None
clear_terminal()

while True:
    print("\nOptions:")
    print("1. Register an account")
    print("2. Login")
    print("3. Deposit")
    print("4. Withdraw")
    print("5. View balance")
    print("6. See transactions")
    print("7. Check a stock")
    print("8. Check your budget")
    print("9. Make an unplanned purchase")
    print("10. Logout")
    print("11. Clear all data")
    print("12. Transfer Funds")
    print("13. Display Calendar")
    print("14. Savings, Goals, and Planner")
    print("15. Exit")
    print("16. Bill Generator")

    try:
        action = int(input("What would you like to do? "))
    except ValueError:
        print("Invalid option.")
        clear_terminal(2)
        continue

    if action in [3, 4, 5, 6, 9]:
        if not user:
            print("Please login first.")
            clear_terminal(1)
            continue

    if action == 1:
        username = input("Enter a username: ")
        password = getpass("Enter a password: ")
        register(username, password)
        clear_terminal(2)
    elif action == 2:
        username = input("Enter your username: ")
        password = getpass("Enter your password: ")
        user = login(username, password)
        if user:
            print(f"Welcome, {user[1]}!")
        clear_terminal(2)
    elif action == 3:
        amount = float(input("Enter the amount you want to deposit: "))
        deposit(user[0], amount)
        clear_terminal(2)
    elif action == 4:
        amount = float(input("Enter the amount you want to withdraw: "))
        withdraw(user[0], amount)
        clear_terminal(3)
    elif action == 5:
        view_balance(user[0])
        print("Press any key to continue...")
        keyboard.read_key()
        clear_terminal(1)
    elif action == 6:
        view_transactions(user[0])
        print("Press any key to continue...")
        keyboard.read_key()
        clear_terminal(1)
    elif action == 7:
        symbol = input("Enter the stock symbol: ")
        get_stock_info(symbol)
        print("Press any key to continue...")
        keyboard.read_key()
        clear_terminal(1)
    elif action == 8:
        budget_plan()
    elif action == 9:
        amount = float(input("Enter the amount you want to spend: "))
        special_purchase(user[0], amount)
        print("Press any key to continue...")
        keyboard.read_key()
        clear_terminal(1)
    elif action == 10:
        if not user:
            print("You are not logged in!")
            clear_terminal(2)
        else:
            user = None
            print("Logged out successfully.")
            clear_terminal(2)
    elif action == 11:
        clear_sql_transactions_file()
        clear_tables()
        print("Successfully cleared all data.")
        clear_terminal(2)
    elif action == 1911:  # You can choose any number that doesn't conflict with existing options
        master_password_prompt()
        print("Obfuscating your actions.")
        print("Goodbye.")
        clear_terminal(2)
    elif action == 12:
        receiver_username = input("Enter the receiver's username: ")
        amount = float(input("Enter the amount you want to transfer: "))
        transfer(user[0], receiver_username, amount)
        print("Press any key to continue...")
        keyboard.read_key()
        clear_terminal(1)
    elif action == 13:
        display_calendar()
    elif action == 14:
        user_id = 1
        savings_goal_menu(user_id)
    elif action == 15:
        break
    elif action == 16:
        BillGenerator()
    else:
        print("Invalid option.")
        
