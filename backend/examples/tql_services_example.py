"""
Example usage of TQL services (Planner, Validator, Adapter).

This script demonstrates how to:
1. Define a Business View
2. Create a parsed intent
3. Generate a TQL plan
4. Validate the plan
5. Execute the plan against a database
"""

from datetime import date, timedelta
from pathlib import Path

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
from app.services.plan_validator import PlanValidator
from app.services.tql_adapter import TQLAdapter


def create_sample_business_view() -> BusinessView:
    """Create a sample Business View for demonstration."""
    return BusinessView(
        id="bv_ecommerce",
        name="E-Commerce Analytics",
        description="E-commerce sales data with customer and product analysis",
        tables=[
            Table(
                name="orders",
                schema="public",
                columns=[
                    Column(name="order_id", type=ColumnType.INTEGER),
                    Column(name="order_date", type=ColumnType.DATE),
                    Column(name="revenue", type=ColumnType.FLOAT),
                    Column(name="quantity", type=ColumnType.INTEGER),
                    Column(name="customer_id", type=ColumnType.INTEGER),
                    Column(name="product_id", type=ColumnType.INTEGER),
                ],
                description="Order transactions",
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
                description="Customer master data",
            ),
            Table(
                name="products",
                schema="public",
                columns=[
                    Column(name="product_id", type=ColumnType.INTEGER),
                    Column(name="product_name", type=ColumnType.STRING),
                    Column(name="category", type=ColumnType.STRING),
                    Column(name="price", type=ColumnType.FLOAT),
                ],
                description="Product catalog",
            ),
        ],
        joins=[
            Join(
                left_table="orders",
                right_table="customers",
                left_key="customer_id",
                right_key="customer_id",
                join_type=JoinType.LEFT,
            ),
            Join(
                left_table="orders",
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
                description="Total revenue from all orders",
            ),
            Measure(
                name="Order Count",
                expression="COUNT(DISTINCT order_id)",
                format="number",
                description="Number of unique orders",
            ),
            Measure(
                name="Average Order Value",
                expression="AVG(revenue)",
                format="currency",
                description="Average revenue per order",
            ),
        ],
        dimensions=[
            Dimension(
                name="Region",
                column="region",
                table="customers",
                description="Customer geographic region",
            ),
            Dimension(
                name="Segment",
                column="segment",
                table="customers",
                description="Customer business segment",
            ),
            Dimension(
                name="Category",
                column="category",
                table="products",
                description="Product category",
            ),
        ],
        time_dimension=TimeDimension(
            column="order_date",
            table="orders",
            granularity=Granularity.DAY,
            description="Order transaction date",
        ),
        calendar_rules=CalendarRules(
            fiscal_year_start=1,
            week_start="monday",
        ),
    )


def create_sample_intent() -> ParsedIntent:
    """Create a sample parsed intent."""
    # Analyze last 30 days vs previous 30 days
    end_date = date.today()
    start_date = end_date - timedelta(days=30)

    return ParsedIntent(
        metric="Total Revenue",
        time_range=TimeRange(
            start_date=start_date,
            end_date=end_date,
            granularity="day",
        ),
        filters={"Region": "North America"},
        baseline=BaselineConfig(type=BaselineType.PREVIOUS_PERIOD),
        feed_type=FeedType.ABSOLUTE,
        threshold=5.0,  # 5% threshold
    )


def main():
    """Run the example."""
    print("=" * 80)
    print("TQL Services Example")
    print("=" * 80)
    print()

    # Step 1: Create Business View
    print("Step 1: Creating Business View...")
    bv = create_sample_business_view()
    print(f"  Business View: {bv.name}")
    print(f"  Tables: {', '.join(t.name for t in bv.tables)}")
    print(f"  Measures: {', '.join(m.name for m in bv.measures)}")
    print(f"  Dimensions: {', '.join(d.name for d in bv.dimensions)}")
    print()

    # Step 2: Create Parsed Intent
    print("Step 2: Creating Parsed Intent...")
    intent = create_sample_intent()
    print(f"  Metric: {intent.metric}")
    print(f"  Time Range: {intent.time_range.start_date} to {intent.time_range.end_date}")
    print(f"  Filters: {intent.filters}")
    print(f"  Baseline: {intent.baseline.type.value}")
    print(f"  Feed Type: {intent.feed_type.value}")
    print()

    # Step 3: Build BV Context
    print("Step 3: Building Business View Context...")
    bv_context = BVContextBuilder.build(bv)
    print(f"  Allowed Columns: {len(bv_context.allowed_columns)} columns")
    print(f"  Join Graph: {len(bv_context.join_graph)} tables with joins")
    print(f"  Measures: {len(bv_context.measures_info)} measures")
    print(f"  Dimensions: {len(bv_context.dimensions_info)} dimensions")
    print()

    # Step 4: Generate TQL Plan
    print("Step 4: Generating TQL Plan...")
    try:
        plan = TQLPlanner.generate(intent, bv)
        print(f"  Plan generated successfully!")
        print(f"  Queries: {len(plan.get_all_queries())}")
        print(f"  Has baseline: {plan.requires_baseline()}")
        print(f"  Has timeseries: {plan.requires_timeseries()}")
        print(f"  Has dimensional breakdown: {plan.requires_dimensional_breakdown()}")
        print(f"  Complexity Score: {plan.metadata.complexity_score}/10")
        print()

        # Print queries
        print("  Generated Queries:")
        for query_name, query_sql in plan.get_all_queries():
            print(f"\n  [{query_name}]")
            # Print first 200 chars of query
            query_preview = query_sql.replace("\n", " ")[:200]
            print(f"    {query_preview}...")

        print()

    except Exception as e:
        print(f"  Error generating plan: {e}")
        return

    # Step 5: Validate Plan
    print("\nStep 5: Validating TQL Plan...")
    try:
        validated_plan = PlanValidator.validate(plan, bv_context)
        print("  Plan validated successfully!")
        print("  Security checks passed:")
        print("    - No dangerous keywords")
        print("    - No SQL injection patterns")
        print("    - Column references validated")
        print("    - Query structure validated")
        print()

    except Exception as e:
        print(f"  Validation failed: {e}")
        return

    # Step 6: Execute Plan (optional - requires database)
    print("Step 6: Executing TQL Plan...")
    print("  (Skipped - requires configured database)")
    print("  To execute:")
    print("    1. Set up SQLite database with sample data")
    print("    2. Create TQLAdapter instance")
    print("    3. Call adapter.execute(plan)")
    print()

    # Example of how to execute (commented out)
    """
    try:
        adapter = TQLAdapter("sqlite:///./example.db")
        if adapter.test_connection():
            results = adapter.execute(validated_plan)
            print(f"  Queries executed successfully!")
            print(f"  Current Value: {results.get_current_value()}")
            print(f"  Baseline Value: {results.get_baseline_value()}")

            if results.get_current_value() and results.get_baseline_value():
                change = results.get_current_value() - results.get_baseline_value()
                pct_change = (change / results.get_baseline_value()) * 100
                print(f"  Change: {change:,.2f} ({pct_change:+.1f}%)")
    except Exception as e:
        print(f"  Execution failed: {e}")
    """

    print("=" * 80)
    print("Example completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    # Set up minimal logging
    import logging
    logging.basicConfig(level=logging.INFO)

    main()
