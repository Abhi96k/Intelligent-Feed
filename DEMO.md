# Tellius Intelligent Feed - Demo Guide

## 🎬 Demo Scenario

This guide walks through a complete demonstration of the Intelligent Feed system, showcasing its ability to transform natural language questions into deep, actionable insights.

## 📋 Prerequisites

Before starting the demo, ensure:
- ✅ Backend is running on http://localhost:8000
- ✅ Frontend is running on http://localhost:3000
- ✅ Database is initialized with sample data
- ✅ Anthropic API key is configured

## 🚀 Quick Setup

```bash
# Terminal 1: Start Backend
cd backend
source venv/bin/activate
python scripts/init_database.py  # If not already done
python -m app.main

# Terminal 2: Start Frontend
cd frontend
npm install  # If not already done
npm run dev
```

Open **http://localhost:3000** in your browser.

## 🎯 Demo Flow

### Part 1: Threshold-Based Detection (Absolute)

#### Question 1: Regional Revenue Drop

**Ask**: `Why did revenue in APAC drop in the last 8 weeks vs previous period?`

**What the System Does**:
1. ✅ Parses question → extracts: metric=Revenue, region=APAC, time=last 8 weeks, baseline=previous period
2. ✅ Generates SQL queries with proper JOINs
3. ✅ Validates queries for security
4. ✅ Executes against database
5. ✅ Detects 20% drop (exceeds 5% threshold) ✅ **TRIGGERED**
6. ✅ Performs contribution-shift analysis across dimensions
7. ✅ Identifies top drivers (e.g., Enterprise segment drop, Product category changes)
8. ✅ Generates trend chart and driver impact chart
9. ✅ Creates narrative: "Revenue in APAC declined from $X to $Y over the last 8 weeks. The decline was primarily driven by a 23% drop in Enterprise segment sales ($-350K impact)..."

**Expected Output**:
```json
{
  "triggered": true,
  "trigger_reason": "Revenue decreased by 20.3%",
  "what_happened": "Revenue in APAC declined from $2.4M to $2.0M",
  "why_happened": "Primary driver: Enterprise segment drop (-23%, $-350K impact)...",
  "charts": [
    {"type": "line", "title": "Revenue Over Time", ...},
    {"type": "bar", "title": "Top Contributing Drivers", ...}
  ],
  "confidence": 87.5
}
```

**Key Points to Highlight**:
- 🎯 Single question contains ALL parameters (no UI knobs)
- 🎯 Automatic baseline calculation (previous 8 weeks)
- 🎯 Deep RCA identifies specific segment/product impacts
- 🎯 Visual evidence supports the insight
- 🎯 Explainability score (87.5%) shows high confidence

---

#### Question 2: Segment Performance Spike

**Ask**: `What caused the revenue spike in Enterprise segment last month?`

**What the System Does**:
1. ✅ Parses: metric=Revenue, segment=Enterprise, time=last month
2. ✅ Infers baseline (previous month)
3. ✅ Detects 40% increase ✅ **TRIGGERED**
4. ✅ Analyzes by product categories and regions
5. ✅ Identifies Electronics category as primary driver
6. ✅ Generates charts and narrative

**Expected Output**:
```json
{
  "triggered": true,
  "trigger_reason": "Revenue increased by 40.1%",
  "what_happened": "Revenue in Enterprise segment jumped from $X to $Y",
  "why_happened": "Driven by 45% increase in Electronics sales (+$280K)...",
  "confidence": 92.3
}
```

**Key Points**:
- 🎯 Automatic time range parsing ("last month")
- 🎯 Positive change detection (spike, not drop)
- 🎯 Multi-dimensional breakdown
- 🎯 High confidence due to clear driver

---

### Part 2: Anomaly Detection (ARIMA)

#### Question 3: Time-Series Anomalies

**Ask**: `Show me anomalies in revenue for Q4 2024`

**What the System Does**:
1. ✅ Parses: metric=Revenue, time=Q4 2024, feed_type=ARIMA
2. ✅ Generates time-series query (daily granularity)
3. ✅ Fits ARIMA model to data
4. ✅ Computes residuals and detects outliers (3-sigma)
5. ✅ Identifies 5 anomaly points ✅ **TRIGGERED**
6. ✅ Ranks by severity
7. ✅ Marks anomalies on trend chart
8. ✅ Performs RCA for anomalous dates

**Expected Output**:
```json
{
  "triggered": true,
  "trigger_reason": "Detected 5 anomalies (sensitivity: 3.0 sigma)",
  "what_happened": "Revenue exhibited unusual patterns on 5 dates in Q4",
  "why_happened": "Anomaly on Nov 25 (+$50K) driven by Black Friday surge...",
  "anomaly_points": [
    {"date": "2024-11-25", "value": 85000, "residual": 15000, "severity": 0.85},
    ...
  ],
  "confidence": 78.2
}
```

**Key Points**:
- 🎯 Keyword "anomalies" triggers ARIMA mode
- 🎯 Statistical detection (not threshold-based)
- 🎯 Severity scoring for each anomaly
- 🎯 Visual markers on chart

---

### Part 3: Not Triggered (Below Threshold)

#### Question 4: Minor Change

**Ask**: `What happened to profit in November 2024 vs October 2024?`

**What the System Does**:
1. ✅ Parses: metric=Profit, time=November 2024, baseline=October 2024
2. ✅ Executes queries
3. ✅ Detects 2.3% change (below 5% threshold) ❌ **NOT TRIGGERED**
4. ✅ Returns explanation and suggestion
5. ✅ No deep RCA or charts generated

**Expected Output**:
```json
{
  "triggered": false,
  "explanation": "Profit changed by 2.3%, below the 5% threshold",
  "suggestion": "Consider lowering the threshold or checking a different time period",
  "metrics": {
    "current_value": 125000,
    "baseline_value": 122000,
    "percent_change": 2.3
  }
}
```

**Key Points**:
- 🎯 Smart alert filtering (no alert fatigue)
- 🎯 Provides context even when not triggered
- 🎯 Suggests next steps
- 🎯 Shows actual metrics for transparency

---

## 🎨 UI Walkthrough

### Question Input
- Large text area with placeholder
- "Run Analysis" button (blue, prominent)
- "Clear" button (gray)
- Example questions (clickable chips)
- Character counter

### Results Display

**If Triggered**:
- ✅ Green "Triggered" badge
- ✅ Trigger reason at top
- ✅ "What happened" summary (bold)
- ✅ "Why it happened" explanation (detailed)
- ✅ Confidence score badge (0-100%)
- ✅ Primary trend chart (line)
- ✅ Driver impact chart (bar)
- ✅ Evidence section (collapsible)

**If Not Triggered**:
- ⭕ Gray "Not Triggered" badge
- ⭕ Explanation text
- ⭕ Suggestion for next steps
- ⭕ Current metrics display
- ⭕ No charts (saves computational resources)

---

## 🔄 Live Demo Script

### Introduction (2 minutes)
> "The current Tellius Feed requires extensive configuration: define metrics, set thresholds, configure dimensions, schedule checks. Users get alerts but often lack context.
>
> **Intelligent Feed** flips this model: Ask a question in plain English, get a complete answer with visual proof and deep explanations."

### Demo 1: APAC Revenue Drop (5 minutes)

**Say**: "Let's investigate a revenue decline in APAC."

**Type**: `Why did revenue in APAC drop in the last 8 weeks vs previous period?`

**Click**: Run Analysis

**While loading** (5-10 seconds):
> "The system is now:
> 1. Parsing your question with Claude AI
> 2. Generating SQL queries with proper JOINs
> 3. Validating for security
> 4. Executing against the database
> 5. Detecting the change magnitude
> 6. Running deep root-cause analysis
> 7. Building visual evidence
> 8. Generating the narrative"

**When results appear**:

1. **Point to green "Triggered" badge**:
   > "The system detected a significant change: 20% decline, well above the 5% threshold."

2. **Read "What happened"**:
   > "Revenue declined from $2.4M to $2.0M. Clear, factual statement."

3. **Read "Why it happened"**:
   > "Enterprise segment dropped 23%, contributing $-350K. Product A sales decreased 12%, adding $-180K impact. Notice how it cites specific numbers and drivers."

4. **Show Trend Chart**:
   > "Blue line is current period, gray dashed is baseline. Clear visual evidence of the decline."

5. **Show Driver Impact Chart**:
   > "Top contributors ranked by absolute impact. Red bars are negative, green would be positive offsets."

6. **Point to confidence score**:
   > "87.5% explainability score means the top drivers account for most of the change."

**Takeaway**:
> "In one question, we got: detection, explanation, visual proof, and confidence scoring. No dashboard hopping. No manual analysis."

---

### Demo 2: Enterprise Spike (3 minutes)

**Say**: "Now let's look at a positive change."

**Type**: `What caused the revenue spike in Enterprise segment last month?`

**When results appear**:

1. **40% increase detected**
2. **Electronics category identified as driver**
3. **Charts show spike clearly**

**Takeaway**:
> "Same question pattern works for increases and decreases. System adapts automatically."

---

### Demo 3: Anomaly Detection (3 minutes)

**Say**: "Let's switch to statistical anomaly detection."

**Type**: `Show me anomalies in revenue for Q4 2024`

**When results appear**:

1. **5 anomalies detected**
2. **Severity ranked**
3. **Red markers on chart**
4. **Black Friday surge identified**

**Takeaway**:
> "ARIMA mode uses statistical modeling, not thresholds. Perfect for finding unexpected patterns."

---

### Demo 4: Not Triggered (2 minutes)

**Say**: "Not everything triggers an alert. Watch what happens with a minor change."

**Type**: `What happened to profit in November vs October?`

**When results appear**:

1. **"Not Triggered" badge**
2. **2.3% change shown**
3. **Suggestion provided**
4. **No charts (intentional)**

**Takeaway**:
> "Smart filtering prevents alert fatigue. User still gets context but system doesn't waste resources on non-issues."

---

## 💡 Key Differentiators to Highlight

### 1. Question-Driven, Not Configuration-Driven
- ❌ Old: Set up feed → configure threshold → wait for alerts
- ✅ New: Ask question → get answer immediately

### 2. Deep, Not Shallow
- ❌ Old: "Revenue dropped 15%"
- ✅ New: "Revenue dropped 15% because Enterprise segment fell 23% ($-350K) and Product A decreased 12% ($-180K)"

### 3. Visual, Not Text-Only
- ❌ Old: Alert email with numbers
- ✅ New: Interactive charts with trend lines, comparisons, and annotations

### 4. Explainable, Not Black-Box
- ❌ Old: "Alert triggered"
- ✅ New: "87.5% confidence - here's why we're confident"

### 5. AI-Augmented, Not AI-Computed
- ❌ AI generates numbers: ❌ Not trustworthy
- ✅ AI parses questions and writes narratives: ✅ Trustworthy

---

## 🎯 Closing Points

**Say**:
> "This system maintains full compatibility with Tellius Business Views and TQL architecture. It's not replacing existing Tellius Feed—it's the next evolution.
>
> Future: Users can subscribe to questions for ongoing monitoring, turning any question into a scheduled feed with notifications.
>
> **One question. Complete answer. Deep insights. Visual proof. In under 15 seconds.**"

---

## 🐛 Troubleshooting Demo Issues

### Backend not responding
```bash
# Check if running
curl http://localhost:8000/api/health

# Restart if needed
cd backend
python -m app.main
```

### Frontend not loading
```bash
# Check if running
curl http://localhost:3000

# Restart if needed
cd frontend
npm run dev
```

### Database empty
```bash
cd backend
python scripts/init_database.py
```

### API key error
```bash
# Check .env file
cd backend
cat .env | grep ANTHROPIC_API_KEY

# Should have: ANTHROPIC_API_KEY=sk-ant-...
```

---

## 📹 Demo Recording Tips

1. **Pre-load the page** before recording
2. **Use zoom** on important UI elements
3. **Pause for 2-3 seconds** when results appear
4. **Highlight with cursor** key insights
5. **Keep questions visible** in frame
6. **Show confidence scores** clearly

---

**Demo Time**: ~15-20 minutes
**Questions Demonstrated**: 4
**Key Features Covered**: 100%
**Wow Factor**: 🚀🚀🚀
