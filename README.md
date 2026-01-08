# Tellius Intelligent Feed / Deep Insight System

> Next-generation question-driven analytics system with AI-powered deep root-cause analysis

## 🎯 Overview

This project represents a complete redesign of the Tellius Feed feature, transforming it from a configuration-driven alerting system into an **intelligent, question-driven insight engine** with deep explainability.

### Key Innovation

**Before**: "Configure a feed to alert when Revenue > threshold"
**After**: "Why did revenue in APAC drop in the last 8 weeks?"

The system automatically:
- ✅ Determines what happened and why
- ✅ Performs deep root-cause analysis
- ✅ Generates visual evidence (charts)
- ✅ Produces explainable narratives
- ✅ Detects alert-worthy changes

## 🏗️ Architecture

```
User Question
     ↓
Question Parser (LLM) → ParsedIntent
     ↓
TQL Planner → SQL Queries
     ↓
Plan Validator → Security Check
     ↓
TQL Adapter → Execute on SQLite
     ↓
Detection Engine (Absolute/ARIMA) → Triggered?
     ↓
[If Triggered]
     ↓
Deep Insight Engine → Root Cause Analysis
     ↓
Chart Builder → Visual Evidence
     ↓
Narrative Generator (LLM) → Human Explanation
     ↓
Insight Response
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Anthropic API key

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Initialize database
python scripts/init_database.py

# Run backend
python -m app.main
```

Backend runs on **http://localhost:8000**

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run frontend
npm run dev
```

Frontend runs on **http://localhost:3000**

### 3. Test the System

Open **http://localhost:3000** and try these questions:

1. `Why did revenue in APAC drop in the last 8 weeks vs previous period?`
2. `Show me anomalies in revenue for Q4 2024`
3. `What caused the revenue spike in Enterprise segment last month?`

## 📁 Project Structure

```
Hackthon/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Configuration & logging
│   │   ├── models/         # Data contracts
│   │   ├── services/       # Core business logic
│   │   │   ├── bv_context_builder.py
│   │   │   ├── question_parser.py
│   │   │   ├── tql_planner.py
│   │   │   ├── plan_validator.py
│   │   │   ├── tql_adapter.py
│   │   │   ├── detection_engine.py
│   │   │   ├── deep_insight_engine.py
│   │   │   ├── chart_builder.py
│   │   │   ├── narrative_generator.py
│   │   │   └── orchestrator.py
│   │   ├── utils/          # Utilities & sample data
│   │   └── main.py         # FastAPI app
│   ├── tests/              # Test suites
│   ├── scripts/            # Setup scripts
│   └── requirements.txt
│
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── services/       # API client
│   │   ├── hooks/          # Custom hooks
│   │   ├── utils/          # Utilities
│   │   └── App.jsx
│   ├── public/
│   └── package.json
│
├── ARCHITECTURE.md         # System architecture
└── README.md              # This file
```

## 🎨 Key Features

### 1. Question-Driven Interface
- Single natural language input
- No separate UI controls for time, filters, baselines
- Automatic intent extraction via LLM

### 2. Dual Detection Modes

**Absolute Detection** (Threshold-based)
- Compare current vs baseline
- Trigger on % change or absolute delta
- Default 5% threshold

**ARIMA Detection** (Anomaly-based)
- Fit ARIMA model to time-series
- Detect statistical anomalies
- Compute residuals and outliers

### 3. Deep Root-Cause Analysis
- Contribution-shift analysis
- Driver ranking by impact
- Multi-dimensional breakdown
- Explainability scoring (0-100)

### 4. Visual Evidence Generation
- **Primary Trend Chart**: Line chart with current/baseline periods
- **Driver Impact Chart**: Bar chart of top contributors
- **Contribution Comparison**: Current vs baseline breakdown

### 5. AI-Augmented Narratives
- LLM-generated explanations
- Grounded in computed evidence
- "What happened" + "Why it happened"
- Tellius Feed tone and style

## 🔧 Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLite** - Mock TQL service
- **Pandas** - Data processing
- **statsmodels** - ARIMA implementation
- **Anthropic Claude** - LLM for parsing & narration
- **Pydantic** - Data validation
- **structlog** - Structured logging

### Frontend
- **React 18** - UI framework
- **Vite** - Build tool
- **Recharts** - Chart library
- **Tailwind CSS** - Styling
- **React Query** - State management
- **Axios** - HTTP client

## 📊 Sample Data

The system includes a pre-populated E-commerce Sales dataset:

**Schema**:
- `sales_fact` - Transaction-level sales
- `date_dim` - Date dimension (2023-2024)
- `product_dim` - Products (Electronics, Furniture, Office Supplies)
- `customer_dim` - Customers (Enterprise, SMB, Consumer)
- `region_dim` - Regions (North America, Europe, APAC, Latin America)

**Measures**:
- Revenue, Quantity, Cost, Profit, Order_Count, Customer_Count

**Pre-built Patterns**:
- APAC revenue drops 20% in last 8 weeks of 2024
- Enterprise segment spikes 40% in November 2024

## 🔐 Security & Governance

### SQL Security
- ✅ Parameterized queries
- ✅ Column whitelist validation
- ✅ No dynamic SQL from user input
- ✅ SQL injection prevention

### LLM Safety
- ✅ LLM used only for parsing & narration
- ✅ No LLM-generated SQL execution without validation
- ✅ All metrics computed deterministically

### Python Sandbox
- ✅ RestrictedPython for ARIMA
- ✅ No file system access
- ✅ No network access
- ✅ CPU and memory limits

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest tests/
```

### Frontend Tests
```bash
cd frontend
npm test
```

## 📚 API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Main Endpoint

**POST** `/api/insight`

**Request**:
```json
{
  "user_question": "Why did revenue in APAC drop in the last 8 weeks vs previous period?"
}
```

**Response** (Triggered):
```json
{
  "triggered": true,
  "trigger_reason": "Revenue decreased by 15.3% (threshold: 5%)",
  "what_happened": "Revenue in APAC declined from $2.4M to $2.0M over the last 8 weeks",
  "why_happened": "The decline was primarily driven by a 23% drop in Enterprise segment sales...",
  "charts": [...],
  "confidence": 87.5,
  "evidence": {...}
}
```

**Response** (Not Triggered):
```json
{
  "triggered": false,
  "explanation": "Revenue changed by 2.3%, below the 5% threshold",
  "suggestion": "Consider lowering the threshold or checking a different time period."
}
```

## 🎓 Example Questions

Try these questions to see the system in action:

1. **Threshold-based Analysis**:
   - "Why did revenue in APAC drop in the last 8 weeks vs previous period?"
   - "What caused profit to increase by more than 10% in November?"

2. **Anomaly Detection**:
   - "Show me anomalies in revenue for Q4 2024"
   - "Find unusual patterns in Order_Count for the past 3 months"

3. **Segment Analysis**:
   - "What drove the revenue spike in Enterprise segment last month?"
   - "Why did sales decrease in the Electronics category?"

4. **Time Comparisons**:
   - "Compare revenue in Q4 2024 vs Q4 2023"
   - "Show me Customer_Count trends for the past 6 months"

## 📈 Performance

- Question parsing: < 2s
- TQL execution: < 5s
- ARIMA detection: < 10s
- **Total end-to-end: < 15s**

Supports up to 1M rows in time-series analysis.

## 🔮 Future Enhancements

1. **Alert Workflows**
   - Subscribe to questions
   - Scheduled periodic checks
   - Notification channels (email, Slack)

2. **Multi-Metric Analysis**
   - Analyze correlated metrics
   - Cross-metric root-cause analysis

3. **Predictive Insights**
   - Forecast future trends
   - "What-if" scenario analysis

4. **Tellius Feed Integration**
   - Backward compatibility layer
   - Migration from existing feeds
   - Gradual rollout

## 👥 Team

Built by senior staff engineers for Tellius hackathon.

## 📄 License

Proprietary - Tellius Internal

## 🙏 Acknowledgments

- Anthropic Claude for LLM capabilities
- Tellius Business View architecture
- TQL query framework
- React and FastAPI communities

---

**Status**: ✅ Production-ready prototype
**Version**: 1.0.0
**Last Updated**: January 2026
