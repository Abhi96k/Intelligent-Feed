"""LLM SQL Generator - Generate SQL queries directly from natural language using LLM."""

import json
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from anthropic import Anthropic
from app.models.plan import TQLPlan, PlanMetadata
from app.models.intent import ParsedIntent, TimeRange, BaselineConfig, FeedType, BaselineType, ThresholdConfig, ComparisonOperator
from app.services.bv_context_builder import BVContext
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class LLMSQLGeneratorResponse:
    """Response from LLM SQL Generator containing both SQL and parsed intent."""

    def __init__(
        self,
        tql_plan: TQLPlan,
        parsed_intent: ParsedIntent,
        raw_llm_response: Dict[str, Any],
    ):
        self.tql_plan = tql_plan
        self.parsed_intent = parsed_intent
        self.raw_llm_response = raw_llm_response


class LLMSQLGenerator:
    """
    Generates SQL queries directly from natural language using LLM.
    
    This replaces the two-step process (QuestionParser -> TQLPlanner)
    with a single LLM call that generates both the structured intent
    and the SQL queries.
    """

    def __init__(self):
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.ANTHROPIC_MODEL

    async def generate(
        self, user_question: str, bv_context: BVContext
    ) -> LLMSQLGeneratorResponse:
        """
        Generate SQL queries and parsed intent from natural language question.

        Args:
            user_question: Natural language question from user
            bv_context: Business View context for grounding

        Returns:
            LLMSQLGeneratorResponse with TQL plan and parsed intent
        """
        logger.info("llm_sql_generation_started", question=user_question)

        # Build prompt for LLM
        prompt = self._build_prompt(user_question, bv_context)

        # Call LLM
        response = self.client.messages.create(
            model=self.model,
            max_tokens=settings.ANTHROPIC_MAX_TOKENS,
            temperature=settings.ANTHROPIC_TEMPERATURE,
            messages=[{"role": "user", "content": prompt}],
        )

        # Extract JSON from response
        response_text = response.content[0].text
        logger.debug("llm_sql_response", response=response_text[:500])

        # Parse JSON
        parsed_json = self._extract_json(response_text)
        
        # Convert to TQL Plan and ParsedIntent
        tql_plan = self._json_to_tql_plan(parsed_json)
        parsed_intent = self._json_to_parsed_intent(parsed_json)

        logger.info(
            "llm_sql_generation_completed",
            queries_count=len(tql_plan.get_all_queries()),
            feed_type=parsed_intent.feed_type.value,
        )

        return LLMSQLGeneratorResponse(
            tql_plan=tql_plan,
            parsed_intent=parsed_intent,
            raw_llm_response=parsed_json,
        )

    def _extract_json(self, response_text: str) -> Dict[str, Any]:
        """Extract JSON from LLM response."""
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
                return json.loads(json_str)
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
                return json.loads(json_str)
            else:
                raise ValueError(f"Failed to parse LLM response as JSON: {response_text[:500]}")

    def _build_prompt(self, question: str, bv_context: BVContext) -> str:
        """Build LLM prompt for SQL generation."""

        measures_list = "\n".join(
            [f"  - {name}: {info['expression']}" for name, info in bv_context.measures_info.items()]
        )

        dimensions_list = "\n".join(
            [f"  - {name}: {info['table']}.{info['column']}" for name, info in bv_context.dimensions_info.items()]
        )

        # Build table schema
        schema_description = bv_context.schema_context

        prompt = f"""You are an expert SQL generator for Tellius Intelligent Feed analytics system.

## Database Schema
{schema_description}

## Available Measures (with SQL expressions)
{measures_list}

## Available Dimensions
{dimensions_list}

## Time Dimension
- Column: {bv_context.time_info['full_name']}
- Table: {bv_context.time_info['table']}

## Join Relationships
The tables are joined as follows:
- sales_fact.date_id = date_dim.date_id
- sales_fact.product_id = product_dim.product_id
- sales_fact.customer_id = customer_dim.customer_id
- sales_fact.region_id = region_dim.region_id

## Current Date
{datetime.now().date().isoformat()}

## User Question
"{question}"

## Your Task
Generate SQL queries to answer this question. You MUST generate:

1. **current_period_query**: SQL to get the metric value for the analyzed time period
2. **baseline_period_query**: SQL to get the metric value for the comparison period (if comparison is requested)
3. **timeseries_query**: SQL to get time-series data for trend/anomaly detection (if analyzing patterns over time)
4. **dimensional_breakdown_query**: SQL to break down the metric by dimensions for root-cause analysis
5. **baseline_dimensional_breakdown_query**: SQL for baseline period breakdown (if comparison is requested)

## SQL Generation Rules
1. Use the exact measure expressions provided above
2. Always include proper JOINs between tables
3. Use the date_dim.date column for time filtering with format 'YYYY-MM-DD'
4. For aggregated metrics, alias the result as 'metric_value'
5. For time-series, alias date as 'date' and metric as 'value'
6. For dimensional breakdowns, include dimension columns with their names as aliases and metric_value

## Response Format
Return ONLY valid JSON:
```json
{{
  "intent": {{
    "metric": "exact_measure_name",
    "time_range": {{
      "start_date": "YYYY-MM-DD",
      "end_date": "YYYY-MM-DD",
      "granularity": "day|week|month"
    }},
    "filters": {{"DimensionName": "value"}},
    "baseline": {{
      "type": "previous_period|last_year|custom",
      "start_date": "YYYY-MM-DD",
      "end_date": "YYYY-MM-DD"
    }},
    "feed_type": "absolute|arima",
    "threshold_config": {{
      "operator": "greater_than|less_than|greater_than_equal|less_than_equal|equal|not_equal|change_greater_than|change_less_than",
      "value": 1000000,
      "compare_to": "current|baseline|change|percent_change"
    }}
  }},
  "sql": {{
    "current_period_query": "SELECT ... AS metric_value FROM ... WHERE ...",
    "baseline_period_query": "SELECT ... AS metric_value FROM ... WHERE ..." or null,
    "timeseries_query": "SELECT date, value FROM ... GROUP BY date ORDER BY date" or null,
    "dimensional_breakdown_query": "SELECT dimension, metric_value FROM ... GROUP BY dimension",
    "baseline_dimensional_breakdown_query": "..." or null
  }},
  "alert_config": {{
    "should_trigger_alert": true,
    "alert_type": "drop|increase|anomaly|spike",
    "severity": "low|medium|high|critical",
    "description": "Brief description of what to look for"
  }}
}}
```

## Threshold Configuration Guide
The threshold_config determines when to trigger an alert:

### Operators:
- "greater_than": current > value (e.g., revenue > $1M)
- "less_than": current < value (e.g., profit < $100K)
- "greater_than_equal": current >= value
- "less_than_equal": current <= value
- "equal": current == value
- "not_equal": current != value
- "change_greater_than": |current - baseline| > value (e.g., change > $50K)
- "change_less_than": |current - baseline| < value

### compare_to:
- "current": Compare current period value against threshold
- "baseline": Compare baseline period value against threshold
- "change": Compare absolute change (current - baseline) against threshold
- "percent_change": Compare percentage change against threshold

### Examples:
- User asks "Alert if revenue drops below $1M" → operator: "less_than", value: 1000000, compare_to: "current"
- User asks "Alert if profit exceeds $500K" → operator: "greater_than", value: 500000, compare_to: "current"
- User asks "Alert if change is more than $100K" → operator: "change_greater_than", value: 100000, compare_to: "change"
- User asks "Why did revenue drop?" (no specific threshold) → operator: "change_greater_than", value: 0, compare_to: "change" (any change triggers)

## Important Notes
- Generate complete, executable SQL queries
- Include all necessary JOINs
- Use proper date filtering based on the time range
- Always generate dimensional_breakdown_query for root-cause analysis
- For timeseries_query, GROUP BY date_dim.date and ORDER BY date_dim.date

## Choosing feed_type (CRITICAL - Understand User Intent)

Choose feed_type based on the SEMANTIC INTENT of the question, NOT just keywords:

### Use "absolute" when the user's intent is to:
- **Compare two specific time periods** (e.g., "Q3 vs Q2", "this month vs last month", "2024 vs 2023")
- **Understand WHY a change happened** between two periods (e.g., "Why did revenue drop?", "What caused the increase?")
- **Quantify a difference** between current and baseline (e.g., "How much did profit change?")
- **Explain root causes** of a known change (e.g., "What drove the growth in Enterprise segment?")
- The user implies or explicitly mentions a comparison baseline period

### Use "arima" when the user's intent is to:
- **Detect unusual patterns or outliers** in the data over time (e.g., "Find anomalies in sales")
- **Identify unexpected behavior** without a specific comparison period (e.g., "Is there anything unusual?")
- **Monitor for deviations from expected trends** (e.g., "Alert me if revenue behaves abnormally")
- **Analyze time-series patterns** for statistical outliers (e.g., "Detect spikes in the last 6 months")
- The user wants to find anomalies within a SINGLE time range (not comparing two periods)

### Decision Framework:
1. Does the user mention or imply TWO time periods to compare? → "absolute"
2. Is the user asking WHY something changed between periods? → "absolute" 
3. Is the user looking for outliers/anomalies within a single time range? → "arima"
4. Is the user asking for pattern/trend monitoring without baseline? → "arima"
5. Default: If comparing periods or asking "why" → "absolute"; If detecting anomalies → "arima"

### Examples:
- "Why did revenue drop in Q3 2024?" → "absolute" (asking WHY, implies comparison to previous period)
- "Show me anomalies in revenue for 2024" → "arima" (detecting outliers in a time series)
- "Compare Q4 sales to Q3" → "absolute" (explicit two-period comparison)
- "Is there anything unusual about November sales?" → "arima" (looking for unexpected patterns)
- "What caused the profit spike in October?" → "absolute" (asking WHY a known change happened)
- "Detect any irregular patterns in customer count" → "arima" (pattern detection)
- "Revenue dropped 20% - what happened?" → "absolute" (explaining a known change)

Return only the JSON, no additional text.
"""

        return prompt

    def _json_to_tql_plan(self, parsed_json: Dict[str, Any]) -> TQLPlan:
        """Convert parsed JSON to TQLPlan object."""
        sql = parsed_json.get("sql", {})

        # Build metadata
        metadata = PlanMetadata(
            estimated_rows=1000,
            complexity_score=self._calculate_complexity(sql),
            uses_joins=True,
            uses_aggregation=True,
            uses_window_functions=False,
        )

        return TQLPlan(
            current_period_query=sql.get("current_period_query", "SELECT 1"),
            baseline_period_query=sql.get("baseline_period_query"),
            timeseries_query=sql.get("timeseries_query"),
            dimensional_breakdown_query=sql.get("dimensional_breakdown_query"),
            baseline_dimensional_breakdown_query=sql.get("baseline_dimensional_breakdown_query"),
            metadata=metadata,
        )

    def _json_to_parsed_intent(self, parsed_json: Dict[str, Any]) -> ParsedIntent:
        """Convert parsed JSON to ParsedIntent object."""
        intent = parsed_json.get("intent", {})

        # Parse time range
        time_range_data = intent.get("time_range", {})
        time_range = TimeRange(
            start_date=datetime.strptime(time_range_data.get("start_date", "2024-01-01"), "%Y-%m-%d").date(),
            end_date=datetime.strptime(time_range_data.get("end_date", "2024-12-31"), "%Y-%m-%d").date(),
            granularity=time_range_data.get("granularity", "day"),
        )

        # Parse baseline
        baseline = None
        baseline_data = intent.get("baseline")
        if baseline_data:
            baseline = BaselineConfig(
                type=BaselineType(baseline_data.get("type", "previous_period")),
                start_date=datetime.strptime(baseline_data["start_date"], "%Y-%m-%d").date() if baseline_data.get("start_date") else None,
                end_date=datetime.strptime(baseline_data["end_date"], "%Y-%m-%d").date() if baseline_data.get("end_date") else None,
            )

        # Parse feed type
        feed_type_str = intent.get("feed_type", "absolute")
        feed_type = FeedType.ARIMA if feed_type_str == "arima" else FeedType.ABSOLUTE

        # Parse threshold config (new value-based thresholds)
        threshold_config = None
        threshold_config_data = intent.get("threshold_config")
        if threshold_config_data:
            try:
                operator_str = threshold_config_data.get("operator", "greater_than")
                operator = ComparisonOperator(operator_str)
                threshold_config = ThresholdConfig(
                    operator=operator,
                    value=float(threshold_config_data.get("value", 0)),
                    compare_to=threshold_config_data.get("compare_to", "current"),
                )
            except (ValueError, KeyError) as e:
                logger.warning("failed_to_parse_threshold_config", error=str(e))
                threshold_config = None

        return ParsedIntent(
            metric=intent.get("metric", "Revenue"),
            time_range=time_range,
            filters=intent.get("filters", {}),
            baseline=baseline,
            feed_type=feed_type,
            threshold=intent.get("threshold"),  # Legacy support
            threshold_config=threshold_config,
        )

    def _calculate_complexity(self, sql: Dict[str, Any]) -> int:
        """Calculate query complexity score (1-10)."""
        score = 1

        # Count queries
        for key, query in sql.items():
            if query:
                score += 1
                # Check for JOINs
                if query and "JOIN" in query.upper():
                    score += 1

        return min(score, 10)

    def get_alert_config(self, parsed_json: Dict[str, Any]) -> Dict[str, Any]:
        """Extract alert configuration from LLM response."""
        return parsed_json.get("alert_config", {
            "should_trigger_alert": False,
            "alert_type": "unknown",
            "severity": "low",
            "threshold_percent": 5.0,
            "description": "No alert configured",
        })
