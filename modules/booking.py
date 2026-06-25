from database.db_connection import get_connection

def book_ticket():

    conn = get_connection()
    cursor = conn.cursor()

    train_id = input("Enter Train ID: ")
    passenger_name = input("Enter Passenger Name: ")

    # Check available seats
    cursor.execute("SELECT available_seats, total_seats FROM trains WHERE train_id=%s", (train_id,))
    result = cursor.fetchone()

    if not result:
        print("Train not found")
        return

    available_seats = result[0]
    total_seats = result[1]

    if available_seats <= 0:
        print("No seats available")
        return

    # Generate seat number
    seat_number = total_seats - available_seats + 1

    # Insert booking
    cursor.execute(
        "INSERT INTO bookings (passenger_name, train_id, seat_number, status) VALUES (%s, %s, %s, %s)",
        (passenger_name, train_id, seat_number, "BOOKED")
    )

    # Update seats
    cursor.execute(
        "UPDATE trains SET available_seats = available_seats - 1 WHERE train_id=%s",
        (train_id,)
    )

    conn.commit()

    print("\nTicket Booked Successfully!")
    print("Seat Number:", seat_number)

    conn.close()