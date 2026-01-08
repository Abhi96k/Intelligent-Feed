# Tellius Intelligent Feed - Quick Start

## ⚡ 60-Second Setup

### Step 1: Start the System
```bash
cd /Users/abhishek/Desktop/Hackthon
./START.sh
```

That's it! The script will:
- ✅ Check prerequisites
- ✅ Set up Python virtual environment
- ✅ Install dependencies
- ✅ Initialize database
- ✅ Start backend (port 8000)
- ✅ Start frontend (port 3000)

### Step 2: Open Browser
Navigate to: **http://localhost:3000**

### Step 3: Ask a Question
Try: `Why did revenue in APAC drop in the last 8 weeks vs previous period?`

Click **Run Analysis** and wait ~10 seconds.

---

## 🎯 Example Questions

Copy-paste these into the UI:

1. **Regional Analysis** (Absolute detection):
   ```
   Why did revenue in APAC drop in the last 8 weeks vs previous period?
   ```

2. **Segment Performance** (Absolute detection):
   ```
   What caused the revenue spike in Enterprise segment last month?
   ```

3. **Anomaly Detection** (ARIMA):
   ```
   Show me anomalies in revenue for Q4 2024
   ```

4. **Time Comparison** (Not triggered):
   ```
   What happened to profit in November vs October 2024?
   ```

---

## 📊 Understanding Results

### If Triggered (Alert-Worthy)
You'll see:
- ✅ Green "Triggered" badge
- ✅ Trigger reason (e.g., "20% decrease")
- ✅ "What happened" summary
- ✅ "Why it happened" explanation with drivers
- ✅ Trend chart (line chart)
- ✅ Driver impact chart (bar chart)
- ✅ Confidence score (0-100%)

### If Not Triggered
You'll see:
- ⭕ Gray "Not Triggered" badge
- ⭕ Explanation (e.g., "Change is 2.3%, below 5% threshold")
- ⭕ Suggestion for next steps
- ⭕ Current metrics

---

## 🛠️ Manual Setup (if START.sh fails)

### Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env: add ANTHROPIC_API_KEY
python scripts/init_database.py
python -m app.main
```

### Frontend (in separate terminal)
```bash
cd frontend
npm install
npm run dev
```

---

## 🔍 Troubleshooting

### Backend won't start
```bash
# Check if port 8000 is available
lsof -ti:8000 | xargs kill -9

# Check API key
cat backend/.env | grep ANTHROPIC_API_KEY
```

### Frontend won't start
```bash
# Check if port 3000 is available
lsof -ti:3000 | xargs kill -9

# Reinstall dependencies
cd frontend
rm -rf node_modules
npm install
```

### Database issues
```bash
cd backend
rm tellius_feed.db
python scripts/init_database.py
```

### API calls failing
Check backend logs:
```bash
tail -f /tmp/tellius_backend.log
```

---

## 📱 API Testing (Optional)

### Health Check
```bash
curl http://localhost:8000/api/health
```

### Generate Insight
```bash
curl -X POST http://localhost:8000/api/insight \
  -H "Content-Type: application/json" \
  -d '{"user_question": "Why did revenue drop in APAC?"}'
```

### View API Documentation
Open: http://localhost:8000/docs

---

## 🎓 Next Steps

1. **Try all example questions** to see different detection modes
2. **Review DEMO.md** for detailed walkthrough
3. **Read ARCHITECTURE.md** to understand system design
4. **Check PROJECT_SUMMARY.md** for complete overview
5. **Modify sample data** in `backend/app/utils/mock_data_generator.py`

---

## 📞 Quick Reference

| Resource | URL/Path |
|----------|----------|
| Frontend | http://localhost:3000 |
| Backend | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Backend Logs | /tmp/tellius_backend.log |
| Frontend Logs | /tmp/tellius_frontend.log |
| Database | backend/tellius_feed.db |
| Config | backend/.env |

---

## 🎬 Demo Mode

For live demos:
1. Pre-load frontend before presentation
2. Have example questions ready to copy-paste
3. Highlight confidence scores and charts
4. Show both triggered and not-triggered scenarios
5. Point out response time (< 15 seconds)

---

## ⚡ Power User Tips

### Custom Thresholds
```
Why did revenue drop by more than 10% in APAC last month?
```
(System will use 10% instead of default 5%)

### Multiple Filters
```
Why did revenue in APAC for Enterprise segment drop last quarter?
```
(Filters by both region and segment)

### Time Expressions
- "last 8 weeks"
- "Q4 2024"
- "November 2024"
- "past 3 months"
- "year to date"

### Feed Types
- Mention "anomaly/anomalies/unusual" → ARIMA mode
- Mention "drop/increase/change" → Absolute mode
- Default: Absolute

---

**Total Setup Time**: < 2 minutes
**First Insight**: < 15 seconds
**Learn the System**: < 30 minutes

🚀 **You're ready to go!**
