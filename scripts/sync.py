import pyodbc
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

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
sql_cursor.execute("""
SELECT 
    occupation, 
    name, 
    email, 
    phone_no, 
    location, 
    skills, 
    experience, 
    education, 
    other_details, 
    email_valid, 
    phone_valid 
FROM cleaned_data
""")

rows = sql_cursor.fetchall()
print("Total rows fetched:", len(rows))

# ---------- NEON CONNECTION ----------
pg_conn = psycopg2.connect(
    os.getenv("NEON_URL"),
    sslmode='require',
    connect_timeout=10
)
pg_cursor = pg_conn.cursor()

# ---------- CLEAR OLD DATA ----------
pg_cursor.execute("TRUNCATE TABLE cleaned_data RESTART IDENTITY")

# ---------- INSERT NEW DATA (BATCH INSERT) ----------
batch_size = 100

for i in range(0, len(rows), batch_size):
    batch = rows[i:i + batch_size]

    pg_cursor.executemany(
        """
        INSERT INTO cleaned_data 
        (occupation, name, email, phone_no, location, skills, experience, education, other_details, email_valid, phone_valid) 
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """,
        [
            (
                r[0], r[1], r[2], r[3], r[4],
                r[5], r[6], r[7], r[8], r[9], r[10]
            )
            for r in batch
        ]
    )

    pg_conn.commit()
    print(f"Inserted batch {i // batch_size + 1}")

# ---------- CLOSE ----------
sql_cursor.close()
sql_conn.close()
pg_cursor.close()
pg_conn.close()

print("✅ Data synced successfully!")