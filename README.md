# 🚆 Railway Management System

A Python + MySQL based Railway Management System that simulates real-world train booking operations.

---

## 📌 Features

- View available trains
- Book tickets with automatic seat allocation
- Cancel tickets with seat restoration
- Track train location
- View system reports (bookings, cancellations, seats)

---

## 🛠️ Tech Stack

- Python
- MySQL
- SQL
- Git & GitHub

---

## 📂 Project Structure

- main.py → Main menu system
- modules/ → Core logic (booking, cancellation, etc.)
- database/ → DB connection & SQL scripts
- html/ → UI templates (optional)
- css/ → Styling files (optional)

---

## ⚙️ How to Run

1. Install MySQL and create database `railway_db`
2. Import tables from `database/railway.sql`
3. Update MySQL password in `db_connection.py`
4. Run:

```bash
python main.py