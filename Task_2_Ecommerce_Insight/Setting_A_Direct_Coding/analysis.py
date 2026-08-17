import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Set style for premium visualizations
sns.set_theme(style="whitegrid")
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['figure.figsize'] = (12, 7)
plt.rcParams['axes.titlesize'] = 16
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['xtick.labelsize'] = 10
plt.rcParams['ytick.labelsize'] = 10

# Create plots folder
os.makedirs('plots', exist_ok=True)

# Define paths
DATA_DIR = "../../Dataset/Olist Brazilian E-Commerce/"

def load_data():
    print("Loading datasets...")
    customers = pd.read_csv(os.path.join(DATA_DIR, "olist_customers_dataset.csv"))
    orders = pd.read_csv(os.path.join(DATA_DIR, "olist_orders_dataset.csv"))
    order_items = pd.read_csv(os.path.join(DATA_DIR, "olist_order_items_dataset.csv"))
    order_payments = pd.read_csv(os.path.join(DATA_DIR, "olist_order_payments_dataset.csv"))
    order_reviews = pd.read_csv(os.path.join(DATA_DIR, "olist_order_reviews_dataset.csv"))
    products = pd.read_csv(os.path.join(DATA_DIR, "olist_products_dataset.csv"))
    category_translation = pd.read_csv(os.path.join(DATA_DIR, "product_category_name_translation.csv"))
    print("Datasets loaded successfully.")
    return customers, orders, order_items, order_payments, order_reviews, products, category_translation

def preprocess_data(customers, orders, order_items, order_payments, order_reviews, products, category_translation):
    print("Preprocessing data...")
    # Convert date columns to datetime
    date_cols = ['order_purchase_timestamp', 'order_approved_at', 
                 'order_delivered_carrier_date', 'order_delivered_customer_date', 
                 'order_estimated_delivery_date']
    for col in date_cols:
        orders[col] = pd.to_datetime(orders[col])
        
    order_reviews['review_creation_date'] = pd.to_datetime(order_reviews['review_creation_date'])
    order_reviews['review_answer_timestamp'] = pd.to_datetime(order_reviews['review_answer_timestamp'])
    
    order_items['shipping_limit_date'] = pd.to_datetime(order_items['shipping_limit_date'])
    
    # Translate product categories
    products = products.merge(category_translation, on='product_category_name', how='left')
    # Fill missing translations
    products['product_category_name_english'] = products['product_category_name_english'].fillna(products['product_category_name'])
    products['product_category_name_english'] = products['product_category_name_english'].fillna('other')
    products['product_category_name_english'] = products['product_category_name_english'].str.replace('_', ' ').str.title()
    
    print("Preprocessing completed.")
    return customers, orders, order_items, order_payments, order_reviews, products

def analyze_retention(customers, orders):
    print("Performing Customer Retention Analysis...")
    # Merge orders with customers to get unique customer IDs
    df = orders.merge(customers, on='customer_id', how='inner')
    
    # Exclude canceled and unavailable orders
    valid_orders = df[~df['order_status'].isin(['canceled', 'unavailable'])].copy()
    
    # Purchase month
    valid_orders['purchase_month'] = valid_orders['order_purchase_timestamp'].dt.to_period('M')
    
    # Customer's cohort month (first purchase month)
    valid_orders['cohort_month'] = valid_orders.groupby('customer_unique_id')['purchase_month'].transform('min')
    
    # Cohort index (difference in months)
    valid_orders['cohort_index'] = (valid_orders['purchase_month'] - valid_orders['cohort_month']).apply(lambda x: x.n)
    
    # Repeat purchase statistics
    customer_order_counts = valid_orders.groupby('customer_unique_id')['order_id'].nunique()
    repeat_customers_count = (customer_order_counts > 1).sum()
    total_customers_count = customer_order_counts.count()
    repeat_rate = repeat_customers_count / total_customers_count
    
    # Group by cohort month and cohort index
    cohort_group = valid_orders.groupby(['cohort_month', 'cohort_index'])['customer_unique_id'].nunique().reset_index()
    
    # Pivot to cohort matrix
    cohort_matrix = cohort_group.pivot(index='cohort_month', columns='cohort_index', values='customer_unique_id')
    
    # Cohort size (number of customers in first month)
    cohort_sizes = cohort_matrix.iloc[:, 0]
    
    # Divide by cohort size to get retention rate
    retention_matrix = cohort_matrix.divide(cohort_sizes, axis=0)
    
    # Let's filter to cohorts from Jan 2017 to Dec 2017 where we have at least 6-12 months of follow-up
    cohorts_2017 = retention_matrix.loc['2017-01':'2017-12']
    
    plt.figure(figsize=(14, 10))
    sns.heatmap(
        cohorts_2017.iloc[:, 0:13], # Show first year of activity
        annot=True,
        fmt=".2%",
        cmap="YlGnBu",
        cbar_kws={'label': 'Retention Rate'},
        linewidths=0.5
    )
    plt.title("Customer Retention Cohorts - 2017 (First 12 Months)", fontsize=16, fontweight='bold', pad=20)
    plt.ylabel("Cohort Month (First Purchase)", fontsize=12)
    plt.xlabel("Months After First Purchase", fontsize=12)
    plt.tight_layout()
    plt.savefig('plots/cohort_retention_2017.png', dpi=150)
    plt.close()
    
    # Also save the full retention matrix to CSV
    retention_matrix_csv = retention_matrix.copy()
    retention_matrix_csv.index = retention_matrix_csv.index.astype(str)
    retention_matrix_csv.to_csv('cohort_retention_matrix.csv')
    
    print(f"Repeat purchase rate: {repeat_rate:.2%}")
    return {
        'repeat_purchase_rate': float(repeat_rate),
        'total_unique_customers': int(total_customers_count),
        'repeat_customers': int(repeat_customers_count)
    }

def analyze_delivery_delays(orders, customers, order_reviews, order_items, products):
    print("Performing Delivery Delay Analysis...")
    # Use delivered orders
    delivered = orders[orders['order_status'] == 'delivered'].copy()
    
    # Clean null delivered dates
    delivered = delivered.dropna(subset=['order_delivered_customer_date'])
    
    # Calculate delivery metrics in days
    delivered['actual_delivery_days'] = (delivered['order_delivered_customer_date'] - delivered['order_purchase_timestamp']).dt.total_seconds() / (24 * 3600)
    delivered['estimated_delivery_days'] = (delivered['order_estimated_delivery_date'] - delivered['order_purchase_timestamp']).dt.total_seconds() / (24 * 3600)
    delivered['delay_days'] = (delivered['order_delivered_customer_date'] - delivered['order_estimated_delivery_date']).dt.total_seconds() / (24 * 3600)
    
    delivered['is_delayed'] = (delivered['delay_days'] > 0).astype(int)
    
    mean_actual_delivery = delivered['actual_delivery_days'].mean()
    mean_estimated_delivery = delivered['estimated_delivery_days'].mean()
    overall_delay_rate = delivered['is_delayed'].mean()
    mean_delay_for_delayed = delivered[delivered['delay_days'] > 0]['delay_days'].mean()
    
    # Delay by customer state
    delivered_state = delivered.merge(customers, on='customer_id', how='inner')
    state_stats = delivered_state.groupby('customer_state').agg(
        order_count=('order_id', 'count'),
        avg_actual_delivery=('actual_delivery_days', 'mean'),
        avg_estimated_delivery=('estimated_delivery_days', 'mean'),
        delay_rate=('is_delayed', 'mean'),
        avg_delay_days=('delay_days', 'mean')
    ).reset_index()
    
    # Filter states with significant order count (e.g. > 100 orders)
    state_stats = state_stats[state_stats['order_count'] > 100].sort_values(by='delay_rate', ascending=False)
    
    # Plot delay rate by state
    plt.figure(figsize=(14, 8))
    sns.barplot(
        x='delay_rate',
        y='customer_state',
        data=state_stats,
        palette='Reds_r',
        hue='customer_state',
        legend=False
    )
    plt.axvline(x=overall_delay_rate, color='blue', linestyle='--', label=f'National Average ({overall_delay_rate:.1%})')
    plt.title("Delivery Delay Rate by Customer State", fontsize=16, fontweight='bold', pad=20)
    plt.xlabel("Delay Rate (Percentage of Orders Delivered Late)", fontsize=12)
    plt.ylabel("Customer State", fontsize=12)
    plt.gca().xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.0%}'))
    plt.legend()
    plt.tight_layout()
    plt.savefig('plots/delay_rate_by_state.png', dpi=150)
    plt.close()
    
    # Delay and Review Score
    # Keep the latest review per order to avoid duplicates
    reviews_clean = order_reviews.sort_values(by='review_answer_timestamp').drop_duplicates(subset=['order_id'], keep='last')
    
    delivered_reviews = delivered.merge(reviews_clean, on='order_id', how='inner')
    
    correlation = delivered_reviews['delay_days'].corr(delivered_reviews['review_score'])
    
    # Categorize delay
    def categorize_delay(row):
        if row['delay_days'] <= 0:
            return 'On Time or Early'
        elif row['delay_days'] <= 7:
            return '1-7 Days Late'
        elif row['delay_days'] <= 14:
            return '8-14 Days Late'
        else:
            return '>14 Days Late'
            
    delivered_reviews['delay_category'] = delivered_reviews.apply(categorize_delay, axis=1)
    
    delay_order = ['On Time or Early', '1-7 Days Late', '8-14 Days Late', '>14 Days Late']
    avg_score_by_delay = delivered_reviews.groupby('delay_category')['review_score'].agg(['mean', 'count']).reindex(delay_order).reset_index()
    
    # Plot review score by delay category
    plt.figure(figsize=(10, 6))
    colors = ['#2b9348', '#e9d8a6', '#ee9b00', '#ae2012']
    sns.barplot(
        x='delay_category',
        y='mean',
        data=avg_score_by_delay,
        palette=colors,
        hue='delay_category',
        legend=False
    )
    plt.title("Average Customer Review Score by Delivery Performance", fontsize=16, fontweight='bold', pad=20)
    plt.xlabel("Delivery Status / Delay", fontsize=12)
    plt.ylabel("Average Review Score (1-5)", fontsize=12)
    plt.ylim(1, 5)
    for index, row in avg_score_by_delay.iterrows():
        plt.text(index, row['mean'] + 0.1, f"{row['mean']:.2f}", color='black', ha="center", fontweight='bold')
    plt.tight_layout()
    plt.savefig('plots/review_score_by_delay.png', dpi=150)
    plt.close()
    
    # Delay by Product Category
    items_products = order_items.merge(products, on='product_id', how='inner')
    order_category_delays = delivered.merge(items_products, on='order_id', how='inner')
    
    cat_delays = order_category_delays.groupby('product_category_name_english').agg(
        order_count=('order_id', 'count'),
        avg_actual_delivery=('actual_delivery_days', 'mean'),
        delay_rate=('is_delayed', 'mean')
    ).reset_index()
    
    # Top 15 categories by order volume
    top_cats = cat_delays.sort_values(by='order_count', ascending=False).head(15).sort_values(by='delay_rate', ascending=False)
    
    plt.figure(figsize=(14, 8))
    sns.barplot(
        x='delay_rate',
        y='product_category_name_english',
        data=top_cats,
        palette='coolwarm',
        hue='product_category_name_english',
        legend=False
    )
    plt.axvline(x=overall_delay_rate, color='black', linestyle='--', label=f'Average Delay Rate ({overall_delay_rate:.1%})')
    plt.title("Delivery Delay Rate for Top 15 Product Categories", fontsize=16, fontweight='bold', pad=20)
    plt.xlabel("Delay Rate", fontsize=12)
    plt.ylabel("Product Category", fontsize=12)
    plt.gca().xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.0%}'))
    plt.legend()
    plt.tight_layout()
    plt.savefig('plots/delay_rate_by_category.png', dpi=150)
    plt.close()
    
    # Convert state_stats and avg_score_by_delay to list of dicts for JSON reporting
    state_stats_top = state_stats.head(5).to_dict(orient='records')
    state_stats_bottom = state_stats.tail(5).to_dict(orient='records')
    
    print(f"Overall delay rate: {overall_delay_rate:.2%}")
    print(f"Avg delivery: {mean_actual_delivery:.1f} days, Avg estimated: {mean_estimated_delivery:.1f} days")
    
    return {
        'avg_actual_delivery_days': float(mean_actual_delivery),
        'avg_estimated_delivery_days': float(mean_estimated_delivery),
        'overall_delay_rate': float(overall_delay_rate),
        'avg_delay_days_for_late_orders': float(mean_delay_for_delayed),
        'correlation_delay_review': float(correlation),
        'score_by_delay_category': avg_score_by_delay.to_dict(orient='records'),
        'top_delay_states': state_stats_top,
        'lowest_delay_states': state_stats_bottom
    }

def analyze_revenue(orders, order_items, customers, products, order_payments):
    print("Performing Revenue Trends Analysis...")
    # Exclude canceled and unavailable orders
    valid_orders = orders[~orders['order_status'].isin(['canceled', 'unavailable'])].copy()
    
    # Merge orders with items
    order_details = valid_orders.merge(order_items, on='order_id', how='inner')
    
    # Calculate item values
    order_details['total_item_value'] = order_details['price']
    order_details['freight_value'] = order_details['freight_value']
    order_details['total_order_value'] = order_details['price'] + order_details['freight_value']
    
    # Monthly sales trend
    order_details['purchase_month'] = order_details['order_purchase_timestamp'].dt.to_period('M')
    
    monthly_sales = order_details.groupby('purchase_month').agg(
        revenue=('price', 'sum'),
        freight=('freight_value', 'sum'),
        total_sales=('total_order_value', 'sum'),
        orders_count=('order_id', 'nunique')
    ).reset_index()
    
    # Clean up months - Olist dataset has full data from Jan 2017 to Aug 2018
    # Filter out extremely small volume months at start/end
    monthly_sales = monthly_sales[(monthly_sales['purchase_month'] >= '2017-01') & (monthly_sales['purchase_month'] <= '2018-08')].copy()
    monthly_sales['purchase_month_str'] = monthly_sales['purchase_month'].astype(str)
    
    # Compute MoM growth
    monthly_sales['revenue_growth'] = monthly_sales['revenue'].pct_change()
    
    # Plot Monthly Revenue & Order Volume
    fig, ax1 = plt.subplots(figsize=(15, 8))
    
    # Bar plot for Revenue
    color_rev = '#1f77b4'
    ax1.set_xlabel('Month', fontsize=12, labelpad=15)
    ax1.set_ylabel('Revenue (BRL Millions)', color=color_rev, fontsize=12)
    bars = ax1.bar(monthly_sales['purchase_month_str'], monthly_sales['revenue'] / 1e6, color=color_rev, alpha=0.7, label='Revenue')
    ax1.tick_params(axis='y', labelcolor=color_rev)
    ax1.set_xticks(range(len(monthly_sales['purchase_month_str'])))
    ax1.set_xticklabels(monthly_sales['purchase_month_str'], rotation=45, ha='right')
    
    # Line plot for Order Count
    ax2 = ax1.twinx()  
    color_orders = '#ff7f0e'
    ax2.set_ylabel('Number of Orders', color=color_orders, fontsize=12)
    line = ax2.plot(monthly_sales['purchase_month_str'], monthly_sales['orders_count'], color=color_orders, marker='o', linewidth=2.5, label='Orders Count')
    ax2.tick_params(axis='y', labelcolor=color_orders)
    
    # Title & Layout
    plt.title("Monthly Revenue and Order Volume Trends (Jan 2017 - Aug 2018)", fontsize=18, fontweight='bold', pad=25)
    fig.tight_layout()
    plt.savefig('plots/monthly_revenue_orders.png', dpi=150)
    plt.close()
    
    # Revenue by Product Category
    cat_details = order_details.merge(products, on='product_id', how='inner')
    cat_revenue = cat_details.groupby('product_category_name_english').agg(
        revenue=('price', 'sum'),
        orders_count=('order_id', 'nunique')
    ).reset_index().sort_values(by='revenue', ascending=False)
    
    # Plot top 10 product categories by revenue
    plt.figure(figsize=(12, 8))
    sns.barplot(
        x='revenue',
        y='product_category_name_english',
        data=cat_revenue.head(10),
        palette='viridis',
        hue='product_category_name_english',
        legend=False
    )
    plt.title("Top 10 Product Categories by Revenue (BRL)", fontsize=16, fontweight='bold', pad=20)
    plt.xlabel("Total Revenue (BRL)", fontsize=12)
    plt.ylabel("Product Category", fontsize=12)
    plt.gca().xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:,.0f} BRL'))
    plt.tight_layout()
    plt.savefig('plots/top_categories_revenue.png', dpi=150)
    plt.close()
    
    # Revenue by State
    state_details = order_details.merge(customers, on='customer_id', how='inner')
    state_revenue = state_details.groupby('customer_state').agg(
        revenue=('price', 'sum'),
        orders_count=('order_id', 'nunique')
    ).reset_index().sort_values(by='revenue', ascending=False)
    
    # Plot top 10 states by revenue
    plt.figure(figsize=(12, 8))
    sns.barplot(
        x='revenue',
        y='customer_state',
        data=state_revenue.head(10),
        palette='magma',
        hue='customer_state',
        legend=False
    )
    plt.title("Top 10 Brazilian States by Revenue (BRL)", fontsize=16, fontweight='bold', pad=20)
    plt.xlabel("Total Revenue (BRL)", fontsize=12)
    plt.ylabel("State", fontsize=12)
    plt.gca().xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:,.0f} BRL'))
    plt.tight_layout()
    plt.savefig('plots/top_states_revenue.png', dpi=150)
    plt.close()
    
    # Payment Method Analysis
    payment_stats = order_payments.groupby('payment_type').agg(
        total_payment_value=('payment_value', 'sum'),
        transaction_count=('order_id', 'count')
    ).reset_index().sort_values(by='total_payment_value', ascending=False)
    
    # Filter out 'not_defined'
    payment_stats = payment_stats[payment_stats['payment_type'] != 'not_defined']
    
    # Plot payment method donut chart
    plt.figure(figsize=(8, 8))
    colors_pie = ['#3a86c8', '#8338ec', '#ff006e', '#ffbe0b']
    plt.pie(
        payment_stats['total_payment_value'],
        labels=payment_stats['payment_type'].str.replace('_', ' ').str.title(),
        autopct='%1.1f%%',
        startangle=140,
        colors=colors_pie,
        wedgeprops=dict(width=0.4, edgecolor='w')
    )
    plt.title("Payment Methods Share by Value", fontsize=16, fontweight='bold', pad=20)
    plt.tight_layout()
    plt.savefig('plots/payment_methods_share.png', dpi=150)
    plt.close()
    
    # Summary of metrics
    total_rev = float(order_details['price'].sum())
    total_freight = float(order_details['freight_value'].sum())
    freight_ratio = total_freight / (total_rev + total_freight)
    avg_order_value = float(order_details.groupby('order_id')['price'].sum().mean())
    
    # Convert monthly_sales to list of dicts for JSON reporting (drop Period column to prevent serialization error)
    monthly_sales_json = monthly_sales.drop(columns=['purchase_month']).copy()
    monthly_sales_clean = monthly_sales_json.to_dict(orient='records')
    for m in monthly_sales_clean:
        if pd.isna(m['revenue_growth']):
            m['revenue_growth'] = None
            
    print(f"Total Revenue: {total_rev:,.2f} BRL")
    print(f"Average Order Value: {avg_order_value:.2f} BRL")
    
    return {
        'total_revenue': total_rev,
        'total_freight': total_freight,
        'freight_ratio': freight_ratio,
        'avg_order_value': avg_order_value,
        'top_categories_revenue': cat_revenue.head(5).to_dict(orient='records'),
        'top_states_revenue': state_revenue.head(5).to_dict(orient='records'),
        'monthly_sales': monthly_sales_clean,
        'payment_methods': payment_stats.to_dict(orient='records')
    }

def main():
    print("Starting analysis script...")
    
    # Load
    customers, orders, order_items, order_payments, order_reviews, products, category_translation = load_data()
    
    # Clean
    customers, orders, order_items, order_payments, order_reviews, products = preprocess_data(
        customers, orders, order_items, order_payments, order_reviews, products, category_translation
    )
    
    # Run analyses
    retention_results = analyze_retention(customers, orders)
    delivery_results = analyze_delivery_delays(orders, customers, order_reviews, order_items, products)
    revenue_results = analyze_revenue(orders, order_items, customers, products, order_payments)
    
    # Combine results
    summary = {
        'retention': retention_results,
        'delivery': delivery_results,
        'revenue': revenue_results
    }
    
    # Save to JSON for report reference
    with open('analysis_summary.json', 'w') as f:
        json.dump(summary, f, indent=4)
        
    print("Analysis finished. Results saved to analysis_summary.json and plots generated in plots/.")

if __name__ == "__main__":
    main()
