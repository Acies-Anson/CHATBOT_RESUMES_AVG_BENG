# Database Setup Guide (Agent 2)

This guide helps contributors set up the project with a working SQL Server connection and correct `DB_URI`.

## 1. Prerequisites

- Python 3.10+
- SQL Server (Express / Developer / LocalDB)
- ODBC Driver for SQL Server (17 or 18)
- VS Code or terminal access

## 2. Project Setup

From project root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 3. Create Database and Table

Run in SSMS or `sqlcmd`:

```sql
IF DB_ID('Agent2DB') IS NULL
BEGIN
	CREATE DATABASE Agent2DB;
END;
GO

USE Agent2DB;
GO

IF OBJECT_ID('dbo.Orders', 'U') IS NULL
BEGIN
	CREATE TABLE dbo.Orders (
		order_id INT PRIMARY KEY,
		order_date DATE,
		customer_id VARCHAR(20) NULL,
		region VARCHAR(50) NULL,
		product VARCHAR(100) NULL,
		price FLOAT NULL,
		quantity FLOAT NULL
	);
END;
GO
```

Optional sample data:

```sql
USE Agent2DB;
GO

IF NOT EXISTS (SELECT 1 FROM dbo.Orders)
BEGIN
	INSERT INTO dbo.Orders (order_id, order_date, customer_id, region, product, price, quantity) VALUES
	(1, '2026-01-05', 'C001', 'North', 'Laptop', 1200, 2),
	(2, '2026-01-06', 'C002', 'West', 'Mouse', 25, 10),
	(3, '2026-01-07', 'C003', 'South', 'Keyboard', 45, 6),
	(4, '2026-01-08', 'C001', 'North', 'Monitor', 300, 3),
	(5, '2026-01-09', 'C004', 'East', 'Laptop', 1250, 1),
	(6, '2026-01-10', NULL, 'West', 'Desk', 200, 2),
	(7, '2026-01-11', 'C005', NULL, 'Chair', 150, 4),
	(8, '2026-01-12', 'C006', 'South', 'Mouse', NULL, 8),
	(9, '2026-01-13', 'C007', 'East', 'Keyboard', 50, NULL),
	(10, '2026-01-14', 'C008', 'North', 'Laptop', 1300, 2),
	(11, '2026-01-15', 'C009', 'West', 'Headset', 80, 5),
	(12, '2026-01-16', 'C010', 'South', 'Monitor', 280, 2);
END;
GO
```

## 4. Configure `.env`

Create `.env` in project root and set:

```env
DB_URI=...
OPENROUTER_API_KEY=...
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=...
# Optional:
# LANGSMITH_PROJECT=agent2
# LANGSMITH_ENDPOINT=https://api.smith.langchain.com
```

## 5. DB_URI Formats

Use one of these formats based on your SQL Server setup.

### A) SQL Authentication

```env
DB_URI=mssql+pyodbc://username:password@localhost/Agent2DB?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes
```

### B) Windows Authentication

```env
DB_URI=mssql+pyodbc://@localhost/Agent2DB?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes&TrustServerCertificate=yes
```

### C) LocalDB or Named Instance (recommended `odbc_connect`)

```env
DB_URI=mssql+pyodbc:///?odbc_connect=DRIVER%3D%7BODBC+Driver+17+for+SQL+Server%7D%3BSERVER%3D%28localdb%29%5CMSSQLLocalDB%3BDATABASE%3DAgent2DB%3BTrusted_Connection%3Dyes%3BTrustServerCertificate%3Dyes%3B
```

If you use Driver 18, replace `ODBC+Driver+17+for+SQL+Server` with `ODBC+Driver+18+for+SQL+Server`.

## 6. Verify DB Connection

Run this command from project root:

```powershell
.\.venv\Scripts\python.exe -c "import os; from dotenv import load_dotenv; from sqlalchemy import create_engine, text; load_dotenv(); e=create_engine(os.getenv('DB_URI')); c=e.connect(); r=c.execute(text('SELECT @@SERVERNAME AS s, DB_NAME() AS d')).mappings().first(); print(r); c.close()"
```

Expected output includes your server name and `Agent2DB`.

## 7. Run Harness

```powershell
.\.venv\Scripts\python.exe tests\test_harness.py
```

Expected:

- `PRECHECK` with `DB=Connected ...`
- SQL validation and execution test output
- LLM summary output or deterministic fallback

## 8. Common DB_URI Errors

### `DB_URI is missing`

- Ensure `.env` exists in project root
- Ensure key name is exactly `DB_URI`

### `Login failed for user`

- Verify username/password
- Ensure SQL auth is enabled (if using SQL auth)

### `Data source name not found` or driver missing

- Install ODBC Driver 17 or 18
- Ensure driver name matches exactly in `DB_URI`

### Cannot connect to server/instance

- Check SQL Server service is running
- Verify instance name
- Prefer `odbc_connect` for named instances/LocalDB

## 9. Contributor Quick Checklist

1. Activate `.venv`
2. Install requirements
3. Configure `.env` with valid `DB_URI` and `OPENROUTER_API_KEY`
4. Verify DB connection command
5. Run `tests/test_harness.py`

When all pass, the environment is ready.
