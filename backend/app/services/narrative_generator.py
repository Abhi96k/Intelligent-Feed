"""Narrative Generator - Create human-readable insight narratives using LLM."""

import json
from anthropic import Anthropic
from app.models.detection import DetectionResult
from app.models.insight import DeepInsight, Driver
from app.models.intent import ParsedIntent
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class NarrativeGenerator:
    """
    Generates human-readable narratives for insights using LLM.

    The LLM is given computed evidence and generates explanations,
    but does NOT compute any metrics itself.
    """

    def __init__(self):
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.ANTHROPIC_MODEL

    async def generate(
        self,
        detection_result: DetectionResult,
        deep_insight: DeepInsight,
        intent: ParsedIntent,
    ) -> tuple[str, str]:
        """
        Generate insight narrative.

        Args:
            detection_result: Detection engine result
            deep_insight: Deep insight analysis result
            intent: Parsed user intent

        Returns:
            Tuple of (what_happened, why_happened)
        """
        logger.info("generating_narrative", metric=intent.metric)

        # Build prompt with computed evidence
        prompt = self._build_prompt(detection_result, deep_insight, intent)

        # Call LLM
        response = self.client.messages.create(
            model=self.model,
            max_tokens=settings.ANTHROPIC_MAX_TOKENS,
            temperature=0.3,  # Slightly higher for narrative generation
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Extract narrative from response
        response_text = response.content[0].text
        logger.debug("llm_narrative_response", response=response_text)

        # Parse JSON response
        try:
            narrative_json = json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
                narrative_json = json.loads(json_str)
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
                narrative_json = json.loads(json_str)
            else:
                # Fallback: generate simple narrative
                narrative_json = self._generate_fallback_narrative(
                    detection_result, deep_insight, intent
                )

        what_happened = narrative_json.get("what_happened", "")
        why_happened = narrative_json.get("why_happened", "")

        logger.info("narrative_generated", what_len=len(what_happened), why_len=len(why_happened))

        return what_happened, why_happened

    def _build_prompt(
        self,
        detection_result: DetectionResult,
        deep_insight: DeepInsight,
        intent: ParsedIntent,
    ) -> str:
        """Build LLM prompt for narrative generation."""

        # Format detection metrics
        if detection_result.is_absolute():
            detection_summary = f"""
Current Value: {detection_result.current_value:.2f}
Baseline Value: {detection_result.baseline_value:.2f}
Absolute Change: {detection_result.absolute_delta:+.2f}
Percent Change: {detection_result.percent_change:+.1f}%
Threshold: {detection_result.threshold_used}%
"""
        else:
            detection_summary = f"""
Anomalies Detected: {detection_result.get_anomaly_count()}
Severe Anomalies: {detection_result.get_severe_anomaly_count()}
Total Data Points: {detection_result.metrics.get('total_points', 'N/A')}
"""

        # Format top drivers
        drivers_summary = ""
        for i, driver in enumerate(deep_insight.get_top_n_drivers(5), 1):
            impact_sign = "+" if driver.impact > 0 else ""
            drivers_summary += f"""
{i}. {driver.member} ({driver.dimension})
   - Impact: {impact_sign}{driver.impact:.2f}
   - Current Contribution: {driver.contribution_current:.1f}%
   - Baseline Contribution: {driver.contribution_baseline:.1f}%
   - Shift: {driver.shift:+.1f} percentage points
"""

        # Format filters
        filters_summary = ""
        if intent.has_filters():
            filters_summary = "\nFilters Applied:\n"
            for dim, val in intent.filters.items():
                filters_summary += f"  - {dim}: {val}\n"

        prompt = f"""You are generating an insight narrative for Tellius Intelligent Feed.

You are given COMPUTED EVIDENCE below. Your job is to write a clear, concise narrative.

DO NOT compute any numbers yourself. Use ONLY the numbers provided below.

Metric: {intent.metric}

Time Range: {intent.time_range.start_date} to {intent.time_range.end_date}
{filters_summary}

Detection Result:
{detection_summary}

Top Contributing Drivers (ranked by impact):
{drivers_summary}

Explainability Score: {deep_insight.explainability_score:.1f}/100

Generate a narrative with TWO parts:

1. **what_happened**: A single concise sentence (max 150 characters) stating what changed.
   - Focus on the metric, direction, and magnitude
   - Example: "Revenue in APAC declined from $2.4M to $2.0M over the last 8 weeks"

2. **why_happened**: 2-3 sentences explaining WHY it happened.
   - Cite the top 2-3 contributing drivers with specific numbers
   - Use data-driven language
   - Be specific and actionable
   - Example: "The decline was primarily driven by a 23% drop in Enterprise segment sales ($-350K impact) and a 12% decrease in Product A sales ($-180K impact). These were partially offset by 8% growth in SMB segment."

Tone:
- Professional and data-driven
- Confident but not alarmist
- Specific numbers, not vague language
- Action-oriented

Return ONLY valid JSON:
{{
  "what_happened": "...",
  "why_happened": "..."
}}

Do not include any explanations, only the JSON.
"""

        return prompt

    def _generate_fallback_narrative(
        self,
        detection_result: DetectionResult,
        deep_insight: DeepInsight,
        intent: ParsedIntent,
    ) -> dict:
        """Generate simple fallback narrative if LLM fails."""

        logger.warning("using_fallback_narrative")

        if detection_result.is_absolute():
            direction = "increased" if detection_result.absolute_delta > 0 else "decreased"
            what_happened = (
                f"{intent.metric} {direction} by {abs(detection_result.percent_change):.1f}% "
                f"from {detection_result.baseline_value:.2f} to {detection_result.current_value:.2f}"
            )
        else:
            what_happened = (
                f"Detected {detection_result.get_anomaly_count()} anomalies "
                f"in {intent.metric} time-series"
            )

        # Build why_happened from top drivers
        if deep_insight.top_drivers:
            top_driver = deep_insight.top_drivers[0]
            why_happened = (
                f"The primary driver was {top_driver.member} with an impact of "
                f"{top_driver.impact:+.2f}. "
            )

            if len(deep_insight.top_drivers) > 1:
                second_driver = deep_insight.top_drivers[1]
                why_happened += (
                    f"Additional contribution from {second_driver.member} "
                    f"({second_driver.impact:+.2f} impact)."
                )
        else:
            why_happened = "Further analysis is needed to identify specific drivers."

        return {
            "what_happened": what_happened,
            "why_happened": why_happened,
        }
