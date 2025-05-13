import os
import pandas as pd
import json
from ml_service import MLService

"""
This script demonstrates how to use the ML on-the-fly API with the Sales dataset.
It follows the complete workflow of:
1. Uploading a CSV file
2. Selecting a target column
3. Generating a model
4. Training the model
5. Getting insights
6. Making predictions
"""

def run_sales_prediction():
    """Predict sales (revenue) based on other features"""
    # Create ML service
    ml_service = MLService()
    
    # 1. Upload CSV file
    print("\n1. Uploading sales data CSV file...")
    # Use a path that works regardless of where the script is executed from
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_file = os.path.join(script_dir, "sales_data.csv")  # Path to CSV file
    
    try:
        with open(csv_file, 'rb') as f:
            file_content = f.read()
        result = ml_service.process_csv(file_content)
    except FileNotFoundError:
        print(f"Error: File {csv_file} not found!")
        return
    
    if not result.get("success", False):
        print(f"Error: {result.get('error', 'Unknown error')}")
        return
        
    print("CSV uploaded and processed successfully.")
    
    # Print data summary
    data_summary = result["data_summary"]
    print("\nData Summary:")
    print(f"- Rows: {data_summary['num_rows']}")
    print(f"- Columns: {data_summary['num_cols']}")
    print(f"- Available columns: {', '.join(data_summary['columns'][:10])}...")
    
    # 2. Select target column - regression task
    target_column = "revenue"
    print(f"\n2. Selecting target column: {target_column} (regression task)")
    result = ml_service.select_target_column(target_column)
    
    if not result.get("success", False):
        print(f"Error: {result.get('error', 'Unknown error')}")
        return
        
    print(f"Target column selected. Detected problem type: {result['problem_type']}")
    
    # 3. Generate model
    print("\n3. Generating model...")
    result = ml_service.generate_model()
    
    if not result.get("success", False):
        print(f"Error: {result.get('error', 'Unknown error')}")
        return
        
    print(f"Model generated successfully. Problem type: {result['problem_type']}")
    if 'model_source' in result:
        print(f"Model was created using: {result['model_source']}")
    
    # 4. Train model
    print("\n4. Training model...")
    result = ml_service.train_model()
    
    if not result.get("success", False):
        print(f"Error: {result.get('error', 'Unknown error')}")
        return
        
    print("Model trained successfully.")
    
    print("\nTraining summary:")
    print(json.dumps(result["training_summary"], indent=2))
    
    # 5. Get insights
    print("\n5. Getting insights...")
    result = ml_service.get_insights()
    
    if not result.get("success", False):
        print(f"Error: {result.get('error', 'Unknown error')}")
        return
        
    print("\nModel Insights:")
    print(json.dumps(result["insights"], indent=2))
    
    # 6. Make predictions
    print("\n6. Making predictions...")
    # Create sample data for prediction
    sample_input = {
        'day_of_week': 'Saturday',
        'month': 'December',
        'is_weekend': 1,
        'is_holiday': 1,
        'product_category': 'Electronics',
        'customer_age_group': '25-34',
        'customer_gender': 'Male',
        'region': 'East',
        'store_size': 'Large',
        'marketing_campaign': 'Holiday Special',
        'previous_customer': 1,
        'items_purchased': 3,
        'product_name': 'Laptop',
        'base_price': 1000,
        'discount_percentage': 20,
        'price': 800
    }
    
    # Make prediction
    result = ml_service.predict(sample_input)
    
    if not result.get("success", False):
        print(f"Error: {result.get('error', 'Unknown error')}")
        return
        
    print("\nPrediction result (High-value purchase during holiday season):")
    print(f"Predicted revenue: ${result['prediction']:.2f}")
    
    # Try another prediction for a lower-value purchase
    sample_input_2 = {
        'day_of_week': 'Tuesday',
        'month': 'April',
        'is_weekend': 0,
        'is_holiday': 0,
        'product_category': 'Books',
        'customer_age_group': '45-54',
        'customer_gender': 'Female',
        'region': 'West',
        'store_size': 'Small',
        'marketing_campaign': None,
        'previous_customer': 0,
        'items_purchased': 2,
        'product_name': 'Fiction',
        'base_price': 25,
        'discount_percentage': 5,
        'price': 23.75
    }
    
    result = ml_service.predict(sample_input_2)
    
    if not result.get("success", False):
        print(f"Error: {result.get('error', 'Unknown error')}")
        return
        
    print("\nPrediction result (Low-value purchase on weekday):")
    print(f"Predicted revenue: ${result['prediction']:.2f}")
    
    # 7. Get model code
    print("\n7. Getting model code...")
    result = ml_service.get_model_code()
    
    if not result.get("success", False):
        print(f"Error: {result.get('error', 'Unknown error')}")
        return
        
    # Display the model source first
    if 'model_source' in result:
        print(f"\nModel was generated by: {result['model_source']}")
    
    # Display the first 10 lines of the model code
    code_lines = result["model_code"].split('\n')
    print("\nGenerated Model Code (first 10 lines):")
    for i in range(min(10, len(code_lines))):
        print(code_lines[i])
    print("...")

def run_satisfaction_prediction():
    """Predict customer satisfaction (1-5) based on other features"""
    # Create ML service
    ml_service = MLService()
    
    # 1. Upload CSV file
    print("\n1. Uploading sales data CSV file...")
    # Use a path that works regardless of where the script is executed from
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_file = os.path.join(script_dir, "sales_data.csv")  # Path to CSV file
    
    try:
        with open(csv_file, 'rb') as f:
            file_content = f.read()
        result = ml_service.process_csv(file_content)
    except FileNotFoundError:
        print(f"Error: File {csv_file} not found!")
        return
    
    if not result.get("success", False):
        print(f"Error: {result.get('error', 'Unknown error')}")
        return
        
    print("CSV uploaded and processed successfully.")
    
    # 2. Select target column - classification task
    target_column = "customer_satisfaction"
    print(f"\n2. Selecting target column: {target_column} (classification task)")
    result = ml_service.select_target_column(target_column)
    
    if not result.get("success", False):
        print(f"Error: {result.get('error', 'Unknown error')}")
        return
        
    print(f"Target column selected. Detected problem type: {result['problem_type']}")
    
    # 3. Generate model
    print("\n3. Generating model...")
    result = ml_service.generate_model()
    
    if not result.get("success", False):
        print(f"Error: {result.get('error', 'Unknown error')}")
        return
        
    print(f"Model generated successfully. Problem type: {result['problem_type']}")
    if 'model_source' in result:
        print(f"Model was created using: {result['model_source']}")
    
    # 4. Train model
    print("\n4. Training model...")
    result = ml_service.train_model()
    
    if not result.get("success", False):
        print(f"Error: {result.get('error', 'Unknown error')}")
        return
        
    print("Model trained successfully.")
    
    print("\nTraining summary:")
    print(json.dumps(result["training_summary"], indent=2))
    
    # 5. Get insights
    print("\n5. Getting insights...")
    result = ml_service.get_insights()
    
    if not result.get("success", False):
        print(f"Error: {result.get('error', 'Unknown error')}")
        return
        
    print("\nModel Insights:")
    print(json.dumps(result["insights"], indent=2))
    
    # 6. Make predictions
    print("\n6. Making predictions...")
    # Create sample data for prediction
    sample_input = {
        'day_of_week': 'Saturday',
        'month': 'December',
        'is_weekend': 1,
        'is_holiday': 1,
        'product_category': 'Electronics',
        'customer_age_group': '25-34',
        'customer_gender': 'Male',
        'region': 'East',
        'store_size': 'Large',
        'marketing_campaign': 'Holiday Special',
        'previous_customer': 1,
        'items_purchased': 3,
        'product_name': 'Laptop',
        'base_price': 1000,
        'discount_percentage': 30,
        'price': 700,
        'revenue': 2100,
        'conversion': 1
    }
    
    # Make prediction
    result = ml_service.predict(sample_input)
    
    if not result.get("success", False):
        print(f"Error: {result.get('error', 'Unknown error')}")
        return
        
    print("\nPrediction result (Returning customer with high discount):")
    print(f"Predicted satisfaction: {result['prediction']} (on a scale of 1-5)")
    
    # Try another prediction with different features
    sample_input_2 = {
        'day_of_week': 'Tuesday',
        'month': 'April',
        'is_weekend': 0,
        'is_holiday': 0,
        'product_category': 'Books',
        'customer_age_group': '45-54',
        'customer_gender': 'Female',
        'region': 'West',
        'store_size': 'Small',
        'marketing_campaign': None,
        'previous_customer': 0,
        'items_purchased': 2,
        'product_name': 'Fiction',
        'base_price': 25,
        'discount_percentage': 0,
        'price': 25,
        'revenue': 50,
        'conversion': 1
    }
    
    result = ml_service.predict(sample_input_2)
    
    if not result.get("success", False):
        print(f"Error: {result.get('error', 'Unknown error')}")
        return
        
    print("\nPrediction result (New customer, no discount):")
    print(f"Predicted satisfaction: {result['prediction']} (on a scale of 1-5)")
    
    # 7. Get model code
    print("\n7. Getting model code...")
    result = ml_service.get_model_code()
    
    if not result.get("success", False):
        print(f"Error: {result.get('error', 'Unknown error')}")
        return
    
    # Display the model source
    if 'model_source' in result:
        print(f"\nModel was generated by: {result['model_source']}")
    
    # Display the first 10 lines of the model code
    code_lines = result["model_code"].split('\n')
    print("\nGenerated Model Code (first 10 lines):")
    for i in range(min(10, len(code_lines))):
        print(code_lines[i])
    print("...")

if __name__ == "__main__":
    print("===== SALES DATA ML EXAMPLE =====")
    
    # Ask user which prediction to run
    print("\nChoose a prediction type:")
    print("1. Predict sales revenue (regression task)")
    print("2. Predict customer satisfaction (classification task)")
    
    choice = input("\nEnter your choice (1 or 2): ")
    
    if choice == "1":
        run_sales_prediction()
    elif choice == "2":
        run_satisfaction_prediction()
    else:
        print("Invalid choice. Please run again and enter 1 or 2.") 