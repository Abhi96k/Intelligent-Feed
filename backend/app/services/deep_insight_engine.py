"""Deep Insight Engine - Root cause analysis and contribution shift analysis."""

import pandas as pd
import numpy as np
from typing import List, Dict, Any
from app.models.insight import DeepInsight, Driver
from app.models.detection import DetectionResult
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class DeepInsightEngine:
    """
    Analyzes root causes of metric changes through contribution shift analysis.

    This engine performs dimensional breakdown and identifies which dimension
    members contributed most to the observed change.
    """

    @staticmethod
    def analyze(
        current_breakdown: pd.DataFrame,
        baseline_breakdown: pd.DataFrame,
        detection_result: DetectionResult,
        dimension_name: str = "dimension",
    ) -> DeepInsight:
        """
        Perform deep root-cause analysis.

        Args:
            current_breakdown: DataFrame with [dimension, value] for current period
            baseline_breakdown: DataFrame with [dimension, value] for baseline period
            detection_result: Result from detection engine
            dimension_name: Name of the dimension column

        Returns:
            DeepInsight with top drivers and explainability score
        """
        logger.info("deep_insight_analysis_started", dimension=dimension_name)

        # Get total values
        total_current = current_breakdown['metric_value'].sum()
        total_baseline = baseline_breakdown['metric_value'].sum()
        total_change = total_current - total_baseline

        logger.debug(
            "totals",
            current=total_current,
            baseline=total_baseline,
            change=total_change,
        )

        # Merge dataframes to compare
        merged = pd.merge(
            current_breakdown,
            baseline_breakdown,
            on=dimension_name,
            how='outer',
            suffixes=('_current', '_baseline'),
        ).fillna(0)

        # Calculate contribution shifts
        drivers = []
        for _, row in merged.iterrows():
            member = row[dimension_name]
            value_current = row['metric_value_current']
            value_baseline = row['metric_value_baseline']

            # Contribution percentages
            contrib_current = (
                (value_current / total_current * 100) if total_current != 0 else 0
            )
            contrib_baseline = (
                (value_baseline / total_baseline * 100) if total_baseline != 0 else 0
            )

            # Contribution shift (percentage points)
            shift = contrib_current - contrib_baseline

            # Impact on total change
            # Impact = shift in contribution × total current value
            impact = (shift / 100) * total_current

            # Filter out insignificant contributors
            if abs(contrib_current) < settings.MIN_CONTRIBUTION_THRESHOLD and \
               abs(contrib_baseline) < settings.MIN_CONTRIBUTION_THRESHOLD:
                continue

            driver = Driver(
                dimension=dimension_name,
                member=str(member),
                impact=impact,
                contribution_current=contrib_current,
                contribution_baseline=contrib_baseline,
                shift=shift,
                value_current=value_current,
                value_baseline=value_baseline,
            )
            drivers.append(driver)

        # Sort by absolute impact
        drivers.sort(key=lambda d: abs(d.impact), reverse=True)

        # Take top N drivers
        top_drivers = drivers[:settings.TOP_DRIVERS_TO_RETURN]

        # Calculate explainability score
        explainability_score = DeepInsightEngine._calculate_explainability(
            top_drivers, total_change, merged
        )

        # Calculate impact summaries
        total_positive = sum(d.impact for d in top_drivers if d.impact > 0)
        total_negative = sum(d.impact for d in top_drivers if d.impact < 0)
        net_impact = total_positive + total_negative

        # Build evidence dictionary
        evidence = {
            "total_current": total_current,
            "total_baseline": total_baseline,
            "total_change": total_change,
            "drivers_analyzed": len(drivers),
            "drivers_returned": len(top_drivers),
            "contribution_data": merged.to_dict('records'),
        }

        insight = DeepInsight(
            top_drivers=top_drivers,
            explainability_score=explainability_score,
            evidence=evidence,
            total_positive_impact=total_positive,
            total_negative_impact=total_negative,
            net_impact=net_impact,
        )

        logger.info(
            "deep_insight_completed",
            drivers_found=len(top_drivers),
            explainability=explainability_score,
        )

        return insight

    @staticmethod
    def _calculate_explainability(
        top_drivers: List[Driver],
        total_change: float,
        full_data: pd.DataFrame,
    ) -> float:
        """
        Calculate explainability score (0-100).

        Based on:
        - Coverage: % of total change explained by top drivers
        - Consistency: variance in driver impacts
        - Confidence: number of significant drivers
        """
        if total_change == 0:
            return 50.0  # Neutral score when no change

        # Coverage: how much of the change is explained
        explained_change = sum(abs(d.impact) for d in top_drivers)
        coverage = min((explained_change / abs(total_change)) * 100, 100)

        # Confidence: having more significant drivers increases confidence
        num_significant = len([d for d in top_drivers if abs(d.impact) > abs(total_change) * 0.05])
        confidence_factor = min(num_significant / 5, 1.0) * 100  # Normalize to 5 drivers

        # Consistency: lower variance in impacts means more consistent pattern
        if len(top_drivers) > 1:
            impacts = [abs(d.impact) for d in top_drivers]
            impact_cv = np.std(impacts) / np.mean(impacts) if np.mean(impacts) > 0 else 0
            consistency = max(0, 100 - (impact_cv * 20))  # Scale coefficient of variation
        else:
            consistency = 50

        # Weighted average
        explainability = (
            coverage * 0.5 +
            confidence_factor * 0.3 +
            consistency * 0.2
        )

        return min(max(explainability, 0), 100)

    @staticmethod
    def analyze_multiple_dimensions(
        dimension_breakdowns: Dict[str, tuple[pd.DataFrame, pd.DataFrame]],
        detection_result: DetectionResult,
    ) -> Dict[str, DeepInsight]:
        """
        Analyze multiple dimensions in parallel.

        Args:
            dimension_breakdowns: Dict mapping dimension name to (current_df, baseline_df)
            detection_result: Detection result

        Returns:
            Dict mapping dimension name to DeepInsight
        """
        insights = {}

        for dimension_name, (current_df, baseline_df) in dimension_breakdowns.items():
            try:
                insight = DeepInsightEngine.analyze(
                    current_df,
                    baseline_df,
                    detection_result,
                    dimension_name,
                )
                insights[dimension_name] = insight
            except Exception as e:
                logger.error(
                    "dimension_analysis_failed",
                    dimension=dimension_name,
                    error=str(e),
                )

        return insights

    @staticmethod
    def get_unified_top_drivers(
        insights: Dict[str, DeepInsight],
        top_n: int = 10,
    ) -> List[Driver]:
        """
        Get unified list of top drivers across all dimensions.

        Args:
            insights: Dict of dimension name to DeepInsight
            top_n: Number of top drivers to return

        Returns:
            Sorted list of top drivers across all dimensions
        """
        all_drivers = []
        for insight in insights.values():
            all_drivers.extend(insight.top_drivers)

        # Sort by absolute impact
        all_drivers.sort(key=lambda d: abs(d.impact), reverse=True)

        return all_drivers[:top_n]
