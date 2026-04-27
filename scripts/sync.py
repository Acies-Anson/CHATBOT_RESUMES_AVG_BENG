import pyodbc
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
#env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
#load_dotenv(dotenv_path=env_path)

# ---------- SQL SERVER CONNECTION ----------
sql_conn = pyodbc.connect(
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={os.getenv('SQL_SERVER')};"
    f"DATABASE={os.getenv('SQL_DATABASE')};"
    f"UID={os.getenv('SQL_USER')};"
    f"PWD={os.getenv('SQL_PASSWORD')};"
)
sql_cursor = sql_conn.cursor()

# ---------- FETCH DATA ----------
sql_cursor.execute("SELECT name, email, phone_no, location, skills, experience, education FROM resumes")
rows = sql_cursor.fetchall()

# ---------- NEON CONNECTION ----------
pg_conn = psycopg2.connect(os.getenv("NEON_URL"))
pg_cursor = pg_conn.cursor()

# ---------- CLEAR OLD DATA ----------
pg_cursor.execute("DELETE FROM resumes")

# ---------- INSERT NEW DATA ----------
for row in rows:
    pg_cursor.execute(
        "INSERT INTO resumes (name, email, phone_no, location, skills, experience, education) VALUES (%s,%s,%s,%s,%s,%s,%s)",
        row
    )

pg_conn.commit()

# ---------- CLOSE ----------
sql_cursor.close()
sql_conn.close()
pg_cursor.close()
pg_conn.close()

print("Data synced successfully!")