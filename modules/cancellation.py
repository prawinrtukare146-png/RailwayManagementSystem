from database.db_connection import get_connection

def cancel_ticket():

    conn = get_connection()
    cursor = conn.cursor()

    booking_id = input("Enter Booking ID to Cancel: ")

    # Get booking details
    cursor.execute("SELECT train_id, seat_number, status FROM bookings WHERE booking_id=%s", (booking_id,))
    booking = cursor.fetchone()

    if not booking:
        print("Booking not found")
        return

    train_id = booking[0]
    seat_number = booking[1]
    status = booking[2]

    if status == "CANCELLED":
        print("Ticket already cancelled")
        return

    # Update booking status
    cursor.execute(
        "UPDATE bookings SET status='CANCELLED' WHERE booking_id=%s",
        (booking_id,)
    )

    # Restore seat in trains table
    cursor.execute(
        "UPDATE trains SET available_seats = available_seats + 1 WHERE train_id=%s",
        (train_id,)
    )

    conn.commit()

    print("\nTicket Cancelled Successfully!")
    print("Seat Released:", seat_number)

    conn.close()