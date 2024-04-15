import tkinter as tk
from tkinter import simpledialog, messagebox, Toplevel, Label, Entry, Button
import sqlite3
import calendar
from datetime import datetime

# Database setup
conn = sqlite3.connect('simple_banking.db')
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
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
""")
conn.commit()

class BankingApp:
    def __init__(self, root):
        self.root = root
        self.current_user_id = None
        self.root.title("Banking App")
        self.root.geometry("400x600")
        self.main_menu()

    def clear_frame(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def main_menu(self):
        self.clear_frame()
        tk.Button(self.root, text="Register", command=self.register_user, bg="lightblue").pack(fill=tk.X)
        tk.Button(self.root, text="Login", command=self.login_user, bg="lightgreen").pack(fill=tk.X)
        tk.Button(self.root, text="Admin Login", command=self.admin_login, bg="orange").pack(fill=tk.X)
        tk.Button(self.root, text="Display Calendar", command=self.display_calendar, bg="lightgrey").pack(fill=tk.X)
        tk.Button(self.root, text="Exit", command=self.root.quit, bg="lightcoral").pack(fill=tk.X)

    def display_calendar(self):
        calendar_window = Toplevel(self.root)
        calendar_window.title("Calendar")

        self.calendar_year = datetime.now().year
        self.calendar_month = datetime.now().month
        self.calendar_label = Label(calendar_window)
        self.calendar_label.pack(pady=10)
        
        Button(calendar_window, text="Previous", command=lambda: self.change_month(-1)).pack(side=tk.LEFT)
        Button(calendar_window, text="Next", command=lambda: self.change_month(1)).pack(side=tk.RIGHT)
        self.update_calendar()


    def update_calendar(self):
        cal_text = calendar.month(self.calendar_year, self.calendar_month)
        self.calendar_label.config(text=cal_text)

    def change_month(self, delta):
        self.calendar_month += delta
        if self.calendar_month > 12:
            self.calendar_month = 1
            self.calendar_year += 1
        elif self.calendar_month < 1:
            self.calendar_month = 12
            self.calendar_year -= 1
        self.update_calendar()

    def admin_login(self):
        self.clear_frame()

        tk.Label(self.root, text="Admin Username:").pack()
        username = tk.Entry(self.root)
        username.pack()
        tk.Label(self.root, text="Admin Password:").pack()
        password = tk.Entry(self.root, show="*")
        password.pack()
        login_button = tk.Button(self.root, text="Login", command=lambda: self.login(username.get(), password.get(), admin=True), bg="lightgrey")
        login_button.pack()
        self.root.bind('<Return>', lambda event=None: login_button.invoke())
        tk.Button(self.root, text="Back", command=self.main_menu, bg="lightyellow").pack()

    def register_user(self):
        self.clear_frame()

        tk.Label(self.root, text="Username:").pack()
        username = tk.Entry(self.root)
        username.pack()
        tk.Label(self.root, text="Password:").pack()
        password = tk.Entry(self.root, show="*")
        password.pack()
        tk.Button(self.root, text="Register", command=lambda: self.register(username.get(), password.get()), bg="lightgreen").pack()
        tk.Button(self.root, text="Back", command=self.main_menu, bg="lightyellow").pack()

    def login_user(self):
        self.clear_frame()

        tk.Label(self.root, text="Username:").pack()
        username = tk.Entry(self.root)
        username.pack()
        tk.Label(self.root, text="Password:").pack()
        password = tk.Entry(self.root, show="*")
        password.pack()
        login_button = tk.Button(self.root, text="Login", command=lambda: self.login(username.get(), password.get()), bg="lightgreen")
        login_button.pack()
        self.root.bind('<Return>', lambda event=None: login_button.invoke())
        tk.Button(self.root, text="Back", command=self.main_menu, bg="lightyellow").pack()

    def user_dashboard(self, admin=False):
        self.clear_frame()
        if not admin:
            tk.Button(self.root, text="View Balance", command=self.view_balance, bg="lightblue").pack(fill=tk.X)
            tk.Button(self.root, text="Deposit", command=self.deposit, bg="lightgreen").pack(fill=tk.X)
            tk.Button(self.root, text="Withdraw", command=self.withdraw, bg="orange").pack(fill=tk.X)
            tk.Button(self.root, text="Logout", command=self.logout, bg="red").pack(fill=tk.X)
        else:
            tk.Button(self.root, text="View All User Data", command=self.view_all_user_data, bg="violet").pack(fill=tk.X)
            tk.Button(self.root, text="View All Balances", command=self.view_all_balances, bg="lightblue").pack(fill=tk.X)
            tk.Button(self.root, text="View All Transactions", command=self.view_all_transactions, bg="lightgreen").pack(fill=tk.X)
            tk.Button(self.root, text="Logout", command=self.logout, bg="red").pack(fill=tk.X)

    def register(self, username, password):
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            messagebox.showinfo("Success", "Registration successful")
            self.main_menu()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Username already taken")

    def login(self, username, password, admin=False):
        if admin and username == "admin" and password == "adminpass":
            self.user_dashboard(admin=True)
        else:
            cursor.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, password))
            user = cursor.fetchone()
            if user:
                self.current_user_id = user[0]
                self.user_dashboard()
            else:
                messagebox.showerror("Error", "Invalid username or password")

    def logout(self):
        self.current_user_id = None
        self.main_menu()

    def view_balance(self):
        cursor.execute("SELECT balance FROM users WHERE id = ?", (self.current_user_id,))
        balance = cursor.fetchone()[0]
        messagebox.showinfo("Balance", f"Your balance is ${balance:.2f}")

    def deposit(self):
        amount = simpledialog.askfloat("Deposit", "Amount:")
        if amount:
            cursor.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amount, self.current_user_id))
            cursor.execute("INSERT INTO transactions (user_id, amount, type) VALUES (?, ?, 'deposit')", (self.current_user_id, amount))
            conn.commit()
            messagebox.showinfo("Success", f"Deposited ${amount:.2f}")

    def withdraw(self):
        amount = simpledialog.askfloat("Withdraw", "Amount:")
        cursor.execute("SELECT balance FROM users WHERE id = ?", (self.current_user_id,))
        balance = cursor.fetchone()[0]
        if amount and amount <= balance:
            cursor.execute("UPDATE users SET balance = balance - ? WHERE id = ?", (amount, self.current_user_id))
            cursor.execute("INSERT INTO transactions (user_id, amount, type) VALUES (?, ?, 'withdraw')", (self.current_user_id, amount))
            conn.commit()
            messagebox.showinfo("Success", f"Withdrew ${amount:.2f}")
        else:
            messagebox.showerror("Error", "Insufficient funds")

    def view_all_balances(self):
        self.clear_frame()
        cursor.execute("SELECT username, balance FROM users")
        for user in cursor.fetchall():
            Label(self.root, text=f"Username: {user[0]}, Balance: ${user[1]:.2f}").pack()
        Button(self.root, text="Back", command=lambda: self.user_dashboard(admin=True), bg="skyblue").pack()

    def view_all_transactions(self):
        self.clear_frame()
        cursor.execute("SELECT users.username, transactions.amount, transactions.type FROM transactions JOIN users ON users.id = transactions.user_id")
        for transaction in cursor.fetchall():
            Label(self.root, text=f"User: {transaction[0]}, Amount: ${transaction[1]:.2f}, Type: {transaction[2]}").pack()
        Button(self.root, text="Back", command=lambda: self.user_dashboard(admin=True), bg="skyblue").pack()

    def view_all_user_data(self):
        self.clear_frame()
        cursor.execute("SELECT id, username, password, balance FROM users")
        Label(self.root, text="ID | Username | Password | Balance", font=('Arial', 12, 'bold'), fg="blue").pack()
        for user in cursor.fetchall():
            Label(self.root, text=f"{user[0]} | {user[1]} | {user[2]} | ${user[3]:.2f}", bg="lightgray").pack(fill=tk.X)
        Button(self.root, text="Back", command=lambda: self.user_dashboard(admin=True), bg="skyblue").pack()
        
    # New function for displaying the calendar
    def display_calendar(self):
        new_win = Toplevel(self.root) # create new window
        new_win.title("Calendar")
        
        # Add calendar
        cal = calendar.TextCalendar(calendar.SUNDAY)
        cal_str = cal.formatmonth(datetime.now().year, datetime.now().month)
        cal_label = Label(new_win, text=cal_str, justify=tk.LEFT, font=("Courier", 10), padx=10, pady=10)
        cal_label.pack()

        # Add button to close the calendar window
        close_btn = Button(new_win, text="Close", command=new_win.destroy)
        close_btn.pack(pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    app = BankingApp(root)
    root.mainloop()
