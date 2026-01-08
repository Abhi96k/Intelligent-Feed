"""Generate mock data for the sample Business View."""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Tuple
import sqlite3


def generate_mock_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Generate mock data for all tables in the Business View.

    Returns:
        Tuple of (sales_fact, date_dim, product_dim, customer_dim, region_dim)
    """

    # Generate date dimension (2 years of data)
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2024, 12, 31)
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')

    date_dim = pd.DataFrame({
        'date_id': range(1, len(date_range) + 1),
        'date': date_range,
        'day_of_week': date_range.day_name(),
        'week': date_range.isocalendar().week,
        'month': date_range.month,
        'quarter': date_range.quarter,
        'year': date_range.year,
    })

    # Generate region dimension
    regions = [
        {'region_id': 1, 'region_name': 'North America', 'country': 'USA'},
        {'region_id': 2, 'region_name': 'North America', 'country': 'Canada'},
        {'region_id': 3, 'region_name': 'Europe', 'country': 'UK'},
        {'region_id': 4, 'region_name': 'Europe', 'country': 'Germany'},
        {'region_id': 5, 'region_name': 'APAC', 'country': 'India'},
        {'region_id': 6, 'region_name': 'APAC', 'country': 'Australia'},
        {'region_id': 7, 'region_name': 'Latin America', 'country': 'Brazil'},
    ]
    region_dim = pd.DataFrame(regions)

    # Generate product dimension
    products = []
    product_id = 1
    categories = {
        'Electronics': {
            'Laptops': ['Dell', 'HP', 'Lenovo', 'Apple'],
            'Phones': ['Apple', 'Samsung', 'Google'],
            'Tablets': ['Apple', 'Samsung', 'Amazon'],
        },
        'Furniture': {
            'Chairs': ['ErgoChair', 'ComfortSeat', 'OfficeMax'],
            'Desks': ['IKEA', 'StandDesk', 'WorkPro'],
        },
        'Office Supplies': {
            'Pens': ['Pilot', 'BIC', 'Sharpie'],
            'Paper': ['Copy Plus', 'HP', 'Georgia Pacific'],
        }
    }

    for category, subcategories in categories.items():
        for subcategory, brands in subcategories.items():
            for brand in brands:
                products.append({
                    'product_id': product_id,
                    'product_name': f'{brand} {subcategory}',
                    'category': category,
                    'sub_category': subcategory,
                    'brand': brand,
                })
                product_id += 1

    product_dim = pd.DataFrame(products)

    # Generate customer dimension
    segments = ['Enterprise', 'SMB', 'Consumer']
    customers = []
    for i in range(1, 201):  # 200 customers
        customers.append({
            'customer_id': i,
            'customer_name': f'Customer_{i}',
            'segment': np.random.choice(segments),
            'country': np.random.choice(region_dim['country'].tolist()),
        })
    customer_dim = pd.DataFrame(customers)

    # Generate sales fact table with realistic patterns
    np.random.seed(42)
    sales_records = []
    sale_id = 1

    for date_id in date_dim['date_id']:
        # Number of transactions per day varies
        num_transactions = np.random.poisson(20)

        current_date = date_dim[date_dim['date_id'] == date_id]['date'].iloc[0]

        # Introduce a significant drop in APAC region for last 8 weeks of 2024
        # and a spike in Enterprise segment in November 2024
        apac_multiplier = 1.0
        enterprise_multiplier = 1.0

        if current_date >= datetime(2024, 11, 1):
            # Last 8 weeks (Nov-Dec 2024): APAC drops by ~20%
            if current_date >= datetime(2024, 11, 1):
                apac_multiplier = 0.75

            # Enterprise spike in November
            if datetime(2024, 11, 1) <= current_date < datetime(2024, 12, 1):
                enterprise_multiplier = 1.4

        for _ in range(num_transactions):
            product_id = np.random.choice(product_dim['product_id'])
            customer_id = np.random.choice(customer_dim['customer_id'])
            region_id = np.random.choice(region_dim['region_id'])

            # Get customer segment
            segment = customer_dim[customer_dim['customer_id'] == customer_id]['segment'].iloc[0]

            # Base revenue varies by product category
            product = product_dim[product_dim['product_id'] == product_id].iloc[0]
            if product['category'] == 'Electronics':
                base_revenue = np.random.uniform(500, 2000)
            elif product['category'] == 'Furniture':
                base_revenue = np.random.uniform(200, 800)
            else:
                base_revenue = np.random.uniform(10, 100)

            # Apply multipliers
            if region_id in [5, 6]:  # APAC
                base_revenue *= apac_multiplier

            if segment == 'Enterprise':
                base_revenue *= enterprise_multiplier * 1.5  # Enterprise generally spends more

            quantity = np.random.randint(1, 5)
            revenue = base_revenue * quantity
            cost = revenue * np.random.uniform(0.6, 0.8)  # 20-40% profit margin

            sales_records.append({
                'sale_id': sale_id,
                'date_id': date_id,
                'product_id': product_id,
                'customer_id': customer_id,
                'region_id': region_id,
                'revenue': round(revenue, 2),
                'quantity': quantity,
                'cost': round(cost, 2),
            })
            sale_id += 1

    sales_fact = pd.DataFrame(sales_records)

    return sales_fact, date_dim, product_dim, customer_dim, region_dim


def create_sqlite_database(db_path: str = "tellius_feed.db"):
    """
    Create SQLite database and populate with mock data.

    Args:
        db_path: Path to SQLite database file
    """
    # Generate data
    sales_fact, date_dim, product_dim, customer_dim, region_dim = generate_mock_data()

    # Create database connection
    conn = sqlite3.connect(db_path)

    # Write data to SQLite
    sales_fact.to_sql('sales_fact', conn, if_exists='replace', index=False)
    date_dim.to_sql('date_dim', conn, if_exists='replace', index=False)
    product_dim.to_sql('product_dim', conn, if_exists='replace', index=False)
    customer_dim.to_sql('customer_dim', conn, if_exists='replace', index=False)
    region_dim.to_sql('region_dim', conn, if_exists='replace', index=False)

    # Create indexes for better query performance
    cursor = conn.cursor()

    # Indexes on foreign keys
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sales_date ON sales_fact(date_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sales_product ON sales_fact(product_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sales_customer ON sales_fact(customer_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sales_region ON sales_fact(region_id)")

    # Index on date column for time-series queries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_date_date ON date_dim(date)")

    conn.commit()
    conn.close()

    print(f"✓ Database created: {db_path}")
    print(f"  - Sales records: {len(sales_fact):,}")
    print(f"  - Date range: {date_dim['date'].min()} to {date_dim['date'].max()}")
    print(f"  - Products: {len(product_dim)}")
    print(f"  - Customers: {len(customer_dim)}")
    print(f"  - Regions: {len(region_dim)}")


if __name__ == "__main__":
    create_sqlite_database()
