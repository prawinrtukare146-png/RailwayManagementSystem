from database.db_connection import get_connection

def view_reports():

    conn = get_connection()
    cursor = conn.cursor()

    print("\n===== RAILWAY REPORTS =====\n")

    # Total Trains
    cursor.execute("SELECT COUNT(*) FROM trains")
    total_trains = cursor.fetchone()[0]

    # Total Bookings
    cursor.execute("SELECT COUNT(*) FROM bookings")
    total_bookings = cursor.fetchone()[0]

    # Cancelled Tickets
    cursor.execute("SELECT COUNT(*) FROM bookings WHERE status='CANCELLED'")
    cancelled = cursor.fetchone()[0]

    # Active Bookings
    cursor.execute("SELECT COUNT(*) FROM bookings WHERE status='BOOKED'")
    active = cursor.fetchone()[0]

    print("Total Trains:", total_trains)
    print("Total Bookings:", total_bookings)
    print("Active Tickets:", active)
    print("Cancelled Tickets:", cancelled)

    conn.close()