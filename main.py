from modules.train import view_trains
from modules.booking import book_ticket
from modules.cancellation import cancel_ticket
from modules.location import update_location, view_location
from modules.reports import view_reports

while True:

    print("\n==============================")
    print("  RAILWAY MANAGEMENT SYSTEM   ")
    print("==============================")

    print("1. View Trains")
    print("2. Book Ticket")
    print("3. Cancel Ticket")
    print("4. Update Train Location")
    print("5. View Train Location")
    print("6. View Reports")
    print("7. Exit")

    choice = input("Enter choice: ")

    if choice == "1":
        view_trains()

    elif choice == "2":
        book_ticket()

    elif choice == "3":
        cancel_ticket()

    elif choice == "4":
        update_location()

    elif choice == "5":
        view_location()

    elif choice == "6":
        view_reports()

    elif choice == "7":
        print("Thank you!")
        break

    else:
        print("Invalid choice")