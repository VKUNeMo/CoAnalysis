import pytest
import pandas as pd
import numpy as np

@pytest.fixture
def sample_orders_df():
    # 3 customers, 5 orders
    data = {
        'order_id': ['o1', 'o2', 'o3', 'o4', 'o5'],
        'customer_id': ['c1_1', 'c1_2', 'c2_1', 'c3_1', 'c3_2'],
        'order_status': ['delivered', 'delivered', 'delivered', 'delivered', 'canceled'],
        'order_purchase_timestamp': pd.to_datetime([
            '2018-01-01 10:00:00',
            '2018-01-15 12:00:00',
            '2018-01-20 14:00:00',
            '2018-02-10 16:00:00',
            '2018-02-25 18:00:00'
        ])
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_customers_df():
    data = {
        'customer_id': ['c1_1', 'c1_2', 'c2_1', 'c3_1', 'c3_2'],
        'customer_unique_id': ['cust1', 'cust1', 'cust2', 'cust3', 'cust3'],
        'customer_zip_code_prefix': [1000, 1000, 2000, 3000, 3000],
        'customer_city': ['city_a', 'city_a', 'city_b', 'city_c', 'city_c'],
        'customer_state': ['SA', 'SA', 'SB', 'SC', 'SC']
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_payments_df():
    data = {
        'order_id': ['o1', 'o2', 'o3', 'o4', 'o5'],
        'payment_sequential': [1, 1, 1, 1, 1],
        'payment_type': ['credit_card', 'boleto', 'credit_card', 'voucher', 'credit_card'],
        'payment_installments': [1, 2, 1, 1, 1],
        'payment_value': [100.0, 50.0, 200.0, 30.0, 150.0]
    }
    return pd.DataFrame(data)
