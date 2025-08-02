# 💸 SpendWise

SpendWise is a GenAI-powered personal finance assistant that helps you track, categorize, and analyze your spending by uploading your credit/debit card statements as PDFs.

---

## 🚀 Features

- User authentication (JWT)
- Upload debit or credit bank statements as PDF
- LLM extracts and categorizes transactions
- Auto-generated financial insights
- Accept LLM suggestions as budgets
- Creates user spending profile
- Provides insights and suggestions on budget spending compatibility of users

---

## 🛠️ Tech Stack

- **Backend**: FastAPI, PostgreSQL, SQLAlchemy
- **LLM Integration**: OpenAI GPT-4
- **Auth**: JWT (with OAuth2 scheme)
- **Migrations**: Alembic
- **Testing**: Pytest

---

## Setup Instructions

### 1. Clone the Repo
```bash
git clone https://github.com/yourusername/spendwise.git
cd spendwise

### 2. Create Virtual Environment
python -m venv sw_venv
source sw_venv/bin/activate  # macOS/Linux
sw_venv\Scripts\activate     # Windows

### 3. Install Requirements
pip install -r requirements.txt

### 4. Set Up Environment Variables
DATABASE_URL=postgresql://postgres:password@localhost:5432/spendwise
SECRET_KEY=your-secret-key

### 5. Run Migrations
Make sure to start PostgreSQL (e.g., via Postgres.app)
Ensure that the .env contains a valid DATABASE_URL
alembic upgrade head

### 6. Start the Server
uvicorn app.main:app --reload

### Run Tests
pytest
