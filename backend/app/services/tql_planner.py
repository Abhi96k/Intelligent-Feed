"""TQL Plan Generator - Converts parsed intent into executable SQL/TQL plans."""

from typing import List, Set, Dict
from app.models.business_view import BusinessView
from app.models.intent import ParsedIntent, FeedType
from app.models.plan import TQLPlan, PlanMetadata
from app.services.bv_context_builder import BVContext, BVContextBuilder
from app.core.logging import get_logger

logger = get_logger(__name__)


class TQLPlanner:
    """
    Generates SQL/TQL execution plans from parsed intent.

    Responsibilities:
    - Build SQL queries for current and baseline periods
    - Generate time-series queries for ARIMA detection
    - Create dimensional breakdown queries for RCA
    - Handle proper JOINs based on BV join graph
    - Respect time semantics and calendar rules
    """

    @staticmethod
    def generate(intent: ParsedIntent, business_view: BusinessView) -> TQLPlan:
        """
        Generate complete TQL plan from parsed intent.

        Args:
            intent: Parsed user intent
            business_view: Business View with schema and metadata

        Returns:
            TQLPlan with all necessary queries

        Raises:
            ValueError: If intent references invalid measures/dimensions
        """
        logger.info(
            "generating_tql_plan",
            metric=intent.metric,
            feed_type=intent.feed_type.value,
            has_baseline=intent.has_baseline(),
        )

        # Build BV context
        bv_context = BVContextBuilder.build(business_view)

        # Validate intent against BV
        TQLPlanner._validate_intent(intent, business_view)

        # Get measure info
        measure = business_view.get_measure(intent.metric)
        if not measure:
            raise ValueError(f"Measure '{intent.metric}' not found in Business View")

        # Determine required tables
        tables_needed = TQLPlanner._get_required_tables(intent, business_view, bv_context)

        # Build queries
        current_period_query = TQLPlanner._build_current_period_query(
            intent, measure, business_view, bv_context, tables_needed
        )

        baseline_period_query = None
        if intent.has_baseline():
            baseline_period_query = TQLPlanner._build_baseline_period_query(
                intent, measure, business_view, bv_context, tables_needed
            )

        timeseries_query = None
        if intent.feed_type == FeedType.ARIMA:
            timeseries_query = TQLPlanner._build_timeseries_query(
                intent, measure, business_view, bv_context, tables_needed
            )

        dimensional_breakdown_query = None
        baseline_dimensional_breakdown_query = None
        if intent.has_baseline():
            # Generate dimensional breakdowns for RCA
            dimensional_breakdown_query = TQLPlanner._build_dimensional_breakdown_query(
                intent, measure, business_view, bv_context, tables_needed, is_baseline=False
            )
            baseline_dimensional_breakdown_query = TQLPlanner._build_dimensional_breakdown_query(
                intent, measure, business_view, bv_context, tables_needed, is_baseline=True
            )

        # Build metadata
        metadata = PlanMetadata(
            estimated_rows=1000,  # Placeholder - could be enhanced with table stats
            complexity_score=TQLPlanner._calculate_complexity(tables_needed, intent),
            uses_joins=len(tables_needed) > 1,
            uses_aggregation=True,
            uses_window_functions=(intent.feed_type == FeedType.ARIMA),
        )

        plan = TQLPlan(
            current_period_query=current_period_query,
            baseline_period_query=baseline_period_query,
            timeseries_query=timeseries_query,
            dimensional_breakdown_query=dimensional_breakdown_query,
            baseline_dimensional_breakdown_query=baseline_dimensional_breakdown_query,
            metadata=metadata,
        )

        logger.info(
            "tql_plan_generated",
            queries_count=len(plan.get_all_queries()),
            uses_joins=metadata.uses_joins,
            complexity=metadata.complexity_score,
        )

        return plan

    @staticmethod
    def _validate_intent(intent: ParsedIntent, bv: BusinessView) -> None:
        """Validate that intent references valid BV entities."""
        # Check measure exists
        if not bv.get_measure(intent.metric):
            raise ValueError(f"Measure '{intent.metric}' not found in Business View")

        # Check dimension filters reference valid dimensions
        for dimension in intent.filters.keys():
            if not bv.get_dimension(dimension):
                raise ValueError(f"Dimension '{dimension}' not found in Business View")

    @staticmethod
    def _get_required_tables(
        intent: ParsedIntent, bv: BusinessView, context: BVContext
    ) -> List[str]:
        """Determine which tables are needed for this query."""
        tables = set()

        # Add table for measure
        measure_table = BVContextBuilder.get_table_for_measure(bv, intent.metric)
        if measure_table:
            tables.add(measure_table)

        # Add table for time dimension
        tables.add(bv.time_dimension.table)

        # Add tables for filtered dimensions
        for dim_name in intent.filters.keys():
            dim = bv.get_dimension(dim_name)
            if dim:
                tables.add(dim.table)

        # Add tables for all dimensions (for breakdown queries)
        for dim in bv.dimensions:
            tables.add(dim.table)

        return list(tables)

    @staticmethod
    def _build_from_clause(tables: List[str], bv: BusinessView) -> str:
        """Build FROM clause with necessary JOINs."""
        if len(tables) == 1:
            return f"FROM {tables[0]}"

        # Always start with sales_fact (the fact table) if it's in the list
        fact_table = "sales_fact"
        if fact_table in tables:
            start_table = fact_table
        else:
            start_table = tables[0]
        
        from_parts = [f"FROM {start_table}"]

        # Get required joins
        required_joins = BVContextBuilder.get_required_joins(bv, tables)

        # Add JOIN clauses - iterate multiple times to ensure all tables are connected
        joined_tables = {start_table}
        tables_to_join = set(tables) - joined_tables
        
        max_iterations = len(tables) + 1
        iteration = 0
        
        while tables_to_join and iteration < max_iterations:
            iteration += 1
            for join in required_joins:
                # Add join if it connects a new table
                if join['left_table'] in joined_tables and join['right_table'] not in joined_tables:
                    from_parts.append(
                        f"{join['join_type'].upper()} JOIN {join['right_table']} "
                        f"ON {join['left_table']}.{join['left_key']} = {join['right_table']}.{join['right_key']}"
                    )
                    joined_tables.add(join['right_table'])
                    tables_to_join.discard(join['right_table'])
                elif join['right_table'] in joined_tables and join['left_table'] not in joined_tables:
                    from_parts.append(
                        f"{join['join_type'].upper()} JOIN {join['left_table']} "
                        f"ON {join['right_table']}.{join['right_key']} = {join['left_table']}.{join['left_key']}"
                    )
                    joined_tables.add(join['left_table'])
                    tables_to_join.discard(join['left_table'])

        return "\n".join(from_parts)

    @staticmethod
    def _build_where_clause(intent: ParsedIntent, bv: BusinessView, is_baseline: bool = False) -> str:
        """Build WHERE clause with time range and filters."""
        conditions = []

        # Time range condition
        time_col = bv.time_dimension.full_column_name
        if is_baseline:
            baseline_range = intent.get_baseline_range()
            if baseline_range:
                conditions.append(baseline_range.to_sql_condition(time_col))
        else:
            conditions.append(intent.time_range.to_sql_condition(time_col))

        # Add dimension filters
        if intent.has_filters():
            for dim_name, values in intent.filters.items():
                dim = bv.get_dimension(dim_name)
                if dim:
                    col = dim.full_column_name
                    if isinstance(values, list):
                        # Multiple values: use IN
                        values_str = ", ".join(f"'{v}'" for v in values)
                        conditions.append(f"{col} IN ({values_str})")
                    else:
                        # Single value
                        conditions.append(f"{col} = '{values}'")

        if not conditions:
            return ""

        return "WHERE " + " AND ".join(conditions)

    @staticmethod
    def _build_current_period_query(
        intent: ParsedIntent,
        measure: "Measure",
        bv: BusinessView,
        context: BVContext,
        tables: List[str],
    ) -> str:
        """Build query for current period aggregated metric value."""
        select_clause = f"SELECT {measure.expression} AS metric_value"
        from_clause = TQLPlanner._build_from_clause(tables, bv)
        where_clause = TQLPlanner._build_where_clause(intent, bv, is_baseline=False)

        query_parts = [select_clause, from_clause]
        if where_clause:
            query_parts.append(where_clause)

        query = "\n".join(query_parts)
        logger.debug("current_period_query_built", query=query)
        return query

    @staticmethod
    def _build_baseline_period_query(
        intent: ParsedIntent,
        measure: "Measure",
        bv: BusinessView,
        context: BVContext,
        tables: List[str],
    ) -> str:
        """Build query for baseline period aggregated metric value."""
        select_clause = f"SELECT {measure.expression} AS metric_value"
        from_clause = TQLPlanner._build_from_clause(tables, bv)
        where_clause = TQLPlanner._build_where_clause(intent, bv, is_baseline=True)

        query_parts = [select_clause, from_clause]
        if where_clause:
            query_parts.append(where_clause)

        query = "\n".join(query_parts)
        logger.debug("baseline_period_query_built", query=query)
        return query

    @staticmethod
    def _build_timeseries_query(
        intent: ParsedIntent,
        measure: "Measure",
        bv: BusinessView,
        context: BVContext,
        tables: List[str],
    ) -> str:
        """Build time-series query for ARIMA detection."""
        time_col = bv.time_dimension.full_column_name

        select_clause = f"SELECT {time_col} AS date, {measure.expression} AS value"
        from_clause = TQLPlanner._build_from_clause(tables, bv)
        where_clause = TQLPlanner._build_where_clause(intent, bv, is_baseline=False)
        group_by_clause = f"GROUP BY {time_col}"
        order_by_clause = f"ORDER BY {time_col}"

        query_parts = [select_clause, from_clause]
        if where_clause:
            query_parts.append(where_clause)
        query_parts.append(group_by_clause)
        query_parts.append(order_by_clause)

        query = "\n".join(query_parts)
        logger.debug("timeseries_query_built", query=query)
        return query

    @staticmethod
    def _build_dimensional_breakdown_query(
        intent: ParsedIntent,
        measure: "Measure",
        bv: BusinessView,
        context: BVContext,
        tables: List[str],
        is_baseline: bool = False,
    ) -> str:
        """Build dimensional breakdown query for RCA."""
        # Select all dimensions and the measure
        dimension_cols = [dim.full_column_name for dim in bv.dimensions]
        dimension_names = [dim.name for dim in bv.dimensions]

        # Build SELECT with dimension aliases
        select_parts = []
        for dim in bv.dimensions:
            select_parts.append(f"{dim.full_column_name} AS {dim.name}")
        select_parts.append(f"{measure.expression} AS metric_value")

        select_clause = "SELECT " + ", ".join(select_parts)
        from_clause = TQLPlanner._build_from_clause(tables, bv)
        where_clause = TQLPlanner._build_where_clause(intent, bv, is_baseline=is_baseline)

        # Group by all dimensions
        group_by_clause = "GROUP BY " + ", ".join(dimension_cols)

        query_parts = [select_clause, from_clause]
        if where_clause:
            query_parts.append(where_clause)
        query_parts.append(group_by_clause)

        query = "\n".join(query_parts)
        logger.debug(
            "dimensional_breakdown_query_built",
            is_baseline=is_baseline,
            dimensions_count=len(dimension_cols),
        )
        return query

    @staticmethod
    def _calculate_complexity(tables: List[str], intent: ParsedIntent) -> int:
        """
        Calculate query complexity score (1-10).

        Factors:
        - Number of tables (joins)
        - Number of filters
        - Time-series analysis
        - Dimensional breakdown
        """
        score = 1

        # Tables/joins contribute 2 points per table
        score += len(tables) * 2

        # Filters contribute 1 point each
        score += len(intent.filters)

        # ARIMA adds 2 points
        if intent.feed_type == FeedType.ARIMA:
            score += 2

        # Baseline comparison adds 1 point
        if intent.has_baseline():
            score += 1

        # Cap at 10
        return min(score, 10)
