"""Question Parser - Extract structured intent from natural language using LLM."""

import json
from datetime import datetime, timedelta
from typing import Dict, Any
from app.models.intent import ParsedIntent, TimeRange, BaselineConfig, FeedType, BaselineType
from app.services.bv_context_builder import BVContext
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class QuestionParser:
    """Parses natural language questions into structured intents.
    
    Supports both OpenAI and Anthropic providers.
    """

    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()
        
        if self.provider == "openai":
            from openai import OpenAI
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
            self.model = settings.OPENAI_MODEL
        else:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            self.model = settings.ANTHROPIC_MODEL

    async def parse(self, user_question: str, bv_context: BVContext) -> ParsedIntent:
        """
        Parse user question into structured intent.

        Args:
            user_question: Natural language question from user
            bv_context: Business View context for grounding

        Returns:
            ParsedIntent object
        """
        logger.info("parsing_question", question=user_question, provider=self.provider)

        # Build prompt for LLM
        prompt = self._build_prompt(user_question, bv_context)

        # Call LLM based on provider
        if self.provider == "openai":
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=settings.OPENAI_MAX_TOKENS,
                temperature=settings.OPENAI_TEMPERATURE,
                messages=[{"role": "user", "content": prompt}],
            )
            response_text = response.choices[0].message.content
        else:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=settings.ANTHROPIC_MAX_TOKENS,
                temperature=settings.ANTHROPIC_TEMPERATURE,
                messages=[{"role": "user", "content": prompt}],
            )
            response_text = response.content[0].text
        logger.debug("llm_response", response=response_text)

        # Parse JSON
        try:
            parsed_json = json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
                parsed_json = json.loads(json_str)
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
                parsed_json = json.loads(json_str)
            else:
                raise ValueError(f"Failed to parse LLM response as JSON: {response_text}")

        # Convert to ParsedIntent
        intent = self._json_to_intent(parsed_json)

        logger.info("question_parsed", intent=intent.to_dict())

        return intent

    def _build_prompt(self, question: str, bv_context: BVContext) -> str:
        """Build LLM prompt for question parsing."""

        measures_list = "\n".join([f"  - {name}: {info['expression']}"
                                   for name, info in bv_context.measures_info.items()])

        dimensions_list = "\n".join([f"  - {name}"
                                     for name in bv_context.dimensions_info.keys()])

        prompt = f"""You are parsing a Tellius Intelligent Feed question.

Business View Schema:
{bv_context.schema_context}

Available Measures:
{measures_list}

Available Dimensions:
{dimensions_list}

Time Dimension: {bv_context.time_info['full_name']}

Current Date: {datetime.now().date().isoformat()}

User Question: "{question}"

Extract the following structured information:

1. **metric**: Which measure/metric is being analyzed? Use exact measure name from the list above.

2. **time_range**: What time period is being analyzed?
   - Parse relative time expressions like "last 8 weeks", "Q4 2024", "last month", "past 3 months"
   - Convert to absolute dates (start_date, end_date in YYYY-MM-DD format)
   - Infer granularity: "day", "week", or "month"

3. **filters**: Which dimensions are being filtered?
   - Extract dimension=value pairs
   - Example: "in APAC" → {{"Region": "APAC"}}
   - Example: "for Enterprise" → {{"Segment": "Enterprise"}}
   - Use exact dimension names from the list above

4. **baseline**: What comparison period is requested?
   - "vs previous period" → previous_period
   - "vs last year" / "year over year" → last_year
   - If baseline dates are explicit, extract them
   - If no comparison mentioned, set to null

5. **feed_type**: What type of analysis?
   - "anomaly" / "anomalies" / "unusual" / "spikes" → "arima"
   - "drop" / "increase" / "change" / "trend" → "absolute"
   - Default to "absolute" if unclear

6. **threshold**: Is a specific threshold mentioned? (e.g., "more than 10%")
   - Extract numeric value if present
   - Otherwise set to null (will use default 5%)

Return ONLY valid JSON in this exact format:
{{
  "metric": "exact_measure_name",
  "time_range": {{
    "start_date": "YYYY-MM-DD",
    "end_date": "YYYY-MM-DD",
    "granularity": "day|week|month"
  }},
  "filters": {{
    "DimensionName": "value"
  }},
  "baseline": {{
    "type": "previous_period|last_year|custom",
    "start_date": "YYYY-MM-DD",
    "end_date": "YYYY-MM-DD"
  }} or null,
  "feed_type": "absolute|arima",
  "threshold": 5.0 or null
}}

Rules:
- Use exact measure and dimension names from schema
- Convert all relative dates to absolute dates
- Be precise with date calculations
- If information is ambiguous, make reasonable assumptions
- Return only the JSON, no explanations
"""

        return prompt

    def _json_to_intent(self, parsed_json: Dict[str, Any]) -> ParsedIntent:
        """Convert parsed JSON to ParsedIntent object."""

        # Parse time range
        time_range = TimeRange(
            start_date=datetime.strptime(parsed_json['time_range']['start_date'], '%Y-%m-%d').date(),
            end_date=datetime.strptime(parsed_json['time_range']['end_date'], '%Y-%m-%d').date(),
            granularity=parsed_json['time_range']['granularity']
        )

        # Parse baseline
        baseline = None
        if parsed_json.get('baseline'):
            baseline_data = parsed_json['baseline']
            baseline = BaselineConfig(
                type=BaselineType(baseline_data['type']),
                start_date=datetime.strptime(baseline_data['start_date'], '%Y-%m-%d').date() if baseline_data.get('start_date') else None,
                end_date=datetime.strptime(baseline_data['end_date'], '%Y-%m-%d').date() if baseline_data.get('end_date') else None,
            )

        # Create ParsedIntent
        intent = ParsedIntent(
            metric=parsed_json['metric'],
            time_range=time_range,
            filters=parsed_json.get('filters', {}),
            baseline=baseline,
            feed_type=FeedType(parsed_json.get('feed_type', 'absolute')),
            threshold=parsed_json.get('threshold')
        )

        return intent
