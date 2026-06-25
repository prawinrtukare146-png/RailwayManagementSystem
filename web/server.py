from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse
import mysql.connector

PORT = 8000


# ---------------- DATABASE CONNECTION ----------------
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="REMOVED_SECRET",   # 🔴 CHANGE THIS
        database="railway_db"
    )


# ---------------- SERVER ----------------
class Handler(BaseHTTPRequestHandler):

    # ================= GET REQUEST =================
    def do_GET(self):

        if self.path == "/":
            self.path = "/templates/index.html"

        elif self.path == "/index.html":
            self.path = "/templates/index.html"

        elif self.path == "/book.html":
            self.path = "/templates/book.html"

        elif self.path == "/cancel.html":
            self.path = "/templates/cancel.html"

        elif self.path == "/trains":
            self.show_trains()
            return

        elif self.path == "/bookings":
            self.show_bookings()
            return

        elif self.path == "/location":
            self.show_location()
            return

        try:
            file_path = self.path[1:]
            file = open(file_path, "rb")

            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()

            self.wfile.write(file.read())
            file.close()

        except:
            self.send_error(404, "Page Not Found")


    # ================= POST REQUEST =================
    def do_POST(self):

        # ---------- BOOK ----------
        if self.path == "/book":

            length = int(self.headers['Content-Length'])
            data = self.rfile.read(length).decode()
            form = urllib.parse.parse_qs(data)

            name = form['name'][0]
            train_id = form['train_id'][0]

            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute(
                "SELECT available_seats FROM trains WHERE train_id=%s",
                (train_id,)
            )

            result = cursor.fetchone()

            if not result:
                self.respond("Train Not Found")
                return

            seats = result[0]

            if seats <= 0:
                self.respond("No Seats Available")
                return

            seat_number = seats

            cursor.execute(
                "INSERT INTO bookings (passenger_name, train_id, seat_number, status) VALUES (%s,%s,%s,%s)",
                (name, train_id, seat_number, "BOOKED")
            )

            cursor.execute(
                "UPDATE trains SET available_seats = available_seats - 1 WHERE train_id=%s",
                (train_id,)
            )

            conn.commit()
            conn.close()

            self.respond(f"Ticket Booked Successfully! Seat No: {seat_number}")


        # ---------- CANCEL ----------
        elif self.path == "/cancel":

            length = int(self.headers['Content-Length'])
            data = self.rfile.read(length).decode()
            form = urllib.parse.parse_qs(data)

            booking_id = form['booking_id'][0]

            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute(
                "SELECT train_id, seat_number FROM bookings WHERE booking_id=%s",
                (booking_id,)
            )

            result = cursor.fetchone()

            if not result:
                self.respond("Booking Not Found")
                return

            train_id, seat_number = result

            cursor.execute(
                "UPDATE bookings SET status='CANCELLED' WHERE booking_id=%s",
                (booking_id,)
            )

            cursor.execute(
                "UPDATE trains SET available_seats = available_seats + 1 WHERE train_id=%s",
                (train_id,)
            )

            conn.commit()
            conn.close()

            self.respond(f"Ticket Cancelled! Seat Released: {seat_number}")


    # ================= TRAIN LIST =================
    def show_trains(self):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM trains")
        rows = cursor.fetchall()

        html = """
        <html>
        <head>
            <title>Trains</title>
            <meta charset="UTF-8">
        </head>
        <body style="font-family:Arial;text-align:center;">

        <h1>🚆 Available Trains</h1>

        <table border="1" style="margin:auto;">
        <tr>
            <th>ID</th><th>Name</th><th>Source</th><th>Destination</th>
            <th>Departure</th><th>Arrival</th><th>Total Seats</th><th>Available Seats</th>
        </tr>
        """

        for r in rows:
            html += f"""
            <tr>
                <td>{r[0]}</td>
                <td>{r[1]}</td>
                <td>{r[2]}</td>
                <td>{r[3]}</td>
                <td>{r[4]}</td>
                <td>{r[5]}</td>
                <td>{r[6]}</td>
                <td>{r[7]}</td>
            </tr>
            """

        html += """
        </table>
        <br><a href="/">⬅ Home</a>
        </body>
        </html>
        """

        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

        conn.close()


    # ================= BOOKINGS =================
    def show_bookings(self):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM bookings")
        rows = cursor.fetchall()

        html = """
        <html>
        <head>
            <title>Bookings</title>
            <meta charset="UTF-8">
        </head>
        <body style="font-family:Arial;text-align:center;">

        <h1>📋 All Bookings</h1>

        <table border="1" style="margin:auto;">
        <tr>
            <th>ID</th><th>Name</th><th>Train ID</th><th>Seat</th><th>Status</th>
        </tr>
        """

        for r in rows:
            html += f"""
            <tr>
                <td>{r[0]}</td>
                <td>{r[1]}</td>
                <td>{r[2]}</td>
                <td>{r[3]}</td>
                <td>{r[4]}</td>
            </tr>
            """

        html += """
        </table>
        <br><a href="/">⬅ Home</a>
        </body>
        </html>
        """

        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

        conn.close()


    # ================= LOCATION =================
    def show_location(self):

        html = """
        <html>
        <head>
            <title>Track Location</title>
            <meta charset="UTF-8">
        </head>
        <body style="font-family:Arial;text-align:center;">

        <h1>📍 Train Location Tracking</h1>

        <p>Live tracking system (demo version)</p>

        <ul style="list-style:none;">
            <li>🚆 Train 101 → Running</li>
            <li>🚆 Train 102 → Arrived</li>
            <li>🚆 Train 103 → Delayed</li>
        </ul>

        <br><a href="/">⬅ Home</a>
        </body>
        </html>
        """

        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))


    # ================= RESPONSE =================
    def respond(self, message):
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(message.encode("utf-8"))


# ================= START SERVER =================
print("🚆 Railway System Running at http://localhost:8000")

httpd = HTTPServer(("localhost", PORT), Handler)
httpd.serve_forever()