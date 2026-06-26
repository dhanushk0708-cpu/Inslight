# DASH.AI — AI Business Intelligence Co-Pilot

DASH.AI is an **AI-powered Business Intelligence assistant** that allows users to explore and analyze data using **natural language instead of SQL or complex BI tools**.

Users can upload a dataset and simply ask questions like:

> "Show revenue by region"
> "Top 5 products by profit"
> "Monthly sales trends"

The system automatically:

* Converts the question into SQL
* Retrieves relevant data
* Generates interactive dashboards
* Provides AI-generated business insights

---

# 🚀 Key Features

### Natural Language Data Queries

Ask questions in plain English and the system automatically generates SQL queries.

### Automatic Dashboard Generation

DASH.AI dynamically generates:

* KPI Cards
* Charts
* Visual dashboards

### AI Executive Insights

The system analyzes results and produces concise business insights to support decision making.

### CSV Upload Support

Upload any structured CSV dataset and instantly explore it through natural language.

### Voice Query Support

Users can ask questions using voice through browser speech recognition.

### Deep Dive Analysis

Advanced analysis that identifies:

* Top profit drivers
* Loss risk areas
* Business recommendations

### What-If Scenario Simulator

Simulate business scenarios such as:

* Price increase
* Cost changes
* Unit growth

The system calculates projected profit and business impact.

### Anomaly Detection

Automatically detects unusual patterns such as:

* Sudden revenue drops
* Abnormal profit spikes
* Statistical outliers

---

# 🧠 How It Works

The system follows an **AI-driven analytics pipeline**:

1. User asks a question
2. The AI model converts the question into SQL
3. SQL is executed on the dataset
4. Results are analyzed
5. Interactive dashboards and insights are generated

Example:

User Query:

```
Show revenue by region
```

Generated SQL:

```
SELECT region, SUM(revenue) AS total_revenue
FROM sales_data
GROUP BY region
ORDER BY total_revenue DESC
```

---

# 🏗 System Architecture

```
User
  │
  ▼
Frontend (Next.js + React)
  │
  ▼
FastAPI Backend
  │
  ▼
LLM (Groq Llama-3)
  │
  ▼
SQL Generation
  │
  ▼
SQLite Database
  │
  ▼
Pandas Data Processing
  │
  ▼
Charts + AI Insights
```

---

# 🛠 Technology Stack

### Frontend

* Next.js
* React
* TailwindCSS
* Recharts
* Lucide Icons

### Backend

* FastAPI
* Python
* Pandas
* SQLite

### AI

* Groq API
* Llama-3 Large Language Model

---

# 📂 Project Structure

```
Insight/
│
├── backend/
│   ├── data/
│   ├── main.py
│   └── requirements.txt
│
├── frontend/
│   ├── src/app/
│   │   ├── globals.css
│   │   ├── layout.tsx
│   │   └── page.tsx
│   │
│   ├── next.config.js
│   ├── package.json
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── postcss.config.js
│
├── README.md
└── .gitignore
```

---

# ⚙️ Installation & Setup

## 1. Clone Repository

```
git clone https://github.com//dash-ai.git
cd dash-ai
```

---

## 2. Setup Backend

```
cd backend

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt
```

Create `.env` file:

```
GROQ_API_KEY=your_groq_api_key
```

Run backend:

```
uvicorn main:app --reload
```

Backend runs at:

```
http://localhost:8000
```

---

## 3. Setup Frontend

```
cd frontend

npm install
npm run dev
```

Frontend runs at:

```
http://localhost:3000
```

---

# 📊 Example Use Cases

Business teams can ask:

* Show revenue by region
* Top products by profit
* Monthly revenue trends
* Compare categories by sales
* Detect anomalies in sales data

---

# 🔒 Safety Features

The system prevents unsafe database operations:

* Only SELECT queries allowed
* Dangerous commands blocked
* SQL validation layer
* Retry mechanism for failed queries

---

# 🔮 Future Improvements

Planned upgrades include:

* Integration with enterprise databases (PostgreSQL, Snowflake)
* Real-time streaming analytics
* Predictive forecasting models
* Multi-dataset analysis
* Role-based dashboards

---

# 💡 Why DASH.AI?

Traditional BI tools require technical expertise.

DASH.AI enables **anyone to explore data through conversation**, making analytics accessible to managers, founders, and business teams.

---

# 🏆 Hackathon Project

This project was built as part of a hackathon to demonstrate how **AI can transform business analytics into a conversational experience**.

---

# 👨‍💻 Author

Dhanush Team
Dhanush k
MOhan D
saif Ali Khan
BCA (AI Specialization)

---

# ⭐ If you like this project

Give the repository a star!
