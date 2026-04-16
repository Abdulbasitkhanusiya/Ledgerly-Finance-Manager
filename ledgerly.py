#!/usr/bin/env python
# coding: utf-8

# In[1]:


#Connect MySQL
import mysql.connector
mydb=mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password=""
)
mycursor=mydb.cursor()   


# In[2]:


#Create Database
mycursor.execute("Create database if not Exists ledgerly_db")
print("Database Created")


# In[3]:


#Connect Database ledgerly_db
mydb=mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="",
    database="ledgerly_db"
)
mycursor=mydb.cursor()


# In[4]:


#Create Transactions Table
mycursor.execute("Create table if exists transactions(id INT AUTO_INCREMENT PRIMARY KEY,type VARCHAR(20),title VARCHAR(50),amount DECIMAL(10,2),category VARCHAR(30),date DATE)")
print("transactions Table Created")


# In[5]:


import mysql.connector
from tkinter import *
from tkinter import messagebox
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# ================= APP =================
root = Tk()
root.title("Ledgerly")
root.geometry("1000x750")
root.config(bg="#F8FAFC")

selected_id = None
current_page = "Dashboard"

# ================= HELPERS =================
def format_date(date_text):
    """Convert DD-MM-YYYY to YYYY-MM-DD for MySQL"""
    try:
        return datetime.strptime(date_text, "%d-%m-%Y").strftime("%Y-%m-%d")
    except ValueError:
        raise ValueError("Date must be in DD-MM-YYYY format")


def clear_right_frame():
    for widget in right_frame.winfo_children():
        widget.destroy()


def clear_form():
    title_entry.delete(0, END)
    amount_entry.delete(0, END)
    category_entry.delete(0, END)
    date_entry.delete(0, END)


def load_transactions(trans_type):
    listbox.delete(0, END)
    mycursor.execute("SELECT * FROM transactions WHERE type=%s", (trans_type,))
    for row in mycursor.fetchall():
        listbox.insert(END, row)


def select_transaction(event):
    global selected_id
    if not listbox.curselection():
        return

    row = listbox.get(listbox.curselection())
    selected_id = row[0]

    title_entry.delete(0, END)
    amount_entry.delete(0, END)
    category_entry.delete(0, END)
    date_entry.delete(0, END)

    title_entry.insert(0, row[2])
    amount_entry.insert(0, row[3])
    category_entry.insert(0, row[4])

    # Handle both MySQL DATE object and string date values
    if isinstance(row[5], str):
        try:
            formatted_date = datetime.strptime(row[5], "%Y-%m-%d").strftime("%d-%m-%Y")
        except ValueError:
            formatted_date = row[5]
    else:
        formatted_date = row[5].strftime("%d-%m-%Y")

    date_entry.insert(0, formatted_date)


# ================= CRUD =================
def save_transaction(trans_type):
    try:
        db_date = format_date(date_entry.get())
    except ValueError as e:
        messagebox.showerror("Date Error", str(e))
        return

    mycursor.execute(
        "INSERT INTO transactions(type,title,amount,category,date) VALUES(%s,%s,%s,%s,%s)",
        (trans_type, title_entry.get(), amount_entry.get(), category_entry.get(), db_date)
    )
    mydb.commit()
    load_transactions(trans_type)
    dashboard_page(refresh_only=True)
    clear_form()
    messagebox.showinfo("Success", f"{trans_type.title()} added")


def update_transaction(trans_type):
    global selected_id
    if not selected_id:
        messagebox.showwarning("Select", "Please select a record")
        return

    try:
        db_date = format_date(date_entry.get())
    except ValueError as e:
        messagebox.showerror("Date Error", str(e))
        return

    mycursor.execute(
        "UPDATE transactions SET title=%s, amount=%s, category=%s, date=%s WHERE id=%s",
        (title_entry.get(), amount_entry.get(), category_entry.get(), db_date, selected_id)
    )
    mydb.commit()
    load_transactions(trans_type)
    dashboard_page(refresh_only=True)
    clear_form()
    selected_id = None
    messagebox.showinfo("Updated", "Transaction updated")


def delete_transaction(trans_type):
    global selected_id
    if not selected_id:
        messagebox.showwarning("Select", "Please select a record")
        return

    mycursor.execute("DELETE FROM transactions WHERE id=%s", (selected_id,))
    mydb.commit()
    load_transactions(trans_type)
    dashboard_page(refresh_only=True)
    clear_form()
    selected_id = None
    messagebox.showinfo("Deleted", "Transaction deleted")

def export_invoice_pdf():
    global selected_id
    if not selected_id:
        messagebox.showwarning("Select", "Please select a transaction")
        return

    mycursor.execute("SELECT * FROM transactions WHERE id=%s", (selected_id,))
    row = mycursor.fetchone()

    pdf = SimpleDocTemplate(f"invoice_{selected_id}.pdf")
    elements = []

    styles = getSampleStyleSheet()
    elements.append(Paragraph("Ledgerly Invoice", styles["Title"]))
    elements.append(Spacer(1, 10))

    invoice_data = [
        ["Invoice ID", row[0]],
        ["Type", row[1]],
        ["Title", row[2]],
        ["Amount", row[3]],
        ["Category", row[4]],
        ["Date", str(row[5])]
    ]

    table = Table(invoice_data)
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 1, colors.black)
    ]))

    elements.append(table)
    pdf.build(elements)

    messagebox.showinfo("Success", f"Invoice invoice_{selected_id}.pdf created")

# ================= PAGES =================
def transaction_page(trans_type):
    global title_entry, amount_entry, category_entry, date_entry, listbox, current_page
    current_page = trans_type
    clear_right_frame()

    Label(right_frame, text=f"{trans_type} Management", font=("Arial", 20, "bold"),
          bg="#F8FAFC", fg="#1E3A8A").pack(pady=10)

    form = Frame(right_frame, bg="white", bd=1, relief="solid")
    form.pack(pady=10, padx=20, fill=X)

    Label(form, text="Title", bg="white").grid(row=0, column=0, padx=10, pady=8)
    title_entry = Entry(form, width=25)
    title_entry.grid(row=0, column=1)

    Label(form, text="Amount", bg="white").grid(row=1, column=0, padx=10, pady=8)
    amount_entry = Entry(form, width=25)
    amount_entry.grid(row=1, column=1)

    Label(form, text="Category", bg="white").grid(row=2, column=0, padx=10, pady=8)
    category_entry = Entry(form, width=25)
    category_entry.grid(row=2, column=1)

    Label(form, text="Date (DD-MM-YYYY)", bg="white").grid(row=3, column=0, padx=10, pady=8)
    date_entry = Entry(form, width=25)
    date_entry.grid(row=3, column=1)

    btn_frame = Frame(form, bg="white")
    btn_frame.grid(row=4, column=0, columnspan=2, pady=10)

    Button(btn_frame, text=f"Add {trans_type}", bg="#16A34A" if trans_type == "Income" else "#DC2626",
           fg="white", width=15, command=lambda: save_transaction(trans_type.lower())).pack(side=LEFT, padx=5)
    Button(btn_frame, text="Update", bg="#2563EB", fg="white", width=15,
           command=lambda: update_transaction(trans_type.lower())).pack(side=LEFT, padx=5)
    Button(btn_frame, text="Delete", bg="#334155", fg="white", width=15,
           command=lambda: delete_transaction(trans_type.lower())).pack(side=LEFT, padx=5)
    Button(
    btn_frame,
    text="Export Invoice",
    bg="#7C3AED",
    fg="white",
    width=15,
    command=export_invoice_pdf
).pack(side=LEFT, padx=5)

    listbox = Listbox(right_frame, width=100, height=15)
    listbox.pack(padx=20, pady=10)
    listbox.bind("<<ListboxSelect>>", select_transaction)

    load_transactions(trans_type.lower())


def dashboard_page(refresh_only=False):
    global current_page
    if refresh_only and current_page != "Dashboard":
        return

    current_page = "Dashboard"
    clear_right_frame()

    # Total Income
    mycursor.execute("SELECT SUM(amount) FROM transactions WHERE type='income'")
    total_income = float(mycursor.fetchone()[0] or 0)

    # Total Expense
    mycursor.execute("SELECT SUM(amount) FROM transactions WHERE type='expense'")
    total_expense = float(mycursor.fetchone()[0] or 0)

    # Balance
    balance = total_income - total_expense

    # Dashboard Title
    Label(
        right_frame,
        text="Ledgerly Dashboard",
        font=("Arial", 22, "bold"),
        bg="#F8FAFC",
        fg="#1E3A8A"
    ).pack(pady=20)

    # Summary Cards
    card_frame = Frame(right_frame, bg="#F8FAFC")
    card_frame.pack(pady=10)

    for text, value, color in [
        ("Total Income", total_income, "green"),
        ("Total Expense", total_expense, "red"),
        ("Balance", balance, "blue")
    ]:
        card = Frame(card_frame, bg="white", bd=1, relief="solid")
        card.pack(side=LEFT, padx=20)

        Label(
            card,
            text=text,
            font=("Arial", 14, "bold"),
            bg="white"
        ).pack(padx=30, pady=10)

        Label(
            card,
            text=f"₹ {value}",
            font=("Arial", 16),
            fg=color,
            bg="white"
        ).pack(pady=10)

        # Chart + Recent Transactions in one row
    bottom_frame = Frame(right_frame, bg="#F8FAFC")
    bottom_frame.pack(pady=20)

    # Pie Chart Left
    chart_frame = Frame(bottom_frame, bg="#F8FAFC")
    chart_frame.pack(side=LEFT, padx=30)

    fig, ax = plt.subplots(figsize=(3, 3))

    values = [total_income, total_expense]
    labels = ["Income", "Expense"]

    ax.pie(values, labels=labels, autopct="%1.1f%%")
    ax.set_title("Income vs Expense")

    chart = FigureCanvasTkAgg(fig, master=chart_frame)
    chart.draw()
    chart.get_tk_widget().pack()

    # Recent Transactions Right
    recent_frame = Frame(bottom_frame, bg="#F8FAFC")
    recent_frame.pack(side=LEFT, padx=30)

    Label(
        recent_frame,
        text="Recent Transactions",
        font=("Arial", 16, "bold"),
        bg="#F8FAFC"
    ).pack(pady=10)

    recent_box = Listbox(recent_frame, width=45, height=10)
    recent_box.pack()

    mycursor.execute(
        "SELECT type, title, amount FROM transactions ORDER BY id DESC LIMIT 5"
    )

    for row in mycursor.fetchall():
        recent_box.insert(END, row)

def export_report_pdf():
    mycursor.execute("SELECT * FROM transactions ORDER BY id DESC")
    rows = mycursor.fetchall()

    pdf = SimpleDocTemplate("ledgerly_report.pdf")
    elements = []

    styles = getSampleStyleSheet()
    elements.append(Paragraph("Ledgerly Financial Report", styles["Title"]))
    elements.append(Spacer(1, 10))

    data = [["ID", "Type", "Title", "Amount", "Category", "Date"]]
    for row in rows:
        data.append(list(row))

    table = Table(data)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 1, colors.black)
    ]))

    elements.append(table)
    pdf.build(elements)

    messagebox.showinfo("Success", "PDF exported successfully")


def search_transactions():
    keyword = search_entry.get()

    report_box.delete(0, END)

    query = """
    SELECT * FROM transactions
    WHERE title LIKE %s
       OR category LIKE %s
       OR type LIKE %s
    ORDER BY id DESC
    """

    search_value = f"%{keyword}%"

    mycursor.execute(query, (search_value, search_value, search_value))

    for row in mycursor.fetchall():
        report_box.insert(END, row)

def reports_page():
    global report_box, search_entry

    clear_right_frame()

    Label(
        right_frame,
        text="All Transactions",
        font=("Arial", 20, "bold"),
        bg="#F8FAFC",
        fg="#1E3A8A"
    ).pack(pady=20)

    search_entry = Entry(right_frame, width=40)
    search_entry.pack(pady=5)

    Button(
        right_frame,
        text="Search",
        bg="#2563EB",
        fg="white",
        width=15,
        command=search_transactions
    ).pack(pady=5)

    Button(
        right_frame,
        text="Export PDF",
        bg="#16A34A",
        fg="white",
        width=15,
        command=export_report_pdf
    ).pack(pady=5)

    report_box = Listbox(right_frame, width=110, height=18)
    report_box.pack(pady=10)

    mycursor.execute("SELECT * FROM transactions ORDER BY id DESC")
    for row in mycursor.fetchall():
        report_box.insert(END, row)

# ================= UI LAYOUT =================
left_frame = Frame(root, bg="#0F172A", width=220)
left_frame.pack(side=LEFT, fill=Y)

right_frame = Frame(root, bg="#F8FAFC")
right_frame.pack(side=RIGHT, fill=BOTH, expand=True)

Button(left_frame, text="Dashboard", width=20, pady=10,
       bg="#1E40AF", fg="white",
       command=dashboard_page).pack(pady=20)

Button(left_frame, text="Income", width=20, pady=10,
       bg="#16A34A", fg="white",
       command=lambda: transaction_page("Income")).pack(pady=10)

Button(left_frame, text="Expense", width=20, pady=10,
       bg="#DC2626", fg="white",
       command=lambda: transaction_page("Expense")).pack(pady=10)

Button(left_frame, text="Reports", width=20, pady=10,
       bg="#334155", fg="white",
       command=reports_page).pack(pady=10)

# Default page
dashboard_page()

root.mainloop()


# In[6]:


import os
print(os.getcwd())


# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:




