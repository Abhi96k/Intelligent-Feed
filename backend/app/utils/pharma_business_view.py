"""
Pharma Sales Analytics Business View Definition.

This module defines a Business View for pharmaceutical sales and prescription data.
"""

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


def create_pharma_business_view() -> BusinessView:
    """
    Create a Pharma Sales Analytics Business View.
    
    This BV includes:
    - Drug sales fact table
    - Drug dimension (products)
    - Therapeutic area dimension
    - Physician dimension (prescribers)
    - Region dimension
    - Date dimension
    """
    
    # Define tables
    drug_sales_fact = Table(
        name="drug_sales_fact",
        schema="public",
        columns=[
            Column(name="sale_id", type=ColumnType.INTEGER),
            Column(name="date_id", type=ColumnType.INTEGER),
            Column(name="drug_id", type=ColumnType.INTEGER),
            Column(name="physician_id", type=ColumnType.INTEGER),
            Column(name="therapeutic_area_id", type=ColumnType.INTEGER),
            Column(name="region_id", type=ColumnType.INTEGER),
            Column(name="units_sold", type=ColumnType.INTEGER),
            Column(name="revenue", type=ColumnType.FLOAT),
            Column(name="prescriptions", type=ColumnType.INTEGER),
            Column(name="rebates", type=ColumnType.FLOAT),
        ],
        description="Pharmaceutical sales transaction data"
    )
    
    drug_dim = Table(
        name="drug_dim",
        schema="public",
        columns=[
            Column(name="drug_id", type=ColumnType.INTEGER),
            Column(name="drug_name", type=ColumnType.STRING),
            Column(name="brand_name", type=ColumnType.STRING),
            Column(name="generic_name", type=ColumnType.STRING),
            Column(name="manufacturer", type=ColumnType.STRING),
            Column(name="drug_class", type=ColumnType.STRING),
            Column(name="formulation", type=ColumnType.STRING),
            Column(name="unit_price", type=ColumnType.FLOAT),
        ],
        description="Drug/Product information"
    )
    
    therapeutic_area_dim = Table(
        name="therapeutic_area_dim",
        schema="public",
        columns=[
            Column(name="therapeutic_area_id", type=ColumnType.INTEGER),
            Column(name="therapeutic_area", type=ColumnType.STRING),
            Column(name="sub_therapeutic_area", type=ColumnType.STRING),
            Column(name="indication", type=ColumnType.STRING),
        ],
        description="Therapeutic area classification"
    )
    
    physician_dim = Table(
        name="physician_dim",
        schema="public",
        columns=[
            Column(name="physician_id", type=ColumnType.INTEGER),
            Column(name="physician_name", type=ColumnType.STRING),
            Column(name="specialty", type=ColumnType.STRING),
            Column(name="hospital", type=ColumnType.STRING),
            Column(name="tier", type=ColumnType.STRING),
        ],
        description="Physician/Prescriber information"
    )
    
    pharma_region_dim = Table(
        name="pharma_region_dim",
        schema="public",
        columns=[
            Column(name="region_id", type=ColumnType.INTEGER),
            Column(name="region_name", type=ColumnType.STRING),
            Column(name="territory", type=ColumnType.STRING),
            Column(name="country", type=ColumnType.STRING),
        ],
        description="Sales regions and territories"
    )
    
    pharma_date_dim = Table(
        name="pharma_date_dim",
        schema="public",
        columns=[
            Column(name="date_id", type=ColumnType.INTEGER),
            Column(name="date", type=ColumnType.DATE),
            Column(name="week", type=ColumnType.INTEGER),
            Column(name="month", type=ColumnType.INTEGER),
            Column(name="quarter", type=ColumnType.INTEGER),
            Column(name="year", type=ColumnType.INTEGER),
        ],
        description="Date dimension for pharma"
    )
    
    # Define joins
    joins = [
        Join(
            left_table="drug_sales_fact",
            right_table="drug_dim",
            left_key="drug_id",
            right_key="drug_id",
            join_type=JoinType.INNER,
        ),
        Join(
            left_table="drug_sales_fact",
            right_table="therapeutic_area_dim",
            left_key="therapeutic_area_id",
            right_key="therapeutic_area_id",
            join_type=JoinType.INNER,
        ),
        Join(
            left_table="drug_sales_fact",
            right_table="physician_dim",
            left_key="physician_id",
            right_key="physician_id",
            join_type=JoinType.INNER,
        ),
        Join(
            left_table="drug_sales_fact",
            right_table="pharma_region_dim",
            left_key="region_id",
            right_key="region_id",
            join_type=JoinType.INNER,
        ),
        Join(
            left_table="drug_sales_fact",
            right_table="pharma_date_dim",
            left_key="date_id",
            right_key="date_id",
            join_type=JoinType.INNER,
        ),
    ]
    
    # Define measures
    measures = [
        Measure(
            name="Revenue",
            expression="SUM(drug_sales_fact.revenue)",
            format="currency",
            description="Total sales revenue"
        ),
        Measure(
            name="Units_Sold",
            expression="SUM(drug_sales_fact.units_sold)",
            format="number",
            description="Total units sold"
        ),
        Measure(
            name="Prescriptions",
            expression="SUM(drug_sales_fact.prescriptions)",
            format="number",
            description="Total prescriptions written"
        ),
        Measure(
            name="Rebates",
            expression="SUM(drug_sales_fact.rebates)",
            format="currency",
            description="Total rebates paid"
        ),
        Measure(
            name="Net_Revenue",
            expression="SUM(drug_sales_fact.revenue - drug_sales_fact.rebates)",
            format="currency",
            description="Net revenue after rebates"
        ),
        Measure(
            name="Avg_Price_Per_Unit",
            expression="SUM(drug_sales_fact.revenue) / SUM(drug_sales_fact.units_sold)",
            format="currency",
            description="Average price per unit"
        ),
        Measure(
            name="Physician_Count",
            expression="COUNT(DISTINCT drug_sales_fact.physician_id)",
            format="number",
            description="Number of prescribing physicians"
        ),
        Measure(
            name="Scripts_Per_Physician",
            expression="SUM(drug_sales_fact.prescriptions) / COUNT(DISTINCT drug_sales_fact.physician_id)",
            format="number",
            description="Average prescriptions per physician"
        ),
    ]
    
    # Define dimensions
    dimensions = [
        Dimension(
            name="Drug",
            column="drug_name",
            table="drug_dim",
            description="Drug/Product name"
        ),
        Dimension(
            name="Brand",
            column="brand_name",
            table="drug_dim",
            description="Brand name"
        ),
        Dimension(
            name="Generic",
            column="generic_name",
            table="drug_dim",
            description="Generic name"
        ),
        Dimension(
            name="Manufacturer",
            column="manufacturer",
            table="drug_dim",
            description="Drug manufacturer"
        ),
        Dimension(
            name="Drug_Class",
            column="drug_class",
            table="drug_dim",
            description="Drug classification"
        ),
        Dimension(
            name="Therapeutic_Area",
            column="therapeutic_area",
            table="therapeutic_area_dim",
            description="Therapeutic area"
        ),
        Dimension(
            name="Sub_Therapeutic_Area",
            column="sub_therapeutic_area",
            table="therapeutic_area_dim",
            description="Sub-therapeutic area"
        ),
        Dimension(
            name="Specialty",
            column="specialty",
            table="physician_dim",
            description="Physician specialty"
        ),
        Dimension(
            name="Tier",
            column="tier",
            table="physician_dim",
            description="Physician tier"
        ),
        Dimension(
            name="Region",
            column="region_name",
            table="pharma_region_dim",
            description="Sales region"
        ),
        Dimension(
            name="Territory",
            column="territory",
            table="pharma_region_dim",
            description="Sales territory"
        ),
    ]
    
    # Time dimension
    time_dimension = TimeDimension(
        column="date",
        table="pharma_date_dim",
        granularity=Granularity.DAY,
        description="Date for time-based analysis",
    )
    
    # Calendar rules
    calendar_rules = CalendarRules()
    
    # Create Business View
    business_view = BusinessView(
        id="bv_pharma_sales",
        name="Pharma Sales Analytics",
        tables=[
            drug_sales_fact,
            drug_dim,
            therapeutic_area_dim,
            physician_dim,
            pharma_region_dim,
            pharma_date_dim,
        ],
        joins=joins,
        measures=measures,
        dimensions=dimensions,
        time_dimension=time_dimension,
        calendar_rules=calendar_rules,
        description="Pharmaceutical sales and prescription analytics"
    )
    
    return business_view


# Create the business view instance
PHARMA_BUSINESS_VIEW = create_pharma_business_view()
