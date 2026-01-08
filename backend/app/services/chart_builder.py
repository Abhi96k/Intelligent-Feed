"""Chart Builder - Generate chart specifications for visual evidence."""

import pandas as pd
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.models.chart import (
    ChartSpec,
    ChartType,
    AxisConfig,
    Series,
    Annotation,
    AnnotationType,
)
from app.models.detection import DetectionResult, AnomalyPoint
from app.models.insight import DeepInsight, Driver
from app.core.logging import get_logger

logger = get_logger(__name__)


class ChartBuilderService:
    """
    Builds chart specifications for visual evidence.

    Charts serve as proof for insights and replace dashboard navigation.
    """

    @staticmethod
    def build_primary_trend_chart(
        metric_name: str,
        current_timeseries: pd.DataFrame,
        baseline_timeseries: Optional[pd.DataFrame] = None,
        detection_result: Optional[DetectionResult] = None,
    ) -> ChartSpec:
        """
        Build primary trend chart showing metric over time.

        Args:
            metric_name: Name of the metric
            current_timeseries: DataFrame with 'date' and 'value' columns
            baseline_timeseries: Optional baseline period data
            detection_result: Detection result for annotations

        Returns:
            ChartSpec for line chart
        """
        logger.info("building_trend_chart", metric=metric_name)

        # Normalize column names - handle different column naming conventions
        def get_date_value(row):
            """Extract date and value from row with flexible column names."""
            # Try different date column names
            date_val = None
            for col in ['date', 'Date', 'time', 'timestamp', 'period']:
                if col in row.index:
                    date_val = row[col]
                    break
            if date_val is None and len(row) > 0:
                date_val = row.iloc[0]  # First column as date
            
            # Try different value column names
            value_val = None
            for col in ['value', 'Value', 'metric_value', 'amount']:
                if col in row.index:
                    value_val = row[col]
                    break
            if value_val is None and len(row) > 1:
                value_val = row.iloc[-1]  # Last column as value
            
            return date_val, value_val

        # Prepare current period data
        current_data = []
        for _, row in current_timeseries.iterrows():
            date_val, value_val = get_date_value(row)
            if date_val is not None and value_val is not None:
                current_data.append({
                    "date": date_val.isoformat() if hasattr(date_val, 'isoformat') else str(date_val),
                    "value": float(value_val) if value_val is not None else 0.0
                })

        series = [
            Series(
                name="Current Period",
                data=current_data,
                color="#1f77b4",
                style="solid",
                line_width=3,
            )
        ]

        # Add baseline if provided
        if baseline_timeseries is not None and len(baseline_timeseries) > 0:
            baseline_data = []
            for _, row in baseline_timeseries.iterrows():
                date_val, value_val = get_date_value(row)
                if date_val is not None and value_val is not None:
                    baseline_data.append({
                        "date": date_val.isoformat() if hasattr(date_val, 'isoformat') else str(date_val),
                        "value": float(value_val) if value_val is not None else 0.0
                    })
            series.append(
                Series(
                    name="Baseline Period",
                    data=baseline_data,
                    color="#aaaaaa",
                    style="dashed",
                    line_width=2,
                )
            )

        # Add annotations
        annotations = []

        # Add threshold line for absolute detection
        if detection_result and detection_result.is_absolute() and detection_result.threshold_used:
            if detection_result.baseline_value:
                # Handle both numeric (legacy) and string (new format) threshold_used
                threshold_label = str(detection_result.threshold_used)
                
                # Only calculate threshold line for percentage-based thresholds
                if isinstance(detection_result.threshold_used, (int, float)):
                    threshold_value = detection_result.baseline_value * (
                        1 + detection_result.threshold_used / 100
                    )
                    annotations.append(
                        Annotation(
                            type=AnnotationType.THRESHOLD,
                            value=threshold_value,
                            label=f"Threshold ({threshold_label}%)",
                            color="#ff9800",
                            style="dashed",
                        )
                    )
                # For string-based thresholds (e.g., "current > 3000000"), add a reference line if possible
                elif isinstance(detection_result.threshold_used, str) and detection_result.current_value:
                    # Just add a label annotation without calculating a line
                    pass  # Skip threshold line for value-based comparisons

        # Add anomaly markers for ARIMA detection
        if detection_result and detection_result.is_arima() and detection_result.anomaly_points:
            anomaly_data = [
                {
                    "date": point.date.isoformat() if hasattr(point.date, 'isoformat') else str(point.date),
                    "value": float(point.value),
                    "severity": float(point.severity),
                }
                for point in detection_result.anomaly_points
            ]
            annotations.append(
                Annotation(
                    type=AnnotationType.ANOMALY,
                    points=anomaly_data,
                    label="Anomaly",
                    color="#ff0000",
                )
            )

        chart = ChartSpec(
            chart_id="trend_chart",
            chart_type=ChartType.LINE,
            title=f"{metric_name} Over Time",
            subtitle="Primary trend analysis",
            x_axis=AxisConfig(
                field="date",
                label="Date",
                format="date",
            ),
            y_axis=AxisConfig(
                field="value",
                label=metric_name,
                format="number",
            ),
            series=series,
            annotations=annotations,
            show_legend=True,
            show_grid=True,
            height=400,
        )

        logger.debug("trend_chart_built", series_count=len(series), annotations=len(annotations))

        return chart

    @staticmethod
    def build_driver_impact_chart(
        top_drivers: List[Driver],
        metric_name: str = "Impact",
    ) -> ChartSpec:
        """
        Build driver impact bar chart.

        Args:
            top_drivers: List of Driver objects from DeepInsight
            metric_name: Name for Y-axis label

        Returns:
            ChartSpec for bar chart
        """
        logger.info("building_driver_chart", driver_count=len(top_drivers))

        # Prepare data
        driver_data = []
        for driver in top_drivers:
            # Create label combining dimension and member
            label = f"{driver.member}"

            # Determine color based on positive/negative impact
            color = "#2ca02c" if driver.impact > 0 else "#d62728"

            driver_data.append({
                "driver": label,
                "impact": float(driver.impact),
                "dimension": driver.dimension,
                "color": color,
            })

        # Sort by absolute impact
        driver_data.sort(key=lambda x: abs(x['impact']), reverse=True)

        chart = ChartSpec(
            chart_id="driver_impact_chart",
            chart_type=ChartType.BAR,
            title="Top Contributing Drivers",
            subtitle="Ranked by impact on change",
            x_axis=AxisConfig(
                field="driver",
                label="Driver",
            ),
            y_axis=AxisConfig(
                field="impact",
                label=metric_name,
                format="number",
            ),
            series=[
                Series(
                    name="Impact",
                    data=driver_data,
                    color="#2ca02c",  # Default, will be overridden by individual colors
                )
            ],
            show_legend=False,
            show_grid=True,
            height=400,
        )

        logger.debug("driver_chart_built", drivers=len(driver_data))

        return chart

    @staticmethod
    def build_contribution_comparison_chart(
        top_drivers: List[Driver],
        metric_name: str = "Revenue",
    ) -> ChartSpec:
        """
        Build chart comparing current vs baseline contributions.

        Args:
            top_drivers: List of Driver objects
            metric_name: Name of metric

        Returns:
            ChartSpec for grouped bar chart
        """
        logger.info("building_contribution_chart", driver_count=len(top_drivers))

        # Prepare data for grouped bars
        driver_data = []
        for driver in top_drivers[:10]:  # Top 10 only for readability
            driver_data.append({
                "driver": f"{driver.member}",
                "current": float(driver.contribution_current),
                "baseline": float(driver.contribution_baseline),
            })

        # Create two series (current and baseline)
        current_series = Series(
            name="Current Period",
            data=[{"driver": d["driver"], "value": d["current"]} for d in driver_data],
            color="#1f77b4",
        )

        baseline_series = Series(
            name="Baseline Period",
            data=[{"driver": d["driver"], "value": d["baseline"]} for d in driver_data],
            color="#aaaaaa",
        )

        chart = ChartSpec(
            chart_id="contribution_comparison_chart",
            chart_type=ChartType.BAR,
            title="Contribution Shift Analysis",
            subtitle=f"Current vs Baseline contribution to {metric_name}",
            x_axis=AxisConfig(
                field="driver",
                label="Driver",
            ),
            y_axis=AxisConfig(
                field="value",
                label="Contribution %",
                format="percentage",
            ),
            series=[current_series, baseline_series],
            show_legend=True,
            show_grid=True,
            height=400,
        )

        logger.debug("contribution_chart_built")

        return chart

    @staticmethod
    def build_all_charts(
        metric_name: str,
        current_timeseries: pd.DataFrame,
        baseline_timeseries: Optional[pd.DataFrame],
        detection_result: DetectionResult,
        deep_insight: DeepInsight,
    ) -> List[ChartSpec]:
        """
        Build all required charts for an insight.

        Args:
            metric_name: Name of the metric
            current_timeseries: Current period time-series data
            baseline_timeseries: Baseline period time-series data
            detection_result: Detection result
            deep_insight: Deep insight analysis

        Returns:
            List of ChartSpec objects
        """
        logger.info("building_all_charts", metric=metric_name)

        charts = []

        # 1. Primary trend chart (only if time-series data is available)
        has_timeseries = (
            current_timeseries is not None and 
            len(current_timeseries) > 0 and 
            any(col in current_timeseries.columns for col in ['date', 'Date', 'time', 'timestamp', 'period'])
        )
        
        if has_timeseries:
            trend_chart = ChartBuilderService.build_primary_trend_chart(
                metric_name=metric_name,
                current_timeseries=current_timeseries,
                baseline_timeseries=baseline_timeseries,
                detection_result=detection_result,
            )
            charts.append(trend_chart)

        # 2. Driver impact chart (MANDATORY)
        if deep_insight.top_drivers:
            driver_chart = ChartBuilderService.build_driver_impact_chart(
                top_drivers=deep_insight.top_drivers,
                metric_name=f"{metric_name} Impact",
            )
            charts.append(driver_chart)

        # 3. Contribution comparison (OPTIONAL - if baseline exists)
        if baseline_timeseries is not None and deep_insight.top_drivers:
            contrib_chart = ChartBuilderService.build_contribution_comparison_chart(
                top_drivers=deep_insight.top_drivers,
                metric_name=metric_name,
            )
            charts.append(contrib_chart)

        logger.info("all_charts_built", count=len(charts))

        return charts
