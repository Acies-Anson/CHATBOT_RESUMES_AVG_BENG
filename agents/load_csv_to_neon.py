import os
import csv
from pathlib import Path
from dotenv import load_dotenv
import psycopg2

env_path = Path(__file__).resolve().parent.parent / "agents" / ".env"
load_dotenv(env_path)

NEON_URL = os.getenv("NEON_URL")
if not NEON_URL:
    raise SystemExit("NEON_URL not set in agents/.env")

CSV_PATH = (os.getenv("CSV_PATH") or "data.csv").strip().strip('"').strip("'")

BATCH_SIZE = int(os.getenv("CSV_BATCH_SIZE", "500"))

INSERT_SQL = """
INSERT INTO cleaned_data 
(occupation, name, email, phone_no, location, skills, experience, education, other_details, email_valid, phone_valid)
VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
"""


def iter_csv_rows(path):
    def _to_bool(value):
        text = str(value).strip().lower()
        if text in {"true", "1", "yes", "y"}:
            return True
        if text in {"false", "0", "no", "n"}:
            return False
        return None

    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Map CSV columns to table columns. Adjust keys if your CSV has different headers.
            yield (
                row.get('occupation'),
                row.get('name'),
                row.get('email'),
                row.get('phone_no') or row.get('phone'),
                row.get('location'),
                row.get('skills'),
                row.get('experience'),
                row.get('education'),
                row.get('other_details'),
                _to_bool(row.get('email_valid')),
                _to_bool(row.get('phone_valid')),
            )


def main():
    csv_path = Path(CSV_PATH)
    if not csv_path.exists():
        raise SystemExit(f"CSV file not found: {csv_path}")

    conn = psycopg2.connect(NEON_URL, sslmode='require')
    cur = conn.cursor()

    batch = []
    total = 0
    for r in iter_csv_rows(csv_path):
        batch.append(r)
        if len(batch) >= BATCH_SIZE:
            cur.executemany(INSERT_SQL, batch)
            conn.commit()
            total += len(batch)
            print(f"Inserted {total} rows...")
            batch = []

    if batch:
        cur.executemany(INSERT_SQL, batch)
        conn.commit()
        total += len(batch)
        print(f"Inserted {total} rows (final)")

    cur.close()
    conn.close()
    print("CSV upload complete")


if __name__ == '__main__':
    main()
