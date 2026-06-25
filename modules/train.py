from database.db_connection import get_connection

def view_trains():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM trains")
    trains = cursor.fetchall()

    print("\n===== AVAILABLE TRAINS =====\n")

    for t in trains:
        print("ID:", t[0])
        print("Name:", t[1])
        print("Source:", t[2])
        print("Destination:", t[3])
        print("Departure:", t[4])
        print("Arrival:", t[5])
        print("Total Seats:", t[6])
        print("Available Seats:", t[7])
        print("---------------------------")

    conn.close()