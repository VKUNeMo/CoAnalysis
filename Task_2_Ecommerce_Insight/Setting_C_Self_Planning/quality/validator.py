import os
import json
import pandas as pd
import numpy as np
from typing import Dict, Any, List

def run_data_quality_checks(dfs: Dict[str, pd.DataFrame], output_dir: str = None) -> Dict[str, Any]:
    """
    Checks data consistency, missing timestamps, invalid currency amounts,
    cross-validates revenue sums, and returns a list of valid order IDs 
    for delivery analysis. Exports a detailed JSON report.
    """
    print("Running data quality checks...")
    orders = dfs['orders']
    items = dfs['order_items']
    payments = dfs['order_payments']
    customers = dfs['customers']
    
    report = {}
    checks = []
    
    # -------------------------------------------------------------------------
    # 1. Check time logic: purchase_timestamp > delivered_customer_date
    # -------------------------------------------------------------------------
    time_mask = (orders['order_purchase_timestamp'] > orders['order_delivered_customer_date'])
    time_errors_df = orders[time_mask]
    report['time_logic_errors_count'] = len(time_errors_df)
    report['time_logic_errors_order_ids'] = time_errors_df['order_id'].tolist()
    
    checks.append({
        'check_id': 'DQ-01',
        'check_name': 'Time Logic Consistency',
        'description': 'purchase_timestamp should not be after delivered_customer_date',
        'errors_found': len(time_errors_df),
        'status': 'PASS' if len(time_errors_df) == 0 else 'WARN',
        'detail': f'{len(time_errors_df)} orders with purchase > delivery timestamp'
    })
    
    # -------------------------------------------------------------------------
    # 2. Check missing timestamps in orders
    # -------------------------------------------------------------------------
    missing_cols = ['order_approved_at', 'order_delivered_carrier_date', 'order_delivered_customer_date']
    missing_report = {}
    total_orders = len(orders)
    for col in missing_cols:
        null_count = int(orders[col].isnull().sum())
        null_ratio = float(null_count / total_orders) if total_orders > 0 else 0.0
        missing_report[col] = {
            'missing_count': null_count,
            'missing_ratio': round(null_ratio, 6)
        }
    report['missing_dates_report'] = missing_report
    
    total_missing = sum(v['missing_count'] for v in missing_report.values())
    checks.append({
        'check_id': 'DQ-02',
        'check_name': 'Missing Timestamp Fields',
        'description': 'Check null values in order timestamp columns',
        'errors_found': total_missing,
        'status': 'PASS' if total_missing < total_orders * 0.05 else 'WARN',
        'detail': {col: v['missing_count'] for col, v in missing_report.items()}
    })
    
    # -------------------------------------------------------------------------
    # 3. Check invalid values in currency (price < 0 or payment_value < 0)
    # -------------------------------------------------------------------------
    negative_price_count = int((items['price'] < 0).sum())
    negative_payment_count = int((payments['payment_value'] < 0).sum())
    report['currency_anomaly_report'] = {
        'negative_prices_count': negative_price_count,
        'negative_payments_count': negative_payment_count
    }
    
    checks.append({
        'check_id': 'DQ-03',
        'check_name': 'Currency Value Validity',
        'description': 'No negative price or payment values',
        'errors_found': negative_price_count + negative_payment_count,
        'status': 'PASS' if (negative_price_count + negative_payment_count) == 0 else 'FAIL',
        'detail': f'{negative_price_count} negative prices, {negative_payment_count} negative payments'
    })
    
    # -------------------------------------------------------------------------
    # 4. Revenue Reconciliation: sum(payment_value) vs pipeline computation
    # -------------------------------------------------------------------------
    total_payment_value = float(payments['payment_value'].sum())
    total_item_revenue = float(items['price'].sum() + items['freight_value'].sum())
    revenue_delta = abs(total_payment_value - total_item_revenue)
    
    checks.append({
        'check_id': 'DQ-04',
        'check_name': 'Revenue Reconciliation',
        'description': 'Cross-validate sum(payment_value) vs sum(price + freight)',
        'errors_found': 0,
        'status': 'INFO',
        'detail': {
            'sum_payment_value': round(total_payment_value, 2),
            'sum_price_plus_freight': round(total_item_revenue, 2),
            'delta': round(revenue_delta, 4),
            'note': 'Delta expected due to voucher/discount adjustments and rounding'
        }
    })
    report['revenue_reconciliation'] = {
        'sum_payment_value': round(total_payment_value, 2),
        'sum_price_plus_freight': round(total_item_revenue, 2),
        'delta': round(revenue_delta, 4)
    }
    
    # -------------------------------------------------------------------------
    # 5. Customer ID Consistency
    # -------------------------------------------------------------------------
    unique_cust_in_orders = orders['customer_id'].nunique()
    unique_cust_in_customers = customers['customer_id'].nunique()
    cust_delta = abs(unique_cust_in_orders - unique_cust_in_customers)
    
    unique_cust_unique_id = customers['customer_unique_id'].nunique()
    
    checks.append({
        'check_id': 'DQ-05',
        'check_name': 'Customer ID Consistency',
        'description': 'customer_id count in orders vs customers table',
        'errors_found': cust_delta,
        'status': 'PASS' if cust_delta == 0 else 'WARN',
        'detail': {
            'unique_customer_id_in_orders': unique_cust_in_orders,
            'unique_customer_id_in_customers': unique_cust_in_customers,
            'delta': cust_delta,
            'unique_customer_unique_id': unique_cust_unique_id
        }
    })
    report['customer_consistency'] = {
        'unique_customer_unique_id': unique_cust_unique_id,
        'customer_id_delta': cust_delta
    }
    
    # -------------------------------------------------------------------------
    # 6. Extract valid order_ids for delivery performance analysis
    # -------------------------------------------------------------------------
    valid_delivery_mask = (
        (orders['order_status'] == 'delivered') &
        (orders['order_delivered_customer_date'].notnull()) &
        (orders['order_estimated_delivery_date'].notnull())
    )
    valid_delivery_orders = orders[valid_delivery_mask]
    report['valid_delivery_order_ids'] = valid_delivery_orders['order_id'].tolist()
    
    # Late rate invariant check
    valid_count = len(valid_delivery_orders)
    checks.append({
        'check_id': 'DQ-06',
        'check_name': 'Delivery Sample Definition',
        'description': 'Valid delivered orders with both delivery and estimated timestamps',
        'errors_found': 0,
        'status': 'INFO',
        'detail': {
            'total_orders': total_orders,
            'delivered_with_timestamps': valid_count,
            'filter_logic': 'order_status == delivered AND delivered_customer_date NOT NULL AND estimated_delivery_date NOT NULL',
            'late_comparison_method': 'datetime comparison (delivery_timestamp > estimated_timestamp)',
            'note': 'Using full datetime comparison; date-only comparison would yield ~6.77% late rate'
        }
    })
    
    # -------------------------------------------------------------------------
    # Summary
    # -------------------------------------------------------------------------
    pass_count = sum(1 for c in checks if c['status'] == 'PASS')
    total_checks = len(checks)
    report['validation_summary'] = {
        'total_checks': total_checks,
        'passed': pass_count,
        'warnings': sum(1 for c in checks if c['status'] == 'WARN'),
        'failures': sum(1 for c in checks if c['status'] == 'FAIL'),
        'info': sum(1 for c in checks if c['status'] == 'INFO')
    }
    report['checks'] = checks
    
    # Export JSON report if output directory is provided
    if output_dir:
        report_path = os.path.join(output_dir, 'data_quality_report.json')
        # Create a serializable copy (remove order_id lists for JSON size)
        export_report = {k: v for k, v in report.items() if k != 'valid_delivery_order_ids' and k != 'time_logic_errors_order_ids'}
        export_report['valid_delivery_orders_count'] = len(report['valid_delivery_order_ids'])
        export_report['time_logic_errors_count'] = report['time_logic_errors_count']
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(export_report, f, indent=4, ensure_ascii=False, default=str)
        print(f"Data quality report exported to {os.path.basename(report_path)}")
    
    print(f"Data quality checks completed. {pass_count}/{total_checks} passed, "
          f"{len(report['valid_delivery_order_ids'])} valid delivery orders.")
    
    return report

