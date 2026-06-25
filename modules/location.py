from database.db_connection import get_connection
import datetime

def update_location():

    conn = get_connection()
    cursor = conn.cursor()

    train_id = input("Enter Train ID: ")
    station = input("Enter Current Station: ")

    time_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        "INSERT INTO locations (train_id, current_station, updated_time) VALUES (%s, %s, %s)",
        (train_id, station, time_now)
    )

    conn.commit()

    print("\nLocation Updated Successfully!")
    print("Train:", train_id)
    print("Station:", station)

    conn.close()


def view_location():

    conn = get_connection()
    cursor = conn.cursor()

    train_id = input("Enter Train ID: ")

    cursor.execute(
        "SELECT current_station, updated_time FROM locations WHERE train_id=%s ORDER BY location_id DESC LIMIT 1",
        (train_id,)
    )

    result = cursor.fetchone()

    if not result:
        print("No location data found")
        return

    print("\n===== TRAIN LOCATION =====")
    print("Current Station:", result[0])
    print("Last Updated:", result[1])

    conn.close()