"""Sample Business View for demo purposes."""

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
    WeekStart,
)


def create_sample_business_view() -> BusinessView:
    """
    Create a sample Business View for E-commerce Sales Analysis.

    Schema:
    - sales_fact: transaction-level sales data
    - date_dim: date dimension
    - product_dim: product information
    - customer_dim: customer information
    - region_dim: geographical regions
    """

    # Define tables
    sales_fact_table = Table(
        name="sales_fact",
        schema="public",
        columns=[
            Column(name="sale_id", type=ColumnType.INTEGER),
            Column(name="date_id", type=ColumnType.INTEGER),
            Column(name="product_id", type=ColumnType.INTEGER),
            Column(name="customer_id", type=ColumnType.INTEGER),
            Column(name="region_id", type=ColumnType.INTEGER),
            Column(name="revenue", type=ColumnType.FLOAT),
            Column(name="quantity", type=ColumnType.INTEGER),
            Column(name="cost", type=ColumnType.FLOAT),
        ],
        description="Transaction-level sales data"
    )

    date_dim_table = Table(
        name="date_dim",
        schema="public",
        columns=[
            Column(name="date_id", type=ColumnType.INTEGER),
            Column(name="date", type=ColumnType.DATE),
            Column(name="day_of_week", type=ColumnType.STRING),
            Column(name="week", type=ColumnType.INTEGER),
            Column(name="month", type=ColumnType.INTEGER),
            Column(name="quarter", type=ColumnType.INTEGER),
            Column(name="year", type=ColumnType.INTEGER),
        ],
        description="Date dimension"
    )

    product_dim_table = Table(
        name="product_dim",
        schema="public",
        columns=[
            Column(name="product_id", type=ColumnType.INTEGER),
            Column(name="product_name", type=ColumnType.STRING),
            Column(name="category", type=ColumnType.STRING),
            Column(name="sub_category", type=ColumnType.STRING),
            Column(name="brand", type=ColumnType.STRING),
        ],
        description="Product information"
    )

    customer_dim_table = Table(
        name="customer_dim",
        schema="public",
        columns=[
            Column(name="customer_id", type=ColumnType.INTEGER),
            Column(name="customer_name", type=ColumnType.STRING),
            Column(name="segment", type=ColumnType.STRING),
            Column(name="country", type=ColumnType.STRING),
        ],
        description="Customer information"
    )

    region_dim_table = Table(
        name="region_dim",
        schema="public",
        columns=[
            Column(name="region_id", type=ColumnType.INTEGER),
            Column(name="region_name", type=ColumnType.STRING),
            Column(name="country", type=ColumnType.STRING),
        ],
        description="Geographical regions"
    )

    # Define joins
    joins = [
        Join(
            left_table="sales_fact",
            right_table="date_dim",
            left_key="date_id",
            right_key="date_id",
            join_type=JoinType.INNER
        ),
        Join(
            left_table="sales_fact",
            right_table="product_dim",
            left_key="product_id",
            right_key="product_id",
            join_type=JoinType.INNER
        ),
        Join(
            left_table="sales_fact",
            right_table="customer_dim",
            left_key="customer_id",
            right_key="customer_id",
            join_type=JoinType.INNER
        ),
        Join(
            left_table="sales_fact",
            right_table="region_dim",
            left_key="region_id",
            right_key="region_id",
            join_type=JoinType.INNER
        ),
    ]

    # Define measures
    measures = [
        Measure(
            name="Revenue",
            expression="SUM(sales_fact.revenue)",
            format="currency",
            description="Total revenue"
        ),
        Measure(
            name="Quantity",
            expression="SUM(sales_fact.quantity)",
            format="number",
            description="Total quantity sold"
        ),
        Measure(
            name="Cost",
            expression="SUM(sales_fact.cost)",
            format="currency",
            description="Total cost"
        ),
        Measure(
            name="Profit",
            expression="SUM(sales_fact.revenue - sales_fact.cost)",
            format="currency",
            description="Total profit (Revenue - Cost)"
        ),
        Measure(
            name="Order_Count",
            expression="COUNT(DISTINCT sales_fact.sale_id)",
            format="number",
            description="Number of orders"
        ),
        Measure(
            name="Customer_Count",
            expression="COUNT(DISTINCT sales_fact.customer_id)",
            format="number",
            description="Number of unique customers"
        ),
    ]

    # Define dimensions
    dimensions = [
        Dimension(
            name="Region",
            column="region_name",
            table="region_dim",
            description="Sales region"
        ),
        Dimension(
            name="Country",
            column="country",
            table="region_dim",
            description="Country"
        ),
        Dimension(
            name="Product",
            column="product_name",
            table="product_dim",
            description="Product name"
        ),
        Dimension(
            name="Category",
            column="category",
            table="product_dim",
            description="Product category"
        ),
        Dimension(
            name="Sub_Category",
            column="sub_category",
            table="product_dim",
            description="Product sub-category"
        ),
        Dimension(
            name="Brand",
            column="brand",
            table="product_dim",
            description="Product brand"
        ),
        Dimension(
            name="Segment",
            column="segment",
            table="customer_dim",
            description="Customer segment"
        ),
        Dimension(
            name="Customer",
            column="customer_name",
            table="customer_dim",
            description="Customer name"
        ),
    ]

    # Define time dimension
    time_dimension = TimeDimension(
        column="date",
        table="date_dim",
        granularity=Granularity.DAY,
        description="Transaction date"
    )

    # Define calendar rules
    calendar_rules = CalendarRules(
        fiscal_year_start=1,  # January (calendar year)
        week_start=WeekStart.MONDAY
    )

    # Create Business View
    business_view = BusinessView(
        id="bv_ecommerce_sales",
        name="E-commerce Sales Analysis",
        tables=[
            sales_fact_table,
            date_dim_table,
            product_dim_table,
            customer_dim_table,
            region_dim_table,
        ],
        joins=joins,
        measures=measures,
        dimensions=dimensions,
        time_dimension=time_dimension,
        calendar_rules=calendar_rules,
        description="Business view for analyzing e-commerce sales data"
    )

    return business_view


# Global instance for use throughout the application
SAMPLE_BUSINESS_VIEW = create_sample_business_view()
