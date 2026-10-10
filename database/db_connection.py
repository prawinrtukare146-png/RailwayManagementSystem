import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    connection = mysql.connector.connect(
        host="localhost",
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD"),
        database="railway_db"
    )
    return connection