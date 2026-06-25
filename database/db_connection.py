import mysql.connector

def get_connection():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="REMOVED_SECRET",
        database="railway_db"
    )
    return connection