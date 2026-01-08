"""Generate mock data for the Pharma Business View."""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Tuple
import sqlite3


def generate_pharma_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Generate mock pharmaceutical sales data.
    
    Returns:
        Tuple of (drug_sales_fact, drug_dim, therapeutic_area_dim, physician_dim, pharma_region_dim, pharma_date_dim)
    """
    np.random.seed(42)
    
    # Generate date dimension (2 years of data)
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2024, 12, 31)
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    
    pharma_date_dim = pd.DataFrame({
        'date_id': range(1, len(date_range) + 1),
        'date': date_range,
        'week': date_range.isocalendar().week,
        'month': date_range.month,
        'quarter': date_range.quarter,
        'year': date_range.year,
    })
    
    # Generate region dimension
    regions = [
        {'region_id': 1, 'region_name': 'Northeast', 'territory': 'NY Metro', 'country': 'USA'},
        {'region_id': 2, 'region_name': 'Northeast', 'territory': 'New England', 'country': 'USA'},
        {'region_id': 3, 'region_name': 'Southeast', 'territory': 'Florida', 'country': 'USA'},
        {'region_id': 4, 'region_name': 'Southeast', 'territory': 'Georgia', 'country': 'USA'},
        {'region_id': 5, 'region_name': 'Midwest', 'territory': 'Chicago', 'country': 'USA'},
        {'region_id': 6, 'region_name': 'Midwest', 'territory': 'Detroit', 'country': 'USA'},
        {'region_id': 7, 'region_name': 'West', 'territory': 'California', 'country': 'USA'},
        {'region_id': 8, 'region_name': 'West', 'territory': 'Pacific Northwest', 'country': 'USA'},
    ]
    pharma_region_dim = pd.DataFrame(regions)
    
    # Generate therapeutic area dimension
    therapeutic_areas = [
        {'therapeutic_area_id': 1, 'therapeutic_area': 'Oncology', 'sub_therapeutic_area': 'Breast Cancer', 'indication': 'HER2+ Breast Cancer'},
        {'therapeutic_area_id': 2, 'therapeutic_area': 'Oncology', 'sub_therapeutic_area': 'Lung Cancer', 'indication': 'NSCLC'},
        {'therapeutic_area_id': 3, 'therapeutic_area': 'Oncology', 'sub_therapeutic_area': 'Prostate Cancer', 'indication': 'mCRPC'},
        {'therapeutic_area_id': 4, 'therapeutic_area': 'Cardiovascular', 'sub_therapeutic_area': 'Heart Failure', 'indication': 'HFrEF'},
        {'therapeutic_area_id': 5, 'therapeutic_area': 'Cardiovascular', 'sub_therapeutic_area': 'Hypertension', 'indication': 'Essential HTN'},
        {'therapeutic_area_id': 6, 'therapeutic_area': 'Immunology', 'sub_therapeutic_area': 'Rheumatoid Arthritis', 'indication': 'Moderate-Severe RA'},
        {'therapeutic_area_id': 7, 'therapeutic_area': 'Immunology', 'sub_therapeutic_area': 'Psoriasis', 'indication': 'Plaque Psoriasis'},
        {'therapeutic_area_id': 8, 'therapeutic_area': 'Neurology', 'sub_therapeutic_area': 'Multiple Sclerosis', 'indication': 'RRMS'},
        {'therapeutic_area_id': 9, 'therapeutic_area': 'Neurology', 'sub_therapeutic_area': 'Migraine', 'indication': 'Chronic Migraine'},
        {'therapeutic_area_id': 10, 'therapeutic_area': 'Diabetes', 'sub_therapeutic_area': 'Type 2 Diabetes', 'indication': 'T2DM'},
    ]
    therapeutic_area_dim = pd.DataFrame(therapeutic_areas)
    
    # Generate drug dimension
    drugs = [
        # Oncology drugs
        {'drug_id': 1, 'drug_name': 'Herceptin', 'brand_name': 'Herceptin', 'generic_name': 'Trastuzumab', 'manufacturer': 'Roche', 'drug_class': 'Monoclonal Antibody', 'formulation': 'IV Infusion', 'unit_price': 4500},
        {'drug_id': 2, 'drug_name': 'Keytruda', 'brand_name': 'Keytruda', 'generic_name': 'Pembrolizumab', 'manufacturer': 'Merck', 'drug_class': 'PD-1 Inhibitor', 'formulation': 'IV Infusion', 'unit_price': 9800},
        {'drug_id': 3, 'drug_name': 'Xtandi', 'brand_name': 'Xtandi', 'generic_name': 'Enzalutamide', 'manufacturer': 'Pfizer', 'drug_class': 'Androgen Receptor Inhibitor', 'formulation': 'Oral Capsule', 'unit_price': 12500},
        # Cardiovascular drugs
        {'drug_id': 4, 'drug_name': 'Entresto', 'brand_name': 'Entresto', 'generic_name': 'Sacubitril/Valsartan', 'manufacturer': 'Novartis', 'drug_class': 'ARNI', 'formulation': 'Oral Tablet', 'unit_price': 580},
        {'drug_id': 5, 'drug_name': 'Eliquis', 'brand_name': 'Eliquis', 'generic_name': 'Apixaban', 'manufacturer': 'Bristol-Myers Squibb', 'drug_class': 'Factor Xa Inhibitor', 'formulation': 'Oral Tablet', 'unit_price': 520},
        # Immunology drugs
        {'drug_id': 6, 'drug_name': 'Humira', 'brand_name': 'Humira', 'generic_name': 'Adalimumab', 'manufacturer': 'AbbVie', 'drug_class': 'TNF Inhibitor', 'formulation': 'Subcutaneous', 'unit_price': 2800},
        {'drug_id': 7, 'drug_name': 'Stelara', 'brand_name': 'Stelara', 'generic_name': 'Ustekinumab', 'manufacturer': 'Johnson & Johnson', 'drug_class': 'IL-12/23 Inhibitor', 'formulation': 'Subcutaneous', 'unit_price': 13500},
        # Neurology drugs
        {'drug_id': 8, 'drug_name': 'Ocrevus', 'brand_name': 'Ocrevus', 'generic_name': 'Ocrelizumab', 'manufacturer': 'Roche', 'drug_class': 'B-Cell Depleting', 'formulation': 'IV Infusion', 'unit_price': 32000},
        {'drug_id': 9, 'drug_name': 'Aimovig', 'brand_name': 'Aimovig', 'generic_name': 'Erenumab', 'manufacturer': 'Amgen', 'drug_class': 'CGRP Inhibitor', 'formulation': 'Subcutaneous', 'unit_price': 690},
        # Diabetes drugs
        {'drug_id': 10, 'drug_name': 'Ozempic', 'brand_name': 'Ozempic', 'generic_name': 'Semaglutide', 'manufacturer': 'Novo Nordisk', 'drug_class': 'GLP-1 Agonist', 'formulation': 'Subcutaneous', 'unit_price': 950},
        {'drug_id': 11, 'drug_name': 'Jardiance', 'brand_name': 'Jardiance', 'generic_name': 'Empagliflozin', 'manufacturer': 'Boehringer Ingelheim', 'drug_class': 'SGLT2 Inhibitor', 'formulation': 'Oral Tablet', 'unit_price': 580},
        {'drug_id': 12, 'drug_name': 'Trulicity', 'brand_name': 'Trulicity', 'generic_name': 'Dulaglutide', 'manufacturer': 'Eli Lilly', 'drug_class': 'GLP-1 Agonist', 'formulation': 'Subcutaneous', 'unit_price': 890},
    ]
    drug_dim = pd.DataFrame(drugs)
    
    # Drug to therapeutic area mapping
    drug_ta_map = {
        1: 1, 2: 2, 3: 3,  # Oncology
        4: 4, 5: 5,        # Cardiovascular
        6: 6, 7: 7,        # Immunology
        8: 8, 9: 9,        # Neurology
        10: 10, 11: 10, 12: 10,  # Diabetes
    }
    
    # Generate physician dimension
    specialties = ['Oncology', 'Cardiology', 'Rheumatology', 'Dermatology', 'Neurology', 'Endocrinology', 'Primary Care']
    hospitals = ['Mayo Clinic', 'Cleveland Clinic', 'Johns Hopkins', 'Mass General', 'UCSF Medical', 'MD Anderson', 'Memorial Sloan', 'Stanford Health', 'Duke University', 'UCLA Medical']
    tiers = ['Tier 1', 'Tier 2', 'Tier 3']
    
    physicians = []
    for i in range(1, 151):  # 150 physicians
        physicians.append({
            'physician_id': i,
            'physician_name': f'Dr. {np.random.choice(["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Chen", "Patel", "Kim", "Lee", "Wang"])} {chr(65 + i % 26)}.',
            'specialty': np.random.choice(specialties),
            'hospital': np.random.choice(hospitals),
            'tier': np.random.choice(tiers, p=[0.2, 0.5, 0.3]),  # 20% Tier 1, 50% Tier 2, 30% Tier 3
        })
    physician_dim = pd.DataFrame(physicians)
    
    # Generate sales fact table
    sales_records = []
    sale_id = 1
    
    for date_id in pharma_date_dim['date_id']:
        current_date = pharma_date_dim[pharma_date_dim['date_id'] == date_id]['date'].iloc[0]
        
        # Seasonal and trend multipliers
        month = current_date.month
        year = current_date.year
        
        # Q4 2024 sees decline in Oncology drugs
        oncology_multiplier = 1.0
        if year == 2024 and month >= 10:
            oncology_multiplier = 0.7  # 30% drop
        
        # Ozempic sees spike in Q3 2024
        ozempic_multiplier = 1.0
        if year == 2024 and month >= 7 and month <= 9:
            ozempic_multiplier = 1.8  # 80% spike
        
        # Generate 10-30 transactions per day
        num_transactions = np.random.randint(10, 30)
        
        for _ in range(num_transactions):
            drug_id = np.random.choice(drug_dim['drug_id'])
            drug_info = drug_dim[drug_dim['drug_id'] == drug_id].iloc[0]
            therapeutic_area_id = drug_ta_map[drug_id]
            physician_id = np.random.choice(physician_dim['physician_id'])
            region_id = np.random.choice(pharma_region_dim['region_id'])
            
            # Base units
            units_sold = np.random.randint(1, 10)
            
            # Apply multipliers
            if drug_id in [1, 2, 3]:  # Oncology drugs
                units_sold = int(units_sold * oncology_multiplier)
            
            if drug_id == 10:  # Ozempic
                units_sold = int(units_sold * ozempic_multiplier)
            
            if units_sold < 1:
                units_sold = 1
                
            revenue = units_sold * drug_info['unit_price'] * np.random.uniform(0.85, 1.15)
            prescriptions = np.random.randint(1, units_sold + 1)
            rebates = revenue * np.random.uniform(0.15, 0.35)  # 15-35% rebates
            
            sales_records.append({
                'sale_id': sale_id,
                'date_id': date_id,
                'drug_id': drug_id,
                'physician_id': physician_id,
                'therapeutic_area_id': therapeutic_area_id,
                'region_id': region_id,
                'units_sold': units_sold,
                'revenue': round(revenue, 2),
                'prescriptions': prescriptions,
                'rebates': round(rebates, 2),
            })
            sale_id += 1
    
    drug_sales_fact = pd.DataFrame(sales_records)
    
    return drug_sales_fact, drug_dim, therapeutic_area_dim, physician_dim, pharma_region_dim, pharma_date_dim


def add_pharma_tables_to_database(db_path: str = "tellius_feed.db"):
    """
    Add Pharma tables to the existing SQLite database.
    
    Args:
        db_path: Path to SQLite database file
    """
    # Generate data
    drug_sales_fact, drug_dim, therapeutic_area_dim, physician_dim, pharma_region_dim, pharma_date_dim = generate_pharma_data()
    
    # Create database connection
    conn = sqlite3.connect(db_path)
    
    # Write data to SQLite
    drug_sales_fact.to_sql('drug_sales_fact', conn, if_exists='replace', index=False)
    drug_dim.to_sql('drug_dim', conn, if_exists='replace', index=False)
    therapeutic_area_dim.to_sql('therapeutic_area_dim', conn, if_exists='replace', index=False)
    physician_dim.to_sql('physician_dim', conn, if_exists='replace', index=False)
    pharma_region_dim.to_sql('pharma_region_dim', conn, if_exists='replace', index=False)
    pharma_date_dim.to_sql('pharma_date_dim', conn, if_exists='replace', index=False)
    
    # Create indexes
    cursor = conn.cursor()
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pharma_sales_date ON drug_sales_fact(date_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pharma_sales_drug ON drug_sales_fact(drug_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pharma_sales_physician ON drug_sales_fact(physician_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pharma_sales_ta ON drug_sales_fact(therapeutic_area_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pharma_sales_region ON drug_sales_fact(region_id)")
    
    conn.commit()
    conn.close()
    
    print(f"✓ Pharma tables added to: {db_path}")
    print(f"  - Drug sales records: {len(drug_sales_fact):,}")
    print(f"  - Date range: {pharma_date_dim['date'].min()} to {pharma_date_dim['date'].max()}")
    print(f"  - Drugs: {len(drug_dim)}")
    print(f"  - Physicians: {len(physician_dim)}")
    print(f"  - Therapeutic areas: {len(therapeutic_area_dim)}")
    print(f"  - Regions: {len(pharma_region_dim)}")


if __name__ == "__main__":
    add_pharma_tables_to_database()

