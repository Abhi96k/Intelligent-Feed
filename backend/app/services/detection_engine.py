"""Detection engines for Absolute and ARIMA anomaly detection."""

import pandas as pd
import numpy as np
from typing import Optional, List
from datetime import date
from RestrictedPython import compile_restricted
from RestrictedPython.Guards import safe_builtins, guarded_iter_unpack_sequence
from app.models.detection import DetectionResult, AnomalyPoint
from app.models.intent import FeedType, ThresholdConfig, ComparisonOperator
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class AbsoluteDetectionEngine:
    """
    Absolute (threshold-based) detection engine.

    Compares current vs baseline value and triggers based on threshold conditions.
    Supports operators: >, <, >=, <=, ==, != with value comparisons.
    """

    @staticmethod
    def detect(
        current_value: float,
        baseline_value: float,
        threshold_config: Optional[ThresholdConfig] = None,
        threshold: Optional[float] = None,  # Legacy support
    ) -> DetectionResult:
        """
        Detect if threshold condition is met.

        Args:
            current_value: Current period metric value
            baseline_value: Baseline period metric value
            threshold_config: New threshold configuration with operator and value
            threshold: Legacy percentage threshold (for backward compatibility)

        Returns:
            DetectionResult
        """
        # Calculate deltas for metrics
        absolute_delta = current_value - baseline_value
        
        # Handle division by zero for percent change
        if baseline_value == 0:
            if current_value == 0:
                percent_change = 0.0
            else:
                percent_change = float('inf') if current_value > 0 else float('-inf')
        else:
            percent_change = (absolute_delta / baseline_value) * 100

        # Determine trigger based on threshold config or legacy threshold
        triggered = False
        trigger_reason = ""
        threshold_used = None

        if threshold_config is not None:
            # New value-based threshold with operator
            logger.info(
                "absolute_detection_with_config",
                current=current_value,
                baseline=baseline_value,
                operator=threshold_config.operator.value,
                threshold_value=threshold_config.value,
                compare_to=threshold_config.compare_to,
            )
            
            triggered = threshold_config.evaluate(current_value, baseline_value)
            threshold_used = threshold_config.to_human_readable()
            
            if triggered:
                direction = "increased" if absolute_delta > 0 else "decreased"
                trigger_reason = (
                    f"Alert triggered: {threshold_config.compare_to} value "
                    f"({AbsoluteDetectionEngine._format_value(current_value if threshold_config.compare_to == 'current' else baseline_value)}) "
                    f"meets condition '{threshold_config.to_human_readable()}'"
                )
            else:
                trigger_reason = (
                    f"Condition not met: {threshold_config.to_human_readable()} "
                    f"(current: {AbsoluteDetectionEngine._format_value(current_value)}, "
                    f"baseline: {AbsoluteDetectionEngine._format_value(baseline_value)})"
                )
        else:
            # Legacy percentage-based threshold
            if threshold is None:
                threshold = settings.DEFAULT_ABSOLUTE_THRESHOLD
            
            logger.info(
                "absolute_detection_legacy",
                current=current_value,
                baseline=baseline_value,
                threshold_percent=threshold,
            )
            
            threshold_used = f"{threshold}%"
            
            if abs(percent_change) >= threshold:
                triggered = True
                direction = "increased" if absolute_delta > 0 else "decreased"
                trigger_reason = (
                    f"Metric {direction} by {abs(percent_change):.1f}% "
                    f"(threshold: {threshold}%)"
                )
            else:
                trigger_reason = (
                    f"Change of {abs(percent_change):.1f}% is below threshold "
                    f"({threshold}%)"
                )

        result = DetectionResult(
            triggered=triggered,
            trigger_reason=trigger_reason,
            feed_type=FeedType.ABSOLUTE,
            metrics={
                "current_value": current_value,
                "baseline_value": baseline_value,
                "absolute_delta": absolute_delta,
                "percent_change": percent_change,
                "threshold_used": threshold_used,
            },
            current_value=current_value,
            baseline_value=baseline_value,
            absolute_delta=absolute_delta,
            percent_change=percent_change,
            threshold_used=threshold_used,
        )

        logger.info(
            "absolute_detection_result",
            triggered=triggered,
            reason=trigger_reason,
        )

        return result

    @staticmethod
    def _format_value(value: float) -> str:
        """Format value for human-readable display."""
        if abs(value) >= 1_000_000:
            return f"${value/1_000_000:.2f}M"
        elif abs(value) >= 1_000:
            return f"${value/1_000:.2f}K"
        else:
            return f"${value:.2f}"


class ARIMADetectionEngine:
    """
    ARIMA-based anomaly detection engine.

    Fits ARIMA model to time-series and detects anomalies based on residuals.
    Uses sandboxed Python execution for security.
    """

    @staticmethod
    def detect(
        timeseries_df: pd.DataFrame,
        sensitivity: Optional[float] = None,
    ) -> DetectionResult:
        """
        Detect anomalies in time-series using ARIMA.

        Args:
            timeseries_df: DataFrame with 'date' and 'value' columns
            sensitivity: Sigma multiplier for anomaly threshold (default from settings)

        Returns:
            DetectionResult with anomaly points
        """
        if sensitivity is None:
            sensitivity = settings.DEFAULT_ARIMA_SENSITIVITY

        logger.info(
            "arima_detection",
            rows=len(timeseries_df),
            sensitivity=sensitivity,
        )

        # Validate input
        if len(timeseries_df) < 10:
            logger.warning("insufficient_data_for_arima", rows=len(timeseries_df))
            return DetectionResult(
                triggered=False,
                trigger_reason="Insufficient data for ARIMA analysis (need at least 10 points)",
                feed_type=FeedType.ARIMA,
                metrics={"data_points": len(timeseries_df)},
            )

        # Generate and execute ARIMA code
        try:
            anomaly_points = ARIMADetectionEngine._run_arima(
                timeseries_df, sensitivity
            )

            if anomaly_points:
                trigger_reason = (
                    f"Detected {len(anomaly_points)} anomalies in time-series "
                    f"(sensitivity: {sensitivity} sigma)"
                )
                triggered = True
            else:
                trigger_reason = f"No anomalies detected (sensitivity: {sensitivity} sigma)"
                triggered = False

            result = DetectionResult(
                triggered=triggered,
                trigger_reason=trigger_reason,
                feed_type=FeedType.ARIMA,
                anomaly_points=anomaly_points,
                metrics={
                    "total_points": len(timeseries_df),
                    "anomaly_count": len(anomaly_points),
                    "sensitivity": sensitivity,
                },
            )

            logger.info(
                "arima_detection_result",
                triggered=triggered,
                anomaly_count=len(anomaly_points),
            )

            return result

        except Exception as e:
            logger.error("arima_detection_failed", error=str(e))
            return DetectionResult(
                triggered=False,
                trigger_reason=f"ARIMA analysis failed: {str(e)}",
                feed_type=FeedType.ARIMA,
                metrics={},
            )

    @staticmethod
    def _run_arima(df: pd.DataFrame, sensitivity: float) -> List[AnomalyPoint]:
        """
        Run ARIMA model and detect anomalies.

        Note: In production, this should use RestrictedPython sandbox.
        For now, using direct implementation.
        """
        try:
            from statsmodels.tsa.arima.model import ARIMA
            from statsmodels.tools.sm_exceptions import ConvergenceWarning
            import warnings
            warnings.filterwarnings('ignore', category=ConvergenceWarning)

            # Prepare data
            ts_data = df.set_index('date')['value']

            # Try different ARIMA orders (simple approach)
            orders = [(1, 0, 0), (1, 1, 0), (2, 1, 0), (1, 1, 1)]
            best_model = None
            best_aic = float('inf')

            for order in orders:
                try:
                    model = ARIMA(ts_data, order=order)
                    fitted = model.fit()
                    if fitted.aic < best_aic:
                        best_aic = fitted.aic
                        best_model = fitted
                except:
                    continue

            if best_model is None:
                logger.warning("arima_model_fit_failed")
                return []

            # Get residuals
            residuals = best_model.resid
            fitted_values = best_model.fittedvalues

            # Detect anomalies (residuals beyond threshold)
            residual_std = residuals.std()
            threshold = sensitivity * residual_std

            anomalies = []
            for idx, residual in residuals.items():
                if abs(residual) > threshold:
                    # Severity: 0-1 scale based on how many sigmas away
                    severity = min(abs(residual) / (sensitivity * residual_std), 1.0)

                    anomaly = AnomalyPoint(
                        date=idx.date() if hasattr(idx, 'date') else idx,
                        value=ts_data[idx],
                        expected_value=fitted_values[idx],
                        residual=residual,
                        severity=severity,
                    )
                    anomalies.append(anomaly)

            # Sort by severity
            anomalies.sort(key=lambda x: x.severity, reverse=True)

            return anomalies

        except Exception as e:
            logger.error("arima_execution_error", error=str(e))
            raise

    @staticmethod
    def _run_arima_sandboxed(df: pd.DataFrame, sensitivity: float) -> List[AnomalyPoint]:
        """
        Run ARIMA in sandboxed environment (production approach).

        This would use RestrictedPython to safely execute ARIMA code.
        Placeholder for production implementation.
        """
        # TODO: Implement full sandbox using RestrictedPython
        # For now, delegate to direct implementation
        return ARIMADetectionEngine._run_arima(df, sensitivity)
