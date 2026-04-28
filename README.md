# CHATBOT_RESUMES_AVG_BENG

An AI-powered chatbot system that processes natural language queries, converts them into SQL, retrieves relevant candidate data from a PostgreSQL (Neon) database, and generates meaningful summaries.

---

## Overview

This project implements a resume search and summarization system that:

- Converts user queries into SQL using an LLM  
- Retrieves candidate data from a database  
- Generates structured, human-readable summaries  
- Provides preview results for quick inspection  

---

## Key Features

- Natural Language to SQL Conversion  
- PostgreSQL (Neon) Database Integration  
- Dynamic Result Summarization  
- Fallback Query Handling for robustness  
- Real-time Query Execution  
- Structured JSON Output  

---

## Project Architecture
User Query -> SQL Agent (generate_sql) -> SQL Cleaning & Validation -> PostgreSQL (Neon DB) -> Result Fetching -> Summarization Agent -> Final JSON Response

---

## Project Structure

```text
CHATBOT_RESUMES_AVG_BENG/
└── CHATBOT_RESUMES_AVG_BENG/
    ├── PDF2CSV/
    │   ├── data/
    │   │   ├── Given_data/                 # Raw PDFs
    │   │   ├── Extracted_json/             # Parsed JSON results
    │   │   └── Extracted_text/             # Raw text from PDFs
    │   ├── scripts/
    │   │   ├── pdf2text.py
    │   │   ├── text2json.py
    │   │   └── json2csv.py
    │   └── testing/
    │       ├── test_count.py               # Missing file auditor
    │       └── text2json_failedfiles.py    # Error handling
    ├── agents/
    │   ├── retrieval_summarizer_agent.py  # Query → SQL → Summary pipeline
    │   └── sql_agent.py                   # SQL generation & validation
    ├── script.py                          # Main entry point
    ├── requirements.txt                   # Dependencies
    ├── pyproject.toml                     # Project config
    └── README.md
```
---

## Tech Stack

- Python  
- PostgreSQL (Neon DB)  
- psycopg2  
- LLM-based SQL Generation  
- Regular Expressions (for SQL cleaning)  

---

## Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/Acies-Anson/CHATBOT_RESUMES_AVG_BENG.git
cd CHATBOT_RESUMES_AVG_BENG
```

### 2. Create a Virtual Environment
```bash
python -m venv venv
```

### 3. Activate the environment:
### - Windows
```bash
venv\Scripts\activate
```
### - Mac/Linux
```bash
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables
```env
NEON_URL=your_neon_connection_string
```

### 6. Ensure Database Setup
```SQL
CREATE TABLE cleaned_data (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200),
    email VARCHAR(200),
    phone_no VARCHAR(200),
    location VARCHAR(200),
    skills TEXT,
    experience TEXT,
    occupation VARCHAR(200),
    education TEXT,
    email_valid BOOLEAN,
    phone_valid BOOLEAN,
    other_details TEXT
);
```

### 7. Run the Application
```bash
python script.py
```
