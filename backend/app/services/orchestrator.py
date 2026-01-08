"""Intelligent Feed Orchestrator - Coordinates entire insight generation pipeline."""

import asyncio
from typing import Union, Dict, Any
from app.models.business_view import BusinessView
from app.models.response import (
    InsightResponseTriggered,
    InsightResponseNotTriggered,
    InsightResponse,
)
from app.services import (
    BVContextBuilder,
    TQLAdapter,
    AbsoluteDetectionEngine,
    ARIMADetectionEngine,
    DeepInsightEngine,
    ChartBuilderService,
    NarrativeGenerator,
    LLMSQLGenerator,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class IntelligentFeedOrchestrator:
    """
    Main orchestrator for the Intelligent Feed system.

    Coordinates all components to generate deep insights from user questions.
    
    NEW FLOW (LLM-generated SQL):
    1. User question -> LLM SQL Generator -> SQL queries + parsed intent
    2. SQL queries -> TQL Adapter -> Query results
    3. Results -> Detection Engine -> Triggered/Not Triggered
    4. If triggered -> Deep Insight Engine -> Root Cause Analysis
    5. Charts + Narrative generation
    """

    def __init__(self, business_view: BusinessView, db_path: str = "tellius_feed.db"):
        """
        Initialize orchestrator.

        Args:
            business_view: Business View object
            db_path: Path to SQLite database
        """
        self.business_view = business_view
        self.db_path = db_path

        # Initialize services
        self.bv_context = BVContextBuilder.build(business_view)
        self.llm_sql_generator = LLMSQLGenerator()
        self.tql_adapter = TQLAdapter(db_path)
        self.narrative_generator = NarrativeGenerator()

        logger.info(
            "orchestrator_initialized",
            business_view=business_view.id,
            db_path=db_path,
            flow="llm_sql_generation",
        )

    async def generate_insight(self, user_question: str) -> InsightResponse:
        """
        Generate insight from user question using LLM-generated SQL.

        This is the main entry point for the Intelligent Feed system.

        Args:
            user_question: Natural language question from user

        Returns:
            InsightResponse (triggered or not triggered)
        """
        logger.info("insight_generation_started", question=user_question)

        try:
            # STEP 1: Generate SQL and parse intent using LLM
            logger.info("step_1_llm_sql_generation")
            llm_response = await self.llm_sql_generator.generate(
                user_question, self.bv_context
            )
            
            intent = llm_response.parsed_intent
            plan = llm_response.tql_plan
            alert_config = self.llm_sql_generator.get_alert_config(llm_response.raw_llm_response)
            
            logger.info(
                "llm_sql_generated",
                metric=intent.metric,
                feed_type=intent.feed_type.value,
                queries_count=len(plan.get_all_queries()),
                alert_type=alert_config.get("alert_type", "unknown"),
            )

            # STEP 2: Execute LLM-generated SQL queries via TQL Adapter
            logger.info("step_2_executing_tql_queries")
            results = self.tql_adapter.execute(plan)
            logger.info(
                "tql_queries_executed",
                current_rows=len(results.current_period) if results.current_period is not None else 0,
                baseline_rows=len(results.baseline_period) if results.baseline_period is not None else 0,
            )

            # Check if we have valid data
            current_value = results.get_current_value()
            if current_value is None:
                logger.warning("no_data_for_time_range")
                return InsightResponseNotTriggered(
                    triggered=False,
                    explanation=f"No data found for {intent.metric} in the specified time range ({intent.time_range.start_date} to {intent.time_range.end_date}). The database contains data from 2023-2024.",
                    suggestion="Try a question with a date range in 2023-2024, for example: 'Why did revenue drop in Q3 2024?'",
                    metric=intent.metric,
                    time_range={
                        "start": str(intent.time_range.start_date),
                        "end": str(intent.time_range.end_date),
                    },
                    filters=intent.filters,
                    metrics={"current_value": 0.0, "baseline_value": 0.0},
                )

            # STEP 3: Run detection
            logger.info("step_3_running_detection", feed_type=intent.feed_type.value)
            detection_result = await self._run_detection(intent, results)
            logger.info(
                "detection_completed",
                triggered=detection_result.triggered,
                reason=detection_result.trigger_reason,
            )

            # STEP 4: If not triggered, return early with alert info
            if not detection_result.triggered:
                logger.info("insight_not_triggered", reason=detection_result.trigger_reason)
                return InsightResponseNotTriggered(
                    triggered=False,
                    explanation=detection_result.trigger_reason,
                    suggestion=self._generate_suggestion(detection_result, intent, alert_config),
                    metric=intent.metric,
                    time_range={
                        "start": str(intent.time_range.start_date),
                        "end": str(intent.time_range.end_date),
                    },
                    filters=intent.filters,
                    metrics=detection_result.metrics,
                )

            # STEP 5: Generate deep insight (only if triggered)
            logger.info("step_5_generating_deep_insight")
            deep_insight = await self._generate_deep_insight(results, detection_result)
            logger.info(
                "deep_insight_generated",
                drivers=len(deep_insight.top_drivers),
                explainability=deep_insight.explainability_score,
            )

            # STEP 6: Build charts
            logger.info("step_6_building_charts")
            # Use timeseries if available (for trend charts), otherwise skip trend chart
            has_timeseries = results.timeseries is not None and len(results.timeseries) > 0
            charts = ChartBuilderService.build_all_charts(
                metric_name=intent.metric,
                current_timeseries=results.timeseries if has_timeseries else None,
                baseline_timeseries=None,  # Only pass if we have actual timeseries baseline
                detection_result=detection_result,
                deep_insight=deep_insight,
            )
            logger.info("charts_built", count=len(charts))

            # STEP 7: Generate narrative
            logger.info("step_7_generating_narrative")
            what_happened, why_happened = await self.narrative_generator.generate(
                detection_result, deep_insight, intent
            )
            logger.info("narrative_generated")

            # STEP 8: Build response with alert information
            logger.info("step_8_building_response")
            response = InsightResponseTriggered(
                triggered=True,
                trigger_reason=detection_result.trigger_reason,
                what_happened=what_happened,
                why_happened=why_happened,
                charts=[chart.to_dict() for chart in charts],
                confidence=deep_insight.explainability_score,
                evidence={
                    "detection": detection_result.metrics,
                    "drivers": [d.to_dict() for d in deep_insight.get_top_n_drivers(10)],
                    "insight_summary": deep_insight.to_summary_dict(),
                    "alert": alert_config,
                    "llm_generated_sql": {
                        "current_period": plan.current_period_query,
                        "baseline_period": plan.baseline_period_query,
                        "timeseries": plan.timeseries_query,
                        "dimensional_breakdown": plan.dimensional_breakdown_query,
                    },
                },
                metric=intent.metric,
                time_range={
                    "start": str(intent.time_range.start_date),
                    "end": str(intent.time_range.end_date),
                },
                filters=intent.filters,
            )

            logger.info("insight_generation_completed", triggered=True)
            return response

        except Exception as e:
            logger.error("insight_generation_failed", error=str(e), exc_info=True)
            raise

    async def _run_detection(self, intent, results):
        """Run appropriate detection engine based on feed type."""
        if intent.feed_type.value == "absolute":
            # Absolute detection requires current and baseline values
            current_value = results.get_current_value() or 0
            baseline_value = results.get_baseline_value() or 0

            # Use new threshold_config if available, otherwise fall back to legacy threshold
            detection_result = AbsoluteDetectionEngine.detect(
                current_value=current_value,
                baseline_value=baseline_value,
                threshold_config=intent.threshold_config,
                threshold=intent.threshold,  # Legacy fallback
            )
        else:
            # ARIMA detection requires time-series
            if results.timeseries is not None and len(results.timeseries) > 0:
                detection_result = ARIMADetectionEngine.detect(
                    timeseries_df=results.timeseries,
                    sensitivity=intent.threshold if intent.threshold else None,
                )
            else:
                logger.warning("no_timeseries_data_for_arima")
                # Fallback to absolute if time-series not available
                current_value = results.get_current_value() or 0
                baseline_value = results.get_baseline_value() or 0
                detection_result = AbsoluteDetectionEngine.detect(
                    current_value=current_value,
                    baseline_value=baseline_value,
                    threshold_config=intent.threshold_config,
                    threshold=intent.threshold,
                )

        return detection_result

    async def _generate_deep_insight(self, results, detection_result):
        """Generate deep insight from query results."""
        # Get dimensional breakdowns
        current_breakdown = results.dimensional_breakdown
        baseline_breakdown = results.baseline_dimensional_breakdown

        if current_breakdown is None or len(current_breakdown) == 0:
            logger.warning("no_dimensional_breakdown_available")
            # Return empty insight
            from app.models.insight import DeepInsight
            return DeepInsight(
                top_drivers=[],
                explainability_score=0.0,
                evidence={"note": "No dimensional breakdown available"},
            )

        # Determine dimension name from breakdown
        # Assume first non-'value' column is the dimension
        dimension_cols = [col for col in current_breakdown.columns if col not in ['value', 'metric_value']]
        dimension_name = dimension_cols[0] if dimension_cols else "dimension"

        # Perform deep insight analysis
        deep_insight = DeepInsightEngine.analyze(
            current_breakdown=current_breakdown,
            baseline_breakdown=baseline_breakdown if baseline_breakdown is not None else current_breakdown.copy(),
            detection_result=detection_result,
            dimension_name=dimension_name,
        )

        return deep_insight

    def _generate_suggestion(self, detection_result, intent, alert_config: Dict[str, Any]) -> str:
        """Generate suggestion when insight is not triggered."""
        alert_type = alert_config.get("alert_type", "unknown")
        threshold = alert_config.get("threshold_percent", 5.0)
        
        if detection_result.feed_type.value == "absolute":
            return (
                f"The change in {intent.metric} ({alert_type}) is within normal variance (threshold: {threshold}%). "
                f"Consider lowering the threshold or checking a different time period."
            )
        else:
            return (
                f"No significant anomalies detected in {intent.metric}. "
                f"Try adjusting the sensitivity or analyzing a different metric."
            )

    def close(self):
        """Close database connections."""
        self.tql_adapter.close()
        logger.info("orchestrator_closed")
