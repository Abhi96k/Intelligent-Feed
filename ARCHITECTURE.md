# Tellius Intelligent Feed / Deep Insight System Architecture

## System Overview

This document describes the architecture for the redesigned Tellius Feed system, transforming it from a configuration-driven alerting system into an intelligent, question-driven insight engine.

## Design Principles

1. **Question-Driven, Not Configuration-Driven**
   - Single natural language input contains all parameters
   - No separate UI controls for filters, time ranges, baselines

2. **AI-Augmented, Not AI-Computed**
   - LLM for parsing, planning, and narration only
   - All metrics, deltas, and statistics computed deterministically
   - Maintains Tellius trust and auditability

3. **Evidence-Based Insights**
   - Visual charts as proof, not decoration
   - Deep root-cause analysis with contribution tracking
   - Explainable confidence scores

4. **Tellius-Compatible**
   - Reuses Business View model and utilities
   - Compatible with TQL/text-to-SQL architecture
   - Aligns with existing Feed types (absolute, ARIMA)

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                             │
│  React + Vite + React Flow + Recharts/Victory               │
│  - Question Input                                            │
│  - Insight Card                                              │
│  - Chart Visualizations                                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP/JSON
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      API Layer (FastAPI)                     │
│  - /api/insight (POST)                                       │
│  - /api/health                                               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Orchestration Layer                       │
│  IntelligentFeedOrchestrator                                 │
│  - Coordinates all components                                │
│  - Implements main insight generation flow                   │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────────┐
│ Understanding│    │  Detection   │    │  Insight         │
│    Layer     │    │    Layer     │    │  Generation      │
│              │    │              │    │                  │
│ - Parser     │    │ - Absolute   │    │ - Deep RCA       │
│ - Planner    │    │ - ARIMA      │    │ - Chart Builder  │
│ - Validator  │    │              │    │ - Narrator       │
└──────────────┘    └──────────────┘    └──────────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       Data Layer                             │
│  - BV Context Builder                                        │
│  - TQL Service Adapter                                       │
│  - Python Sandbox (ARIMA)                                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     External Services                        │
│  - Cloud LLM (Anthropic Claude)                              │
│  - Mock TQL/SQLite                                           │
└─────────────────────────────────────────────────────────────┘
```

## Component Specifications

### 1. Business View Context Builder

**Purpose**: Extract schema, semantics, and metadata from Tellius Business View

**Inputs**:
- Business View object (in-memory, hardcoded)

**Outputs**:
- `schema_context`: DDL, measures, dimensions for LLM grounding
- `allowed_columns`: Whitelist for SQL validation
- `join_graph`: Join relationships for SQL construction
- `time_semantics`: Calendar rules, dialect rules

**Tellius Utilities Used**:
- BV DDL generator
- Measure/dimension extractors
- Join relationship parser
- Time semantic analyzer

### 2. Question Parser

**Purpose**: Extract structured intent from natural language question

**Inputs**:
- `user_question`: string
- `schema_context`: from BV Context Builder

**Process**:
- Send question + schema context to Cloud LLM
- LLM extracts:
  - metric/KPI
  - time range (current window)
  - filters (dimensions + values)
  - baseline (comparison period)
  - feed_type (absolute | arima)

**Outputs**:
- `ParsedIntent` object (validated)

**LLM Prompt Template**:
```
You are parsing a Tellius Feed question.
Given schema: {schema_context}
User question: {user_question}

Extract:
- metric: which measure/KPI
- time_range: start/end dates or relative period
- filters: dimension=value pairs
- baseline: comparison period (previous period, last year, etc.)
- feed_type: absolute or arima

Return JSON only.
```

### 3. SQL/TQL Plan Generator

**Purpose**: Convert parsed intent into executable TQL/SQL plans

**Inputs**:
- `ParsedIntent`
- `schema_context`
- `join_graph`

**Process**:
- Generate SQL for:
  1. Current period query (with filters)
  2. Baseline period query (if applicable)
  3. Time-series query (for ARIMA)
  4. Dimensional breakdown query (for RCA)

**Outputs**:
- `TQLPlan` object containing multiple SQL statements

**Key Logic**:
- Respect Tellius time semantics (fiscal calendars, etc.)
- Apply proper JOIN logic from BV
- Include GROUP BY for dimensional analysis
- Use window functions for time-series

### 4. Plan Validator

**Purpose**: Ensure generated SQL is safe and Tellius-compatible

**Inputs**:
- `TQLPlan`
- `allowed_columns`

**Validation Rules**:
- No columns outside `allowed_columns`
- No subqueries beyond Tellius TQL spec
- No CTEs that violate Tellius dialect
- No dangerous operations (DROP, DELETE, etc.)
- Proper aggregation for measures

**Outputs**:
- `ValidatedTQLPlan` or ValidationError

### 5. TQL Service Adapter

**Purpose**: Execute TQL plans against data layer

**Mock Implementation**:
- SQLite database with sample data
- Pandas DataFrames for result sets
- Simulates Tellius TQL service behavior

**Inputs**:
- `ValidatedTQLPlan`

**Outputs**:
- `QueryResults` (DataFrames for each query)

**Error Handling**:
- Query timeout
- Malformed SQL
- Empty results

### 6. Detection Engines

#### 6a. Absolute Detection Engine

**Purpose**: Threshold-based change detection

**Inputs**:
- Current period value
- Baseline period value
- Threshold (default 5%)

**Process**:
```python
abs_delta = current - baseline
pct_change = (abs_delta / baseline) * 100 if baseline != 0 else None
triggered = abs(pct_change) >= threshold or abs(abs_delta) >= threshold
```

**Outputs**:
- `triggered`: boolean
- `trigger_reason`: string
- `metrics`: {current, baseline, abs_delta, pct_change}

#### 6b. ARIMA Detection Engine

**Purpose**: Intelligent anomaly detection

**Inputs**:
- Time-series DataFrame (date, value)
- Sensitivity parameters

**Process**:
1. Generate Python code for ARIMA fitting
2. Execute in sandboxed Python environment:
   ```python
   from statsmodels.tsa.arima.model import ARIMA
   model = ARIMA(data, order=(p, d, q))
   fit = model.fit()
   residuals = fit.resid
   anomalies = detect_outliers(residuals, threshold=3*std)
   ```
3. Return anomaly indicators

**Outputs**:
- `triggered`: boolean
- `anomaly_points`: List[{date, value, residual}]
- `model_params`: {p, d, q, aic, bic}

**Security**:
- Restricted Python sandbox (no file I/O, no network)
- Timeout limits
- Memory limits

### 7. Deep Insight Engine

**Purpose**: Root-cause analysis and contribution attribution

**Enabled Only If**: Detection engine triggered

**Process**:

1. **Contribution-Shift Analysis**
   - Query dimensional breakdown for current period
   - Query dimensional breakdown for baseline period
   - Compute contribution shift for each dimension member:
     ```python
     contribution_current = value_current / total_current
     contribution_baseline = value_baseline / total_baseline
     shift = contribution_current - contribution_baseline
     impact = shift * total_current
     ```

2. **Driver Ranking**
   - Sort dimension members by absolute impact
   - Identify top 5 positive drivers
   - Identify top 5 negative drivers

3. **Explainability Score**
   - Coverage: % of delta explained by top drivers
   - Confidence: statistical significance
   - Consistency: alignment across dimensions

**Outputs**:
- `DeepInsight` object:
  - `top_drivers`: ranked list
  - `contribution_shifts`: DataFrame
  - `explainability_score`: 0-100
  - `evidence`: raw data for charts

### 8. Chart Builder

**Purpose**: Generate chart specifications as visual evidence

**Enabled Only If**: Detection engine triggered

**Chart 1: Primary Trend Chart**
```json
{
  "type": "line",
  "title": "{metric} Over Time",
  "x_axis": {"field": "date", "label": "Date"},
  "y_axis": {"field": "value", "label": "{metric}"},
  "series": [
    {"name": "Current Period", "data": [...], "color": "#1f77b4"},
    {"name": "Baseline Period", "data": [...], "color": "#aaaaaa", "style": "dashed"}
  ],
  "annotations": [
    {"type": "threshold", "value": X, "label": "Threshold"},
    {"type": "anomaly", "points": [...], "marker": "circle", "color": "#ff0000"}
  ]
}
```

**Chart 2: Driver Impact Chart**
```json
{
  "type": "bar",
  "title": "Top Contributing Drivers",
  "x_axis": {"field": "dimension_member", "label": "Dimension"},
  "y_axis": {"field": "impact", "label": "Impact"},
  "data": [...],
  "sorted_by": "impact",
  "color_scale": "diverging"  // positive/negative colors
}
```

**Inputs**:
- `QueryResults`
- `DeepInsight`
- `DetectionResult`

**Outputs**:
- `List[ChartSpec]`

### 9. Insight Narrative Generator

**Purpose**: Generate human-readable insight narrative

**Enabled Only If**: Detection engine triggered

**Inputs**:
- `DetectionResult`
- `DeepInsight`
- `ParsedIntent`

**Process**:
- Send computed evidence to Cloud LLM
- LLM generates narrative in Tellius Feed tone

**LLM Prompt Template**:
```
You are generating an insight for Tellius Feed.

Metric: {metric}
Current Value: {current}
Baseline Value: {baseline}
Change: {pct_change}%

Top Drivers (by impact):
{drivers}

Generate a concise narrative:
1. What happened (1 sentence)
2. Why it happened (2-3 sentences citing top drivers)

Be specific, data-driven, and actionable.
Do not invent numbers.
```

**Outputs**:
- `what_happened`: string
- `why_happened`: string

### 10. Orchestrator

**Purpose**: Coordinate entire insight generation flow

**Flow**:
```python
def generate_insight(user_question: str, business_view: BV) -> InsightResponse:
    # 1. Extract BV context
    bv_context = BVContextBuilder.extract(business_view)

    # 2. Parse question
    intent = QuestionParser.parse(user_question, bv_context)

    # 3. Generate TQL plan
    plan = TQLPlanner.generate(intent, bv_context)

    # 4. Validate plan
    validated_plan = PlanValidator.validate(plan, bv_context)

    # 5. Execute queries
    results = TQLAdapter.execute(validated_plan)

    # 6. Run detection
    detection = detect(intent.feed_type, results)

    # 7. If NOT triggered, return early
    if not detection.triggered:
        return InsightResponse(
            triggered=False,
            explanation="No significant change detected",
            suggestion="Try adjusting threshold or time range"
        )

    # 8. Generate deep insight
    insight = DeepInsightEngine.analyze(results, detection)

    # 9. Build charts
    charts = ChartBuilder.build(results, insight, detection)

    # 10. Generate narrative
    narrative = NarrativeGenerator.generate(detection, insight, intent)

    # 11. Return full response
    return InsightResponse(
        triggered=True,
        trigger_reason=detection.trigger_reason,
        what_happened=narrative.what_happened,
        why_happened=narrative.why_happened,
        charts=charts,
        confidence=insight.explainability_score,
        evidence=insight.evidence
    )
```

## Data Contracts

### Business View (Input)

```python
@dataclass
class BusinessView:
    """Tellius Business View model (in-memory, hardcoded)"""
    id: str
    name: str
    tables: List[Table]
    joins: List[Join]
    measures: List[Measure]
    dimensions: List[Dimension]
    time_dimension: TimeDimension
    calendar_rules: CalendarRules

@dataclass
class Table:
    name: str
    schema: str
    columns: List[Column]

@dataclass
class Column:
    name: str
    type: str  # "integer", "string", "date", "float"

@dataclass
class Join:
    left_table: str
    right_table: str
    left_key: str
    right_key: str
    join_type: str  # "inner", "left", "right"

@dataclass
class Measure:
    name: str
    expression: str  # e.g., "SUM(revenue)", "COUNT(DISTINCT user_id)"
    format: str

@dataclass
class Dimension:
    name: str
    column: str
    table: str

@dataclass
class TimeDimension:
    column: str
    table: str
    granularity: str  # "day", "week", "month"

@dataclass
class CalendarRules:
    fiscal_year_start: int  # month (1-12)
    week_start: str  # "monday", "sunday"
```

### Parsed Intent

```python
@dataclass
class ParsedIntent:
    """Structured representation of user question"""
    metric: str  # measure name
    time_range: TimeRange
    filters: Dict[str, Union[str, List[str]]]  # dimension -> value(s)
    baseline: Optional[BaselineConfig]
    feed_type: FeedType  # "absolute" or "arima"

@dataclass
class TimeRange:
    start_date: date
    end_date: date
    granularity: str  # "day", "week", "month"

@dataclass
class BaselineConfig:
    type: str  # "previous_period", "last_year", "custom"
    start_date: Optional[date]
    end_date: Optional[date]

class FeedType(Enum):
    ABSOLUTE = "absolute"
    ARIMA = "arima"
```

### TQL Plan

```python
@dataclass
class TQLPlan:
    """Collection of SQL queries to execute"""
    current_period_query: str
    baseline_period_query: Optional[str]
    timeseries_query: Optional[str]
    dimensional_breakdown_query: Optional[str]
    metadata: PlanMetadata

@dataclass
class PlanMetadata:
    estimated_rows: int
    complexity_score: int
    uses_joins: bool
```

### Detection Result

```python
@dataclass
class DetectionResult:
    triggered: bool
    trigger_reason: str
    feed_type: FeedType
    metrics: Dict[str, float]
    anomaly_points: Optional[List[AnomalyPoint]]

@dataclass
class AnomalyPoint:
    date: date
    value: float
    residual: float
    severity: float  # 0-1
```

### Deep Insight

```python
@dataclass
class DeepInsight:
    top_drivers: List[Driver]
    contribution_shifts: pd.DataFrame
    explainability_score: float  # 0-100
    evidence: Dict[str, Any]

@dataclass
class Driver:
    dimension: str
    member: str
    impact: float
    contribution_current: float
    contribution_baseline: float
    shift: float
```

### Chart Specification

```python
@dataclass
class ChartSpec:
    chart_id: str
    chart_type: str  # "line", "bar", "area"
    title: str
    x_axis: AxisConfig
    y_axis: AxisConfig
    series: List[Series]
    annotations: List[Annotation]

@dataclass
class AxisConfig:
    field: str
    label: str
    format: Optional[str]

@dataclass
class Series:
    name: str
    data: List[Dict[str, Any]]
    color: str
    style: Optional[str]  # "solid", "dashed", "dotted"

@dataclass
class Annotation:
    type: str  # "threshold", "anomaly", "reference_line"
    value: Optional[float]
    points: Optional[List[Dict]]
    label: Optional[str]
    color: str
```

### Insight Response (API Output)

```python
@dataclass
class InsightResponse:
    triggered: bool

    # If triggered = True
    trigger_reason: Optional[str]
    what_happened: Optional[str]
    why_happened: Optional[str]
    charts: Optional[List[ChartSpec]]
    confidence: Optional[float]
    evidence: Optional[Dict]

    # If triggered = False
    explanation: Optional[str]
    suggestion: Optional[str]
```

## API Endpoints

### POST /api/insight

**Request**:
```json
{
  "user_question": "Why did revenue in APAC drop in the last 8 weeks vs previous period?"
}
```

**Response (Triggered)**:
```json
{
  "triggered": true,
  "trigger_reason": "Revenue decreased by 15.3% (threshold: 5%)",
  "what_happened": "Revenue in APAC declined from $2.4M to $2.0M over the last 8 weeks",
  "why_happened": "The decline was primarily driven by a 23% drop in Enterprise segment sales ($-350K impact) and a 12% decrease in Product A sales ($-180K impact). These were partially offset by 8% growth in SMB segment.",
  "charts": [
    {
      "chart_id": "trend_chart",
      "chart_type": "line",
      ...
    },
    {
      "chart_id": "drivers_chart",
      "chart_type": "bar",
      ...
    }
  ],
  "confidence": 87.5,
  "evidence": {
    "top_drivers": [...],
    "metrics": {...}
  }
}
```

**Response (Not Triggered)**:
```json
{
  "triggered": false,
  "explanation": "Revenue changed by 2.3%, below the 5% threshold",
  "suggestion": "The change is within normal variance. Consider lowering the threshold or checking a different time period."
}
```

### GET /api/health

**Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "components": {
    "llm": "connected",
    "database": "connected",
    "python_sandbox": "ready"
  }
}
```

## Technology Stack

### Backend
- **Framework**: FastAPI 0.104+
- **Language**: Python 3.11+
- **Database**: SQLite (mock TQL)
- **Data Processing**: Pandas 2.0+
- **Time Series**: statsmodels (ARIMA)
- **LLM Client**: anthropic SDK
- **Validation**: Pydantic v2

### Frontend
- **Framework**: React 18+ with Vite
- **Visualization**: Recharts (charts), React Flow (optional flow viz)
- **State Management**: React Query / TanStack Query
- **Styling**: Tailwind CSS
- **HTTP Client**: Axios

### Infrastructure
- **Python Sandbox**: RestrictedPython or subprocess isolation
- **Logging**: structlog
- **Testing**: pytest, React Testing Library

## Security & Governance

1. **SQL Injection Prevention**
   - Parameterized queries only
   - Column whitelist validation
   - No dynamic SQL from user input

2. **LLM Safety**
   - LLM used only for parsing and narration
   - No LLM-generated SQL execution without validation
   - All numeric outputs computed deterministically

3. **Python Sandbox**
   - No file system access
   - No network access
   - CPU and memory limits
   - Timeout enforcement

4. **Data Privacy**
   - No sensitive data in LLM prompts
   - Schema metadata only (no actual values)
   - Aggregated insights only

## Performance Targets

- Question parsing: < 2s
- TQL execution: < 5s
- ARIMA detection: < 10s
- Total end-to-end: < 15s
- Support up to 1M rows in time-series

## Future Extensions

1. **Alert Workflows**
   - Subscribe to questions
   - Schedule periodic checks
   - Notification channels (email, Slack)

2. **Multi-Metric Analysis**
   - Analyze correlated metrics
   - Cross-metric RCA

3. **Predictive Insights**
   - Forecast future trends
   - "What-if" scenarios

4. **Tellius Feed Integration**
   - Migrate existing feeds to new engine
   - Backward compatibility layer
   - Gradual rollout strategy

## Success Metrics

- **User Engagement**: Questions asked per user per week
- **Insight Quality**: User feedback on triggered insights
- **False Positive Rate**: Triggered but not actionable
- **Time Saved**: Reduction in dashboard navigation
- **Adoption**: % of Feed users migrated to Intelligent Feed
