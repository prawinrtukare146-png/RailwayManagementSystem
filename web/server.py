from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse
import mysql.connector
import os
import html
from dotenv import load_dotenv

load_dotenv()

PORT = 8000
# ---------------- DATABASE ----------------
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD"),
        database="railway_db"
    )

# ---------------- SERVER ----------------
class Handler(BaseHTTPRequestHandler):

    # ================= GET =================
    def do_GET(self):
        try:
            # Remove query parameters from the URL
            path = urllib.parse.urlparse(self.path).path

            if path == "/" or path == "/index.html":
                self.render_template("index.html")

            elif path == "/dashboard":
                self.dashboard()

            elif path == "/trains":
                self.trains()

            elif path == "/bookings":
                self.bookings()

            elif path == "/location":
                self.location()

            elif path == "/book.html":
                self.render_template("book.html")

            elif path == "/cancel.html":
                self.render_template("cancel.html")

            elif path == "/location.html":
                self.location()

            elif path == "/favicon.ico":
                self.send_error(404, "Favicon Not Found")

            else:
                # Load other existing HTML templates
                filename = path.lstrip("/")

                if filename.endswith(".html") and "/" not in filename:
                    self.render_template(filename)
                else:
                    self.send_error(404, "Page Not Found")

        except Exception as e:
            self.send_error(500, str(e))

    # ================= POST =================
    def do_POST(self):
        try:
            path = urllib.parse.urlparse(self.path).path

            length = int(self.headers.get("Content-Length", 0))
            data = self.rfile.read(length).decode("utf-8")
            form = urllib.parse.parse_qs(data)

            # -------- BOOK TICKET --------
            if path == "/book":
                name = form.get("name", [""])[0].strip()
                train_id = form.get("train_id", [""])[0].strip()

                if not name or not train_id:
                    self.respond("Please enter passenger name and train ID.")
                    return

                conn = get_connection()
                cur = conn.cursor()

                try:
                    cur.execute(
                        "SELECT available_seats FROM trains WHERE train_id=%s",
                        (train_id,)
                    )
                    result = cur.fetchone()

                    if not result:
                        self.respond("Train Not Found")
                        return

                    seats = result[0]

                    if seats <= 0:
                        self.respond("No Seats Available")
                        return

                    # Preserve the project's original seat allocation logic
                    seat_no = seats

                    cur.execute(
                        """
                        INSERT INTO bookings
                        (passenger_name, train_id, seat_number, status)
                        VALUES (%s, %s, %s, 'BOOKED')
                        """,
                        (name, train_id, seat_no)
                    )

                    cur.execute(
                        """
                        UPDATE trains
                        SET available_seats = available_seats - 1
                        WHERE train_id = %s
                        """,
                        (train_id,)
                    )

                    conn.commit()

                    self.respond(
                        f"Ticket Booked Successfully! Seat No: {seat_no}"
                    )

                except Exception:
                    conn.rollback()
                    raise

                finally:
                    cur.close()
                    conn.close()

            # -------- CANCEL TICKET --------
            elif path == "/cancel":
                booking_id = form.get("booking_id", [""])[0].strip()

                if not booking_id:
                    self.respond("Please enter a booking ID.")
                    return

                conn = get_connection()
                cur = conn.cursor()

                try:
                    cur.execute(
                        """
                        SELECT train_id, status
                        FROM bookings
                        WHERE booking_id = %s
                        """,
                        (booking_id,)
                    )
                    result = cur.fetchone()

                    if not result:
                        self.respond("Booking Not Found")
                        return

                    train_id, status = result

                    if status == "CANCELLED":
                        self.respond("This booking is already cancelled.")
                        return

                    cur.execute(
                        """
                        UPDATE bookings
                        SET status = 'CANCELLED'
                        WHERE booking_id = %s
                        """,
                        (booking_id,)
                    )

                    cur.execute(
                        """
                        UPDATE trains
                        SET available_seats = available_seats + 1
                        WHERE train_id = %s
                        """,
                        (train_id,)
                    )

                    conn.commit()

                    self.respond("Booking Cancelled Successfully")

                except Exception:
                    conn.rollback()
                    raise

                finally:
                    cur.close()
                    conn.close()

            else:
                self.send_error(404, "POST Route Not Found")

        except Exception as e:
            self.send_error(500, str(e))

    # ================= DASHBOARD =================
    def dashboard(self):
        conn = get_connection()
        cur = conn.cursor()

        try:
            cur.execute("SELECT COUNT(*) FROM trains")
            trains_count = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM bookings")
            bookings_count = cur.fetchone()[0]

            cur.execute(
                "SELECT COUNT(*) FROM bookings WHERE status='CANCELLED'"
            )
            cancelled_count = cur.fetchone()[0]

        finally:
            cur.close()
            conn.close()

        page = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Railway Dashboard</title>
            <style>
                body {{
                    margin: 0;
                    font-family: Arial, sans-serif;
                    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
                    color: white;
                    text-align: center;
                }}
                .navbar {{
                    background: #111;
                    padding: 18px;
                }}
                .navbar a {{
                    color: white;
                    text-decoration: none;
                    margin: 12px;
                }}
                .container {{
                    padding: 40px 15px;
                }}
                .cards {{
                    display: flex;
                    justify-content: center;
                    flex-wrap: wrap;
                    gap: 20px;
                    margin-top: 30px;
                }}
                .card {{
                    background: white;
                    color: black;
                    padding: 25px;
                    border-radius: 12px;
                    width: 180px;
                }}
                .card h1 {{
                    color: #203a43;
                }}
            </style>
        </head>
        <body>
            <div class="navbar">
                <h2>🚆 Railway Management System</h2>
                <a href="/">Home</a>
                <a href="/trains">Trains</a>
                <a href="/bookings">Bookings</a>
                <a href="/location">Track Location</a>
            </div>

            <div class="container">
                <h2>Welcome to Smart Railway Booking System</h2>
                <p>Fast • Secure • Digital Ticketing</p>

                <div class="cards">
                    <div class="card">
                        <h1>{trains_count}</h1>
                        <p>Trains</p>
                    </div>

                    <div class="card">
                        <h1>{bookings_count}</h1>
                        <p>Bookings</p>
                    </div>

                    <div class="card">
                        <h1>{cancelled_count}</h1>
                        <p>Cancelled</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

        self.respond_html(page)

    # ================= TRAINS =================
    def trains(self):
        conn = get_connection()
        cur = conn.cursor()

        try:
            cur.execute(
                """
                SELECT train_id, train_name, source_station,
                       destination_station, departure_time,
                       arrival_time, available_seats
                FROM trains
                """
            )
            rows = cur.fetchall()

        finally:
            cur.close()
            conn.close()

        page = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Available Trains</title>
            <style>
                * { box-sizing: border-box; }
                body {
                    margin: 0;
                    min-height: 100vh;
                    padding: 35px 20px 45px;
                    font-family: "Segoe UI", Arial, sans-serif;
                    text-align: center;
                    color: #f8fafc;
                    background: linear-gradient(-45deg, #071a2b, #123d52, #174e68, #101d3d);
                    background-size: 400% 400%;
                    animation: backgroundFlow 14s ease infinite;
                    overflow-x: hidden;
                }
                @keyframes backgroundFlow {
                    0% { background-position: 0% 50%; }
                    50% { background-position: 100% 50%; }
                    100% { background-position: 0% 50%; }
                }
                .page-title {
                    margin: 8px 0 10px;
                    font-size: clamp(27px, 4vw, 40px);
                    letter-spacing: 1px;
                    text-shadow: 0 0 18px rgba(56, 189, 248, .55);
                    animation: titleReveal .9s ease both;
                }
                @keyframes titleReveal {
                    from { opacity: 0; transform: translateY(-22px); }
                    to { opacity: 1; transform: translateY(0); }
                }
                .train-icon {
                    display: inline-block;
                    animation: trainBounce 2s ease-in-out infinite;
                }
                @keyframes trainBounce {
                    0%, 100% { transform: translateY(0) rotate(0); }
                    50% { transform: translateY(-7px) rotate(-3deg); }
                }
                .subtitle {
                    margin: 0 0 25px;
                    color: #c8eaf8;
                    font-size: 15px;
                    letter-spacing: 2px;
                }
                .track {
                    max-width: 1100px;
                    height: 5px;
                    margin: 0 auto 25px;
                    border-radius: 20px;
                    background: rgba(255,255,255,.18);
                    overflow: hidden;
                }
                .track::after {
                    content: "";
                    display: block;
                    width: 28%;
                    height: 100%;
                    border-radius: inherit;
                    background: linear-gradient(90deg, transparent, #67e8f9, #fef08a, transparent);
                    animation: trackMove 3s linear infinite;
                }
                @keyframes trackMove {
                    from { transform: translateX(-110%); }
                    to { transform: translateX(390%); }
                }
                .table-wrap {
                    max-width: 1100px;
                    margin: 0 auto;
                    overflow-x: auto;
                    border: 1px solid rgba(255,255,255,.25);
                    border-radius: 16px;
                    background: rgba(255,255,255,.96);
                    box-shadow: 0 18px 55px rgba(0,0,0,.32);
                    animation: tableReveal .8s .15s ease both;
                }
                @keyframes tableReveal {
                    from { opacity: 0; transform: translateY(25px) scale(.98); }
                    to { opacity: 1; transform: translateY(0) scale(1); }
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    color: #172b3a;
                    background: white;
                }
                th, td {
                    padding: 15px 13px;
                    border-bottom: 1px solid #e2e8f0;
                    white-space: nowrap;
                }
                th {
                    color: white;
                    background: linear-gradient(120deg, #0f3547, #17627a);
                    font-size: 14px;
                    text-transform: uppercase;
                    letter-spacing: .6px;
                }
                tbody tr {
                    animation: rowAppear .55s ease both;
                    transition: transform .22s ease, background .22s ease, box-shadow .22s ease;
                }
                tbody tr:nth-child(1) { animation-delay: .08s; }
                tbody tr:nth-child(2) { animation-delay: .16s; }
                tbody tr:nth-child(3) { animation-delay: .24s; }
                tbody tr:nth-child(4) { animation-delay: .32s; }
                tbody tr:nth-child(5) { animation-delay: .40s; }
                tbody tr:nth-child(6) { animation-delay: .48s; }
                tbody tr:nth-child(7) { animation-delay: .56s; }
                @keyframes rowAppear {
                    from { opacity: 0; transform: translateX(-18px); }
                    to { opacity: 1; transform: translateX(0); }
                }
                tbody tr:nth-child(even) { background: #f0f9ff; }
                tbody tr:hover {
                    background: #dff7ff;
                    transform: scale(1.012);
                    box-shadow: 0 5px 18px rgba(14,116,144,.15);
                }
                tbody tr:last-child td { border-bottom: 0; }
                td:last-child {
                    color: #047857;
                    font-weight: 800;
                }
                .navigation {
                    display: flex;
                    justify-content: center;
                    flex-wrap: wrap;
                    gap: 12px;
                    margin-top: 27px;
                }
                .navigation a {
                    display: inline-block;
                    padding: 11px 20px;
                    border: 1px solid rgba(255,255,255,.35);
                    border-radius: 30px;
                    color: white;
                    background: rgba(255,255,255,.1);
                    text-decoration: none;
                    font-weight: 700;
                    transition: transform .25s ease, background .25s ease, box-shadow .25s ease;
                    backdrop-filter: blur(8px);
                }
                .navigation a:hover {
                    transform: translateY(-4px);
                    background: #06b6d4;
                    box-shadow: 0 8px 24px rgba(6,182,212,.35);
                }
                .footer-note {
                    margin-top: 24px;
                    color: #c8eaf8;
                    font-size: 13px;
                }
                @media (max-width: 650px) {
                    body { padding: 25px 10px; }
                    th, td { padding: 11px 9px; font-size: 13px; }
                    .subtitle { letter-spacing: 1px; }
                }
                @media (prefers-reduced-motion: reduce) {
                    *, *::before, *::after {
                        animation-duration: .01ms !important;
                        animation-iteration-count: 1 !important;
                        scroll-behavior: auto !important;
                        transition-duration: .01ms !important;
                    }
                }
            </style>
        </head>
        <body>
            <h2 class="page-title"><span class="train-icon">🚆</span> Available Trains</h2>
            <p class="subtitle">YOUR JOURNEY STARTS HERE · EXPLORE THE ROUTES</p>
            <div class="track"></div>
            <div class="table-wrap">
            <table>
                <thead>
                <tr>
                    <th>ID</th>
                    <th>Train Name</th>
                    <th>Source</th>
                    <th>Destination</th>
                    <th>Departure</th>
                    <th>Arrival</th>
                    <th>Available Seats</th>
                </tr>
                </thead>
                <tbody>
        """

        for row in rows:
            page += "<tr>"
            for value in row:
                page += f"<td>{html.escape(str(value))}</td>"
            page += "</tr>"

        page += """
                </tbody>
            </table>
            </div>
            <div class="navigation">
                <a href="/">🏠 Home</a>
                <a href="/dashboard">📊 Dashboard</a>
                <a href="/book.html">🎟️ Book Ticket</a>
                <a href="/location">📍 Track Location</a>
            </div>
            <p class="footer-note">🚆 Travel smarter. Enjoy your journey!</p>
        </body>
        </html>
        """

        self.respond_html(page)

       # ================= ANIMATED BOOKINGS =================
    def bookings(self):
        conn = get_connection()
        cur = conn.cursor()

        try:
            cur.execute(
                """
                SELECT booking_id, passenger_name, train_id,
                       seat_number, status
                FROM bookings
                ORDER BY booking_id
                """
            )
            rows = cur.fetchall()

        finally:
            cur.close()
            conn.close()

        page = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">

            <title>Bookings | Railway Management System</title>

            <style>
                * {
                    box-sizing: border-box;
                }

                body {
                    margin: 0;
                    min-height: 100vh;
                    padding: 35px 20px;
                    font-family: "Segoe UI", Arial, sans-serif;
                    color: #f8fafc;
                    text-align: center;
                    background: linear-gradient(
                        -45deg,
                        #071525,
                        #142a4b,
                        #164e63,
                        #1e1b4b
                    );
                    background-size: 400% 400%;
                    animation: backgroundFlow 14s ease infinite;
                }

                @keyframes backgroundFlow {
                    0% { background-position: 0% 50%; }
                    50% { background-position: 100% 50%; }
                    100% { background-position: 0% 50%; }
                }

                header {
                    margin-bottom: 28px;
                    animation: titleReveal .8s ease both;
                }

                @keyframes titleReveal {
                    from {
                        opacity: 0;
                        transform: translateY(-25px);
                    }
                    to {
                        opacity: 1;
                        transform: translateY(0);
                    }
                }

                .icon {
                    display: inline-block;
                    font-size: 40px;
                    animation: floatIcon 2s ease-in-out infinite;
                    filter: drop-shadow(0 0 12px #38bdf8);
                }

                @keyframes floatIcon {
                    0%, 100% { transform: translateY(0); }
                    50% { transform: translateY(-7px); }
                }

                h1 {
                    margin: 10px 0;
                    font-size: clamp(28px, 4vw, 42px);
                    text-shadow: 0 0 20px #38bdf855;
                }

                .subtitle {
                    color: #bfdbfe;
                    letter-spacing: 2px;
                    font-size: 13px;
                }

                .summary {
                    display: inline-block;
                    margin: 15px auto 25px;
                    padding: 13px 24px;
                    color: #e0f2fe;
                    border: 1px solid #7dd3fc55;
                    border-radius: 15px;
                    background: #ffffff0d;
                    animation: fadeIn .8s .2s ease both;
                }

                @keyframes fadeIn {
                    from { opacity: 0; }
                    to { opacity: 1; }
                }

                .table-card {
                    width: min(1100px, 100%);
                    margin: auto;
                    overflow-x: auto;
                    border: 1px solid #ffffff35;
                    border-radius: 18px;
                    background: white;
                    box-shadow: 0 20px 60px #00000045;
                    animation: cardReveal .9s .15s ease both;
                }

                @keyframes cardReveal {
                    from {
                        opacity: 0;
                        transform: translateY(30px) scale(.98);
                    }
                    to {
                        opacity: 1;
                        transform: translateY(0) scale(1);
                    }
                }

                table {
                    width: 100%;
                    border-collapse: collapse;
                    color: #172b3a;
                }

                th {
                    padding: 17px 14px;
                    color: white;
                    background: linear-gradient(120deg, #0f3547, #17627a);
                    font-size: 13px;
                    text-transform: uppercase;
                    letter-spacing: .5px;
                }

                td {
                    padding: 15px 14px;
                    border-bottom: 1px solid #e2e8f0;
                    white-space: nowrap;
                }

                tbody tr {
                    animation: rowReveal .55s ease both;
                    transition: background .25s, transform .25s;
                }

                tbody tr:nth-child(1) { animation-delay: .08s; }
                tbody tr:nth-child(2) { animation-delay: .16s; }
                tbody tr:nth-child(3) { animation-delay: .24s; }
                tbody tr:nth-child(4) { animation-delay: .32s; }
                tbody tr:nth-child(5) { animation-delay: .40s; }
                tbody tr:nth-child(6) { animation-delay: .48s; }
                tbody tr:nth-child(7) { animation-delay: .56s; }

                @keyframes rowReveal {
                    from {
                        opacity: 0;
                        transform: translateX(-18px);
                    }
                    to {
                        opacity: 1;
                        transform: translateX(0);
                    }
                }

                tbody tr:nth-child(even) {
                    background: #f0f9ff;
                }

                tbody tr:hover {
                    background: #dff7ff;
                    transform: scale(1.01);
                }

                tbody tr:last-child td {
                    border-bottom: none;
                }

                .booking-id {
                    color: #0369a1;
                    font-weight: 800;
                }

                .status {
                    display: inline-block;
                    padding: 6px 12px;
                    border-radius: 20px;
                    font-size: 12px;
                    font-weight: 800;
                    background: #dcfce7;
                    color: #166534;
                }

                .status-cancelled {
                    background: #fee2e2;
                    color: #991b1b;
                }

                .navigation {
                    display: flex;
                    justify-content: center;
                    flex-wrap: wrap;
                    gap: 13px;
                    margin-top: 30px;
                }

                .navigation a {
                    display: inline-block;
                    padding: 12px 22px;
                    color: #e0f2fe;
                    text-decoration: none;
                    font-weight: 700;
                    border: 1px solid #7dd3fc55;
                    border-radius: 30px;
                    background: #ffffff12;
                    transition: .3s ease;
                }

                .navigation a:hover {
                    transform: translateY(-4px);
                    background: #0891b2;
                    box-shadow: 0 8px 25px #06b6d455;
                }

                footer {
                    margin-top: 30px;
                    color: #bfdbfe;
                    font-size: 13px;
                }

                @media (max-width: 600px) {
                    body { padding: 25px 10px; }
                    th, td { padding: 12px 9px; font-size: 12px; }
                }

                @media (prefers-reduced-motion: reduce) {
                    *, *::before, *::after {
                        animation-duration: .01ms !important;
                        animation-iteration-count: 1 !important;
                        transition-duration: .01ms !important;
                    }
                }
            </style>
        </head>

        <body>
            <header>
                <div class="icon">📋</div>
                <h1>Passenger Bookings</h1>
                <p class="subtitle">YOUR TICKETS · YOUR JOURNEY</p>
            </header>

            <div class="summary">
                🎫 Total Booking Records: <strong>""" + str(len(rows)) + """</strong>
            </div>

            <div class="table-card">
                <table>
                    <thead>
                        <tr>
                            <th>Booking ID</th>
                            <th>Passenger</th>
                            <th>Train ID</th>
                            <th>Seat</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
        """

        for row in rows:
            page += "<tr>"

            for index, value in enumerate(row):
                if index == 0:
                    page += (
                        '<td class="booking-id">'
                        f'{html.escape(str(value))}</td>'
                    )

                elif index == 4:
                    status_value = str(value)
                    status_class = (
                        "status-cancelled"
                        if status_value.upper() == "CANCELLED"
                        else ""
                    )

                    page += (
                        f'<td><span class="status {status_class}">'
                        f'{html.escape(status_value)}</span></td>'
                    )

                else:
                    page += (
                        f"<td>{html.escape(str(value))}</td>"
                    )

            page += "</tr>"

        if not rows:
            page += """
                <tr>
                    <td colspan="5">No booking records found.</td>
                </tr>
            """

        page += """
                    </tbody>
                </table>
            </div>

            <nav class="navigation">
                <a href="/">🏠 Home</a>
                <a href="/dashboard">📊 Dashboard</a>
                <a href="/trains">🚆 Available Trains</a>
                <a href="/book.html">🎟️ Book Ticket</a>
                <a href="/cancel.html">❌ Cancel Ticket</a>
            </nav>

            <footer>
                🚆 Every journey begins with a booking.
            </footer>
        </body>
        </html>
        """

        self.respond_html(page)

      # ================= ANIMATED TRACK LOCATION =================
    def location(self):
        conn = get_connection()
        cur = conn.cursor()

        try:
            cur.execute(
                """
                SELECT l.train_id, t.train_name, l.current_station,
                       l.updated_time
                FROM locations l
                LEFT JOIN trains t ON l.train_id = t.train_id
                ORDER BY l.train_id
                """
            )
            rows = cur.fetchall()

        finally:
            cur.close()
            conn.close()

        page = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">

            <title>Track Train Location | Railway Management System</title>

            <style>
                * {
                    box-sizing: border-box;
                }

                body {
                    margin: 0;
                    min-height: 100vh;
                    padding: 35px 20px;
                    font-family: "Segoe UI", Arial, sans-serif;
                    color: #f8fafc;
                    text-align: center;
                    background: linear-gradient(
                        -45deg,
                        #061525,
                        #10364b,
                        #14536a,
                        #111b3d
                    );
                    background-size: 400% 400%;
                    animation: backgroundFlow 14s ease infinite;
                    overflow-x: hidden;
                }

                @keyframes backgroundFlow {
                    0%   { background-position: 0% 50%; }
                    50%  { background-position: 100% 50%; }
                    100% { background-position: 0% 50%; }
                }

                .page-header {
                    margin-bottom: 30px;
                    animation: slideDown .8s ease both;
                }

                @keyframes slideDown {
                    from {
                        opacity: 0;
                        transform: translateY(-25px);
                    }
                    to {
                        opacity: 1;
                        transform: translateY(0);
                    }
                }

                .location-icon {
                    display: inline-block;
                    font-size: 42px;
                    animation: locationPulse 2s ease-in-out infinite;
                    filter: drop-shadow(0 0 15px #f472b6);
                }

                @keyframes locationPulse {
                    0%, 100% {
                        transform: translateY(0) scale(1);
                    }
                    50% {
                        transform: translateY(-7px) scale(1.08);
                    }
                }

                h1 {
                    margin: 10px 0;
                    font-size: clamp(28px, 4vw, 42px);
                    text-shadow: 0 0 20px #38bdf855;
                }

                .subtitle {
                    color: #bae6fd;
                    letter-spacing: 2px;
                    font-size: 13px;
                }

                .track-line {
                    max-width: 1000px;
                    height: 4px;
                    margin: 30px auto;
                    overflow: hidden;
                    border-radius: 20px;
                    background: #ffffff22;
                }

                .track-line::after {
                    content: "";
                    display: block;
                    width: 25%;
                    height: 100%;
                    background: linear-gradient(
                        90deg,
                        transparent,
                        #67e8f9,
                        #ffffff,
                        transparent
                    );
                    animation: trackMove 2.5s linear infinite;
                }

                @keyframes trackMove {
                    from { transform: translateX(-110%); }
                    to { transform: translateX(410%); }
                }

                .table-card {
                    width: min(1000px, 100%);
                    margin: auto;
                    overflow-x: auto;
                    border: 1px solid #ffffff35;
                    border-radius: 18px;
                    background: #ffffff;
                    box-shadow: 0 20px 60px #00000045;
                    animation: cardReveal .9s .15s ease both;
                }

                @keyframes cardReveal {
                    from {
                        opacity: 0;
                        transform: translateY(30px) scale(.98);
                    }
                    to {
                        opacity: 1;
                        transform: translateY(0) scale(1);
                    }
                }

                table {
                    width: 100%;
                    border-collapse: collapse;
                    color: #172b3a;
                }

                th {
                    padding: 17px 14px;
                    color: white;
                    background: linear-gradient(120deg, #0f3547, #17627a);
                    font-size: 14px;
                    text-transform: uppercase;
                    letter-spacing: .5px;
                }

                td {
                    padding: 16px 14px;
                    border-bottom: 1px solid #e2e8f0;
                    white-space: nowrap;
                }

                tbody tr {
                    animation: rowReveal .6s ease both;
                    transition: background .25s, transform .25s;
                }

                tbody tr:nth-child(1) { animation-delay: .1s; }
                tbody tr:nth-child(2) { animation-delay: .2s; }
                tbody tr:nth-child(3) { animation-delay: .3s; }
                tbody tr:nth-child(4) { animation-delay: .4s; }
                tbody tr:nth-child(5) { animation-delay: .5s; }

                @keyframes rowReveal {
                    from {
                        opacity: 0;
                        transform: translateX(-20px);
                    }
                    to {
                        opacity: 1;
                        transform: translateX(0);
                    }
                }

                tbody tr:nth-child(even) {
                    background: #f0f9ff;
                }

                tbody tr:hover {
                    background: #dff7ff;
                    transform: scale(1.01);
                }

                tbody tr:last-child td {
                    border-bottom: none;
                }

                .station {
                    color: #047857;
                    font-weight: 800;
                }

                .navigation {
                    display: flex;
                    justify-content: center;
                    flex-wrap: wrap;
                    gap: 13px;
                    margin-top: 30px;
                }

                .navigation a {
                    display: inline-block;
                    padding: 12px 22px;
                    color: #e0f2fe;
                    text-decoration: none;
                    font-weight: 700;
                    border: 1px solid #7dd3fc55;
                    border-radius: 30px;
                    background: #ffffff12;
                    transition: .3s ease;
                }

                .navigation a:hover {
                    transform: translateY(-4px);
                    background: #0891b2;
                    box-shadow: 0 8px 25px #06b6d455;
                }

                .footer {
                    margin-top: 30px;
                    color: #bae6fd;
                    font-size: 13px;
                }

                @media (max-width: 600px) {
                    body {
                        padding: 25px 10px;
                    }

                    th, td {
                        padding: 12px 9px;
                        font-size: 12px;
                    }
                }

                @media (prefers-reduced-motion: reduce) {
                    *, *::before, *::after {
                        animation-duration: .01ms !important;
                        animation-iteration-count: 1 !important;
                        transition-duration: .01ms !important;
                    }
                }
            </style>
        </head>

        <body>
            <header class="page-header">
                <div class="location-icon">📍</div>
                <h1>Track Train Location</h1>
                <p class="subtitle">
                    REAL-TIME JOURNEY INFORMATION
                </p>
            </header>

            <div class="track-line"></div>

            <div class="table-card">
                <table>
                    <thead>
                        <tr>
                            <th>Train ID</th>
                            <th>Train Name</th>
                            <th>Current Station</th>
                            <th>Last Updated</th>
                        </tr>
                    </thead>

                    <tbody>
        """

        for row in rows:
            page += "<tr>"
            for index, value in enumerate(row):
                css_class = ' class="station"' if index == 2 else ""
                page += (
                    f"<td{css_class}>"
                    f"{html.escape(str(value if value is not None else 'N/A'))}"
                    "</td>"
                )
            page += "</tr>"

        if not rows:
            page += """
                <tr>
                    <td colspan="4">No train location records found.</td>
                </tr>
            """

        page += """
                    </tbody>
                </table>
            </div>

            <nav class="navigation">
                <a href="/">🏠 Home</a>
                <a href="/trains">🚆 Available Trains</a>
                <a href="/dashboard">📊 Dashboard</a>
                <a href="/book.html">🎟️ Book Ticket</a>
            </nav>

            <footer class="footer">
                🚆 Follow your journey. Travel smarter.
            </footer>
        </body>
        </html>
        """

        self.respond_html(page)

    # ================= ANIMATED BOOK TICKET PAGE =================
    def book_page(self):
        page = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Book Your Ticket | Railway Management System</title>
<style>
    * { box-sizing: border-box; }
    :root { color-scheme: dark; }
    body {
        margin: 0; min-height: 100vh; overflow-x: hidden;
        font-family: "Segoe UI", Arial, sans-serif; color: #f8fafc;
        background: linear-gradient(-45deg, #061525, #10364b, #14536a, #111b3d);
        background-size: 400% 400%; animation: bgFlow 14s ease infinite;
        display: flex; flex-direction: column;
    }
    @keyframes bgFlow { 0% {background-position:0% 50%} 50% {background-position:100% 50%} 100% {background-position:0% 50%} }
    .topbar { display:flex; justify-content:space-between; align-items:center; gap:16px; flex-wrap:wrap; padding:18px clamp(18px,5vw,70px); background:rgba(3,12,25,.58); border-bottom:1px solid rgba(125,211,252,.22); backdrop-filter:blur(12px); }
    .brand { display:flex; align-items:center; gap:12px; font-weight:800; font-size:clamp(17px,2vw,22px); }
    .brand-icon { display:inline-block; font-size:30px; filter:drop-shadow(0 0 10px #38bdf8); animation: trainBob 2s ease-in-out infinite; }
    @keyframes trainBob { 0%,100% {transform:translateY(0)} 50% {transform:translateY(-5px)} }
    nav { display:flex; flex-wrap:wrap; gap:10px; }
    nav a, .back-link { color:#e0f2fe; text-decoration:none; padding:10px 14px; border:1px solid rgba(125,211,252,.28); border-radius:999px; transition:.25s; }
    nav a:hover, .back-link:hover { background:#0ea5e9; color:#fff; transform:translateY(-2px); box-shadow:0 0 20px #0ea5e966; }
    main { width:min(1120px, 100%); margin:auto; padding:45px 20px 35px; display:grid; grid-template-columns:1fr 1fr; gap:38px; align-items:center; }
    .intro { animation: slideIn .8s ease both; }
    @keyframes slideIn { from {opacity:0; transform:translateX(-24px)} to {opacity:1; transform:translateX(0)} }
    .eyebrow { display:inline-block; color:#7dd3fc; border:1px solid #38bdf866; background:#0c4a6e55; border-radius:999px; padding:8px 13px; font-size:12px; letter-spacing:2px; text-transform:uppercase; }
    h1 { margin:20px 0 14px; font-size:clamp(35px,5vw,58px); line-height:1.08; letter-spacing:-1.5px; }
    h1 .accent { color:#67e8f9; text-shadow:0 0 24px #22d3ee66; }
    .intro p { max-width:470px; color:#c5dced; line-height:1.8; font-size:16px; }
    .journey-art { position:relative; height:175px; max-width:460px; margin-top:28px; border-radius:20px; overflow:hidden; border:1px solid #7dd3fc33; background:linear-gradient(135deg,#082f49aa,#172554aa); }
    .journey-art:before { content:""; position:absolute; left:0; right:0; bottom:32px; height:4px; background:repeating-linear-gradient(90deg,#bae6fd 0 32px,transparent 32px 48px); animation: trackMove 1.3s linear infinite; }
    .journey-art:after { content:""; position:absolute; left:-30%; right:-30%; bottom:23px; height:1px; background:#38bdf866; }
    @keyframes trackMove { to {background-position:48px 0} }
    .art-train { position:absolute; left:13%; bottom:39px; font-size:76px; filter:drop-shadow(0 0 17px #38bdf8aa); animation: trainTravel 5s ease-in-out infinite alternate; }
    @keyframes trainTravel { from {transform:translateX(0)} to {transform:translateX(175px)} }
    .star { position:absolute; color:#bae6fd; animation: twinkle 2s ease-in-out infinite alternate; }
    .star.one {top:20px;left:20%;font-size:20px}.star.two {top:44px;right:18%;font-size:15px;animation-delay:.8s}.star.three {top:17px;right:37%;font-size:12px;animation-delay:.4s}
    @keyframes twinkle { from {opacity:.3;transform:scale(.8)} to {opacity:1;transform:scale(1.2)} }
    .benefits { display:flex; gap:10px; flex-wrap:wrap; margin-top:22px; }
    .benefits span { color:#dbeafe; font-size:13px; padding:9px 12px; background:#ffffff0b; border:1px solid #ffffff16; border-radius:10px; }
    .booking-card { position:relative; padding:clamp(24px,4vw,38px); border-radius:26px; background:linear-gradient(145deg,rgba(15,35,59,.94),rgba(9,22,42,.92)); border:1px solid rgba(125,211,252,.3); box-shadow:0 25px 70px #02061788, inset 0 1px #ffffff12; animation: cardEnter .9s .12s ease both; }
    @keyframes cardEnter { from {opacity:0;transform:translateY(25px) scale(.98)} to {opacity:1;transform:translateY(0) scale(1)} }
    .booking-card:before { content:""; position:absolute; top:-1px; left:12%; right:12%; height:2px; background:linear-gradient(90deg,transparent,#67e8f9,transparent); filter:drop-shadow(0 0 8px #22d3ee); }
    .card-title { margin:0; font-size:27px; }
    .card-subtitle { color:#a9c4d9; margin:9px 0 26px; font-size:14px; line-height:1.6; }
    .field { margin-bottom:20px; }
    label { display:block; margin-bottom:9px; color:#e0f2fe; font-size:14px; font-weight:700; }
    .input-wrap { position:relative; }
    .input-icon { position:absolute; left:15px; top:50%; transform:translateY(-50%); font-size:18px; pointer-events:none; }
    input { width:100%; border:1px solid #42627b; border-radius:13px; outline:none; background:#071729; color:#f8fafc; padding:15px 15px 15px 46px; font-size:15px; transition:border-color .25s,box-shadow .25s,background .25s; }
    input::placeholder { color:#7892a8; }
    input:focus { border-color:#38bdf8; background:#092038; box-shadow:0 0 0 4px #0ea5e922,0 0 20px #0ea5e91c; }
    .submit-btn { width:100%; margin-top:5px; padding:16px 18px; border:0; border-radius:13px; color:#032033; font-weight:900; font-size:16px; letter-spacing:.3px; cursor:pointer; background:linear-gradient(100deg,#67e8f9,#38bdf8,#a5f3fc); background-size:200% 100%; box-shadow:0 10px 28px #0ea5e933; transition:transform .25s,box-shadow .25s; animation: buttonGlow 3s ease-in-out infinite; }
    @keyframes buttonGlow { 0%,100% {background-position:0% 50%;box-shadow:0 8px 24px #0ea5e922} 50% {background-position:100% 50%;box-shadow:0 8px 30px #22d3ee55} }
    .submit-btn:hover { transform:translateY(-3px); box-shadow:0 14px 32px #22d3ee55; }
    .submit-btn:active { transform:translateY(0) scale(.99); }
    .secure-note { text-align:center; margin:17px 0 0; color:#91a9bd; font-size:12px; }
    .bottom { text-align:center; padding:0 20px 25px; color:#8eabc1; font-size:12px; }
    .bottom a { color:#a5f3fc; text-decoration:none; }
    @media(max-width:780px) { main {grid-template-columns:1fr;gap:25px;padding-top:30px}.intro {text-align:center}.intro p {margin-left:auto;margin-right:auto}.journey-art {margin-left:auto;margin-right:auto}.benefits {justify-content:center}.booking-card {max-width:560px;width:100%;margin:auto}.topbar {justify-content:center;text-align:center}nav {justify-content:center} }
    @media(prefers-reduced-motion:reduce) { *,*::before,*::after {animation-duration:.01ms!important;animation-iteration-count:1!important;scroll-behavior:auto!important;transition-duration:.01ms!important} }
</style>
</head>
<body>
<header class="topbar">
    <div class="brand"><span class="brand-icon">🚆</span><span>Railway Management System</span></div>
    <nav aria-label="Main navigation">
        <a href="/">🏠 Home</a><a href="/trains">🚉 View Trains</a><a href="/bookings">📋 Bookings</a>
    </nav>
</header>
<main>
    <section class="intro">
        <span class="eyebrow">✦ Your journey begins here</span>
        <h1>Book your ticket.<br><span class="accent">Enjoy the journey.</span></h1>
        <p>Plan your next trip with ease. Enter your passenger details and train ID to book your railway ticket in just a few steps.</p>
        <div class="journey-art" aria-hidden="true">
            <span class="star one">✦</span><span class="star two">✧</span><span class="star three">✦</span>
            <span class="art-train">🚆</span>
        </div>
        <div class="benefits"><span>⚡ Quick booking</span><span>🎫 Seat confirmation</span><span>🛡️ Simple & secure</span></div>
    </section>
    <section class="booking-card">
        <h2 class="card-title">🎟️ Book Your Ticket</h2>
        <p class="card-subtitle">Fill in the details below to reserve your seat.</p>
        <form action="/book" method="POST">
            <div class="field">
                <label for="name">Passenger Name</label>
                <div class="input-wrap"><span class="input-icon">👤</span><input type="text" id="name" name="name" placeholder="Enter passenger name" maxlength="100" autocomplete="name" required></div>
            </div>
            <div class="field">
                <label for="train_id">Train ID</label>
                <div class="input-wrap"><span class="input-icon">🚆</span><input type="number" id="train_id" name="train_id" placeholder="e.g. 1" min="1" step="1" required></div>
            </div>
            <button class="submit-btn" type="submit">✨ Confirm Booking <span aria-hidden="true">→</span></button>
        </form>
        <p class="secure-note">🚉 Please check the train ID before confirming your booking.</p>
    </section>
</main>
<footer class="bottom">Need to choose a train first? <a href="/trains">View available trains</a> · <a href="/">Back to Home</a></footer>
</body>
</html>"""
        self.respond_html(page)

    # ================= TEMPLATE LOADER =================
    def render_template(self, file):
        if file == "book.html":
            self.book_page()
            return
        base_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base_dir, "templates", file)

        # Prevent requests from accessing files outside templates
        if os.path.basename(file) != file:
            self.send_error(400, "Invalid template name")
            return

        try:
            with open(path, "rb") as template:
                self.send_response(200)
                self.send_header(
                    "Content-Type",
                    "text/html; charset=utf-8"
                )
                self.end_headers()
                self.wfile.write(template.read())

        except FileNotFoundError:
            self.send_error(404, "Page Not Found")

    # ================= RESPONSE =================
    def respond(self, msg):
        self.respond_html(
            "<!DOCTYPE html><html><head><meta charset='UTF-8'>"
            "<meta name='viewport' content='width=device-width, initial-scale=1.0'>"
            "<title>Railway Management System</title></head>"
            f"<body><h2>{html.escape(msg)}</h2>"
            "<p><a href='/'>Home</a></p></body></html>"
        )

    def respond_html(self, page):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(page.encode("utf-8"))


# ---------------- START SERVER ----------------
if __name__ == "__main__":
    print(f"🚆 Railway System Running at http://localhost:{PORT}")
    server = HTTPServer(("localhost", PORT), Handler)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.server_close()