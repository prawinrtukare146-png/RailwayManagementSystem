from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse
import mysql.connector
import os

PORT = 8000


# ---------------- DATABASE ----------------
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="REMOVED_SECRET",   # change if needed
        database="railway_db"
    )


# ---------------- SERVER ----------------
class Handler(BaseHTTPRequestHandler):

    # ================= GET =================
    def do_GET(self):
        try:
            if self.path == "/" or self.path == "/index.html":
                self.render_template("index.html")

            elif self.path == "/dashboard":
                self.dashboard()

            elif self.path == "/trains":
                self.trains()

            elif self.path == "/bookings":
                self.bookings()

            elif self.path == "/cancel.html":
                self.render_template("cancel.html")

            else:
                self.render_template(self.path.lstrip("/"))

        except Exception as e:
            self.send_error(500, str(e))


    # ================= POST =================
    def do_POST(self):
        try:
            length = int(self.headers['Content-Length'])
            data = self.rfile.read(length).decode()
            form = urllib.parse.parse_qs(data)

            # -------- BOOK --------
            if self.path == "/book":
                name = form['name'][0]
                train_id = form['train_id'][0]

                conn = get_connection()
                cur = conn.cursor()

                cur.execute("SELECT available_seats FROM trains WHERE train_id=%s", (train_id,))
                result = cur.fetchone()

                if not result:
                    self.respond("Train Not Found")
                    return

                seats = result[0]

                if seats <= 0:
                    self.respond("No Seats Available")
                    return

                seat_no = seats

                cur.execute(
                    "INSERT INTO bookings (passenger_name, train_id, seat_number, status) VALUES (%s,%s,%s,'BOOKED')",
                    (name, train_id, seat_no)
                )

                cur.execute(
                    "UPDATE trains SET available_seats = available_seats - 1 WHERE train_id=%s",
                    (train_id,)
                )

                conn.commit()
                conn.close()

                self.respond(f"Ticket Booked Successfully! Seat No: {seat_no}")


            # -------- CANCEL --------
            elif self.path == "/cancel":
                booking_id = form['booking_id'][0]

                conn = get_connection()
                cur = conn.cursor()

                cur.execute("SELECT train_id FROM bookings WHERE booking_id=%s", (booking_id,))
                result = cur.fetchone()

                if not result:
                    self.respond("Booking Not Found")
                    return

                train_id = result[0]

                cur.execute(
                    "UPDATE bookings SET status='CANCELLED' WHERE booking_id=%s",
                    (booking_id,)
                )

                cur.execute(
                    "UPDATE trains SET available_seats = available_seats + 1 WHERE train_id=%s",
                    (train_id,)
                )

                conn.commit()
                conn.close()

                self.respond("Booking Cancelled Successfully")

        except Exception as e:
            self.send_error(500, str(e))


    # ================= DASHBOARD (IRCTC STYLE FIXED) =================
    def dashboard(self):
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM trains")
        trains = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM bookings")
        bookings = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM bookings WHERE status='CANCELLED'")
        cancelled = cur.fetchone()[0]

        conn.close()

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>IRCTC Dashboard</title>

            <style>
                body {{
                    margin: 0;
                    font-family: Arial;
                    background: linear-gradient(135deg,#0f2027,#203a43,#2c5364);
                    color: white;
                }}

                .navbar {{
                    background: #111;
                    padding: 15px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }}

                .navbar h2 {{
                    margin: 0;
                    color: #ffcc00;
                }}

                .nav a {{
                    color: white;
                    margin: 0 10px;
                    text-decoration: none;
                    font-weight: bold;
                }}

                .container {{
                    text-align: center;
                    padding: 40px;
                }}

                .cards {{
                    display: flex;
                    justify-content: center;
                    gap: 20px;
                    flex-wrap: wrap;
                }}

                .card {{
                    background: white;
                    color: black;
                    padding: 25px;
                    border-radius: 12px;
                    width: 180px;
                    box-shadow: 0 10px 20px rgba(0,0,0,0.3);
                    transition: 0.3s;
                }}

                .card:hover {{
                    transform: scale(1.05);
                }}

                .card h1 {{
                    color: #203a43;
                    margin: 10px 0;
                }}
            </style>
        </head>

        <body>

            <div class="navbar">
                <h2>🚆 IRCTC Railway System</h2>
                <div class="nav">
                    <a href="/">Home</a>
                    <a href="/trains">Trains</a>
                    <a href="/bookings">Bookings</a>
                </div>
            </div>

            <div class="container">

                <h2>Welcome to Smart Railway Booking System</h2>
                <p>Fast • Secure • Digital Ticketing</p>

                <div class="cards">

                    <div class="card">
                        <h1>🚆 {trains}</h1>
                        <p>Trains</p>
                    </div>

                    <div class="card">
                        <h1>🎫 {bookings}</h1>
                        <p>Bookings</p>
                    </div>

                    <div class="card">
                        <h1>❌ {cancelled}</h1>
                        <p>Cancelled</p>
                    </div>

                </div>

            </div>

        </body>
        </html>
        """

        self.respond_html(html)


    # ================= TRAINS =================
    def trains(self):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM trains")
        rows = cur.fetchall()
        conn.close()

        html = "<h2>🚆 Trains</h2><table border='1' style='margin:auto'>"
        html += "<tr><th>ID</th><th>Name</th><th>Source</th><th>Destination</th><th>Seats</th></tr>"

        for r in rows:
            html += f"<tr><td>{r[0]}</td><td>{r[1]}</td><td>{r[2]}</td><td>{r[3]}</td><td>{r[7]}</td></tr>"

        html += "</table><br><a href='/dashboard'>Back</a>"
        self.respond_html(html)


    # ================= BOOKINGS =================
    def bookings(self):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM bookings")
        rows = cur.fetchall()
        conn.close()

        html = """
        <h2>📋 Bookings</h2>
        <table border='1' style='margin:auto'>
        <tr><th>ID</th><th>Name</th><th>Train</th><th>Seat</th><th>Status</th></tr>
        """

        for r in rows:
            html += f"<tr><td>{r[0]}</td><td>{r[1]}</td><td>{r[2]}</td><td>{r[3]}</td><td>{r[4]}</td></tr>"

        html += "</table><br><a href='/dashboard'>Back</a>"
        self.respond_html(html)


    # ================= TEMPLATE LOADER =================
    def render_template(self, file):
        try:
            path = os.path.join("templates", file)
            with open(path, "rb") as f:
                self.send_response(200)
                self.send_header("Content-type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(f.read())
        except:
            self.send_error(404, "Page Not Found")


    # ================= RESPONSE =================
    def respond(self, msg):
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(msg.encode())


    def respond_html(self, html):
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode())


# ---------------- START SERVER ----------------
print("🚆 IRCTC System Running at http://localhost:8000")
httpd = HTTPServer(("localhost", PORT), Handler)
httpd.serve_forever()