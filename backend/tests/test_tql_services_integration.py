"""Integration tests for TQL services (Planner, Validator, Adapter)."""

import pytest
from datetime import date, timedelta
from pathlib import Path
import tempfile
import os

from app.models.business_view import (
    BusinessView,
    Table,
    Column,
    ColumnType,
    Join,
    JoinType,
    Measure,
    Dimension,
    TimeDimension,
    CalendarRules,
    Granularity,
)
from app.models.intent import (
    ParsedIntent,
    TimeRange,
    BaselineConfig,
    BaselineType,
    FeedType,
)
from app.services.bv_context_builder import BVContextBuilder
from app.services.tql_planner import TQLPlanner
from app.services.plan_validator import PlanValidator, ValidationError
from app.services.tql_adapter import TQLAdapter, QueryExecutionError


@pytest.fixture
def sample_business_view():
    """Create a sample Business View for testing."""
    return BusinessView(
        id="bv_sales",
        name="Sales Analytics",
        description="Sales data with customer and product dimensions",
        tables=[
            Table(
                name="sales",
                schema="public",
                columns=[
                    Column(name="sale_id", type=ColumnType.INTEGER),
                    Column(name="sale_date", type=ColumnType.DATE),
                    Column(name="revenue", type=ColumnType.FLOAT),
                    Column(name="quantity", type=ColumnType.INTEGER),
                    Column(name="customer_id", type=ColumnType.INTEGER),
                    Column(name="product_id", type=ColumnType.INTEGER),
                ],
            ),
            Table(
                name="customers",
                schema="public",
                columns=[
                    Column(name="customer_id", type=ColumnType.INTEGER),
                    Column(name="customer_name", type=ColumnType.STRING),
                    Column(name="region", type=ColumnType.STRING),
                    Column(name="segment", type=ColumnType.STRING),
                ],
            ),
            Table(
                name="products",
                schema="public",
                columns=[
                    Column(name="product_id", type=ColumnType.INTEGER),
                    Column(name="product_name", type=ColumnType.STRING),
                    Column(name="category", type=ColumnType.STRING),
                ],
            ),
        ],
        joins=[
            Join(
                left_table="sales",
                right_table="customers",
                left_key="customer_id",
                right_key="customer_id",
                join_type=JoinType.LEFT,
            ),
            Join(
                left_table="sales",
                right_table="products",
                left_key="product_id",
                right_key="product_id",
                join_type=JoinType.LEFT,
            ),
        ],
        measures=[
            Measure(
                name="Total Revenue",
                expression="SUM(revenue)",
                format="currency",
                description="Total revenue from sales",
            ),
            Measure(
                name="Total Quantity",
                expression="SUM(quantity)",
                format="number",
                description="Total quantity sold",
            ),
        ],
        dimensions=[
            Dimension(
                name="Region",
                column="region",
                table="customers",
                description="Customer region",
            ),
            Dimension(
                name="Segment",
                column="segment",
                table="customers",
                description="Customer segment",
            ),
            Dimension(
                name="Category",
                column="category",
                table="products",
                description="Product category",
            ),
        ],
        time_dimension=TimeDimension(
            column="sale_date",
            table="sales",
            granularity=Granularity.DAY,
        ),
        calendar_rules=CalendarRules(
            fiscal_year_start=1,  # January
            week_start="monday",
        ),
    )


@pytest.fixture
def sample_intent():
    """Create a sample parsed intent for testing."""
    end_date = date.today()
    start_date = end_date - timedelta(days=30)

    return ParsedIntent(
        metric="Total Revenue",
        time_range=TimeRange(
            start_date=start_date,
            end_date=end_date,
            granularity="day",
        ),
        filters={"Region": "APAC"},
        baseline=BaselineConfig(type=BaselineType.PREVIOUS_PERIOD),
        feed_type=FeedType.ABSOLUTE,
    )


@pytest.fixture
def temp_database():
    """Create a temporary SQLite database for testing."""
    # Create temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)

    # Initialize with sample schema
    adapter = TQLAdapter(f"sqlite:///{db_path}")

    schema_sql = """
    CREATE TABLE IF NOT EXISTS sales (
        sale_id INTEGER PRIMARY KEY,
        sale_date DATE NOT NULL,
        revenue REAL NOT NULL,
        quantity INTEGER NOT NULL,
        customer_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL
    );

    CREATE TABLE IF NOT EXISTS customers (
        customer_id INTEGER PRIMARY KEY,
        customer_name TEXT NOT NULL,
        region TEXT NOT NULL,
        segment TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS products (
        product_id INTEGER PRIMARY KEY,
        product_name TEXT NOT NULL,
        category TEXT NOT NULL
    );

    -- Insert sample data
    INSERT INTO customers (customer_id, customer_name, region, segment) VALUES
        (1, 'Customer A', 'APAC', 'Enterprise'),
        (2, 'Customer B', 'APAC', 'SMB'),
        (3, 'Customer C', 'EMEA', 'Enterprise');

    INSERT INTO products (product_id, product_name, category) VALUES
        (1, 'Product X', 'Electronics'),
        (2, 'Product Y', 'Software');

    -- Insert sample sales data
    INSERT INTO sales (sale_id, sale_date, revenue, quantity, customer_id, product_id) VALUES
        (1, '2026-01-01', 1000.0, 10, 1, 1),
        (2, '2026-01-02', 1500.0, 15, 2, 2),
        (3, '2026-01-03', 2000.0, 20, 1, 1),
        (4, '2025-12-01', 1200.0, 12, 1, 1),
        (5, '2025-12-02', 1800.0, 18, 2, 2);
    """

    adapter.initialize_database(schema_sql)

    yield adapter

    # Cleanup
    try:
        os.unlink(db_path)
    except Exception:
        pass


class TestTQLPlanner:
    """Tests for TQL Planner service."""

    def test_generate_basic_plan(self, sample_business_view, sample_intent):
        """Test generating a basic TQL plan."""
        plan = TQLPlanner.generate(sample_intent, sample_business_view)

        assert plan is not None
        assert plan.current_period_query is not None
        assert plan.baseline_period_query is not None
        assert "SELECT" in plan.current_period_query.upper()
        assert "FROM" in plan.current_period_query.upper()
        assert "SUM(revenue)" in plan.current_period_query

    def test_generate_plan_with_filters(self, sample_business_view, sample_intent):
        """Test that filters are properly included in queries."""
        plan = TQLPlanner.generate(sample_intent, sample_business_view)

        assert "Region" in plan.current_period_query or "region" in plan.current_period_query
        assert "APAC" in plan.current_period_query

    def test_generate_plan_with_baseline(self, sample_business_view, sample_intent):
        """Test baseline query generation."""
        plan = TQLPlanner.generate(sample_intent, sample_intent)

        assert plan.requires_baseline()
        assert plan.baseline_period_query is not None

    def test_generate_timeseries_for_arima(self, sample_business_view):
        """Test time-series query generation for ARIMA."""
        intent = ParsedIntent(
            metric="Total Revenue",
            time_range=TimeRange(
                start_date=date(2026, 1, 1),
                end_date=date(2026, 1, 31),
                granularity="day",
            ),
            filters={},
            feed_type=FeedType.ARIMA,
        )

        plan = TQLPlanner.generate(intent, sample_business_view)

        assert plan.requires_timeseries()
        assert plan.timeseries_query is not None
        assert "GROUP BY" in plan.timeseries_query.upper()
        assert "ORDER BY" in plan.timeseries_query.upper()

    def test_generate_dimensional_breakdown(self, sample_business_view, sample_intent):
        """Test dimensional breakdown query generation."""
        plan = TQLPlanner.generate(sample_intent, sample_business_view)

        assert plan.requires_dimensional_breakdown()
        assert plan.dimensional_breakdown_query is not None
        assert plan.baseline_dimensional_breakdown_query is not None

    def test_invalid_measure_raises_error(self, sample_business_view):
        """Test that invalid measure raises ValueError."""
        intent = ParsedIntent(
            metric="Invalid Metric",
            time_range=TimeRange(
                start_date=date(2026, 1, 1),
                end_date=date(2026, 1, 31),
            ),
            filters={},
        )

        with pytest.raises(ValueError, match="not found"):
            TQLPlanner.generate(intent, sample_business_view)


class TestPlanValidator:
    """Tests for Plan Validator service."""

    def test_validate_safe_plan(self, sample_business_view, sample_intent):
        """Test validating a safe SQL plan."""
        plan = TQLPlanner.generate(sample_intent, sample_business_view)
        bv_context = BVContextBuilder.build(sample_business_view)

        # Should not raise any errors
        validated_plan = PlanValidator.validate(plan, bv_context)
        assert validated_plan is plan

    def test_detect_dangerous_keywords(self, sample_business_view):
        """Test detection of dangerous SQL keywords."""
        from app.models.plan import TQLPlan, PlanMetadata

        dangerous_plan = TQLPlan(
            current_period_query="SELECT * FROM sales; DROP TABLE sales;",
            metadata=PlanMetadata(),
        )

        bv_context = BVContextBuilder.build(sample_business_view)

        with pytest.raises(ValidationError, match="DROP"):
            PlanValidator.validate(dangerous_plan, bv_context)

    def test_detect_sql_injection(self, sample_business_view):
        """Test detection of SQL injection patterns."""
        from app.models.plan import TQLPlan, PlanMetadata

        injection_plan = TQLPlan(
            current_period_query="SELECT * FROM sales WHERE region = 'APAC' OR 1=1 --",
            metadata=PlanMetadata(),
        )

        bv_context = BVContextBuilder.build(sample_business_view)

        # Should detect suspicious comment pattern
        with pytest.raises(ValidationError):
            PlanValidator.validate(injection_plan, bv_context)

    def test_detect_union_attack(self, sample_business_view):
        """Test detection of UNION-based attacks."""
        from app.models.plan import TQLPlan, PlanMetadata

        union_plan = TQLPlan(
            current_period_query="SELECT revenue FROM sales UNION SELECT password FROM users",
            metadata=PlanMetadata(),
        )

        bv_context = BVContextBuilder.build(sample_business_view)

        with pytest.raises(ValidationError, match="UNION"):
            PlanValidator.validate(union_plan, bv_context)

    def test_reject_non_select_queries(self, sample_business_view):
        """Test rejection of non-SELECT queries."""
        from app.models.plan import TQLPlan, PlanMetadata

        update_plan = TQLPlan(
            current_period_query="UPDATE sales SET revenue = 0",
            metadata=PlanMetadata(),
        )

        bv_context = BVContextBuilder.build(sample_business_view)

        with pytest.raises(ValidationError, match="SELECT"):
            PlanValidator.validate(update_plan, bv_context)


class TestTQLAdapter:
    """Tests for TQL Adapter service."""

    def test_connection(self, temp_database):
        """Test database connection."""
        assert temp_database.test_connection()

    def test_list_tables(self, temp_database):
        """Test listing database tables."""
        tables = temp_database.list_tables()

        assert "sales" in tables
        assert "customers" in tables
        assert "products" in tables

    def test_execute_simple_query(self, temp_database):
        """Test executing a simple query."""
        query = "SELECT COUNT(*) as count FROM sales"
        df = temp_database.execute_raw_query(query)

        assert df is not None
        assert len(df) == 1
        assert df.iloc[0]['count'] >= 0

    def test_execute_plan(self, temp_database, sample_business_view):
        """Test executing a complete TQL plan."""
        intent = ParsedIntent(
            metric="Total Revenue",
            time_range=TimeRange(
                start_date=date(2026, 1, 1),
                end_date=date(2026, 1, 31),
                granularity="day",
            ),
            filters={},
            baseline=BaselineConfig(type=BaselineType.PREVIOUS_PERIOD),
        )

        plan = TQLPlanner.generate(intent, sample_business_view)
        results = temp_database.execute(plan)

        assert results is not None
        assert results.current_period is not None
        assert results.has_baseline()

        # Check we got numeric values
        current_value = results.get_current_value()
        baseline_value = results.get_baseline_value()

        assert current_value is not None
        assert baseline_value is not None
        assert isinstance(current_value, float)
        assert isinstance(baseline_value, float)

    def test_execute_plan_with_filters(self, temp_database, sample_business_view):
        """Test executing a plan with dimension filters."""
        intent = ParsedIntent(
            metric="Total Revenue",
            time_range=TimeRange(
                start_date=date(2026, 1, 1),
                end_date=date(2026, 1, 31),
            ),
            filters={"Region": "APAC"},
        )

        plan = TQLPlanner.generate(intent, sample_business_view)
        results = temp_database.execute(plan)

        assert results.current_period is not None
        current_value = results.get_current_value()
        assert current_value is not None

    def test_invalid_query_raises_error(self, temp_database):
        """Test that invalid SQL raises QueryExecutionError."""
        with pytest.raises(QueryExecutionError):
            temp_database.execute_raw_query("SELECT * FROM nonexistent_table")

    def test_table_info(self, temp_database):
        """Test getting table schema information."""
        info = temp_database.get_table_info("sales")

        assert info is not None
        assert len(info) > 0

    def test_row_count(self, temp_database):
        """Test getting row count."""
        count = temp_database.get_row_count("sales")

        assert count is not None
        assert count >= 0


class TestIntegration:
    """Integration tests for all three services working together."""

    def test_full_pipeline(self, temp_database, sample_business_view, sample_intent):
        """Test complete pipeline: Plan -> Validate -> Execute."""
        # 1. Generate plan
        plan = TQLPlanner.generate(sample_intent, sample_business_view)
        assert plan is not None

        # 2. Validate plan
        bv_context = BVContextBuilder.build(sample_business_view)
        validated_plan = PlanValidator.validate(plan, bv_context)
        assert validated_plan is plan

        # 3. Execute plan
        results = temp_database.execute(validated_plan)
        assert results is not None

        # 4. Verify results
        assert results.get_current_value() is not None
        assert results.get_baseline_value() is not None

    def test_arima_pipeline(self, temp_database, sample_business_view):
        """Test pipeline with ARIMA feed type."""
        intent = ParsedIntent(
            metric="Total Revenue",
            time_range=TimeRange(
                start_date=date(2026, 1, 1),
                end_date=date(2026, 1, 31),
            ),
            filters={},
            feed_type=FeedType.ARIMA,
        )

        # Generate plan
        plan = TQLPlanner.generate(intent, sample_business_view)
        assert plan.requires_timeseries()

        # Validate
        bv_context = BVContextBuilder.build(sample_business_view)
        PlanValidator.validate(plan, bv_context)

        # Execute
        results = temp_database.execute(plan)
        assert results.has_timeseries()
        assert results.timeseries is not None

    def test_dimensional_breakdown_pipeline(self, temp_database, sample_business_view, sample_intent):
        """Test pipeline with dimensional breakdown."""
        # Generate plan
        plan = TQLPlanner.generate(sample_intent, sample_business_view)
        assert plan.requires_dimensional_breakdown()

        # Validate
        bv_context = BVContextBuilder.build(sample_business_view)
        PlanValidator.validate(plan, bv_context)

        # Execute
        results = temp_database.execute(plan)
        assert results.has_dimensional_breakdown()
        assert results.dimensional_breakdown is not None
        assert results.baseline_dimensional_breakdown is not None
