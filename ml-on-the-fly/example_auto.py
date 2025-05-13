import os
import requests
import json
from pprint import pprint

"""
This script demonstrates how to use the ML on-the-fly API with the Automotive dataset.
It follows the complete workflow of:
1. Uploading a CSV file
2. Selecting a target column
3. Generating a model
4. Training the model
5. Getting insights
6. Making predictions
"""

# API base URL
API_URL = "http://localhost:8001"

def main():
    # 1. Upload CSV file
    print("\n1. Uploading CSV file...")
    # Copy the automotive dataset to the local directory if it doesn't exist
    auto_csv_path = "auto_data.csv"
    if not os.path.exists(auto_csv_path):
        source_path = "../GargashDefaultDatasets/AUTO_RTA_Carregistration_ext.csv"
        if os.path.exists(source_path):
            import shutil
            shutil.copy(source_path, auto_csv_path)
            print(f"Copied automotive dataset to {auto_csv_path}")
        else:
            print(f"Error: Source file {source_path} not found.")
            return
    
    with open(auto_csv_path, "rb") as file:
        files = {"file": file}
        response = requests.post(f"{API_URL}/upload-csv", files=files)
    
    if response.status_code != 200:
        print(f"Error uploading CSV: {response.text}")
        return
    
    data_summary = response.json()
    print("CSV uploaded and processed successfully.")
    print("\nData Summary:")
    print(f"- Rows: {data_summary['data_summary']['num_rows']}")
    print(f"- Columns: {data_summary['data_summary']['num_cols']}")
    print(f"- Available columns: {', '.join(data_summary['data_summary']['columns'][:5])}... (and more)")
    
    # 2. Select target column - let's predict manufacture_year as an example
    target_column = "manufacture_year"  # This is a regression task
    print(f"\n2. Selecting target column: {target_column}")
    
    response = requests.post(
        f"{API_URL}/select-target",
        data={"target_column": target_column}
    )
    
    if response.status_code != 200:
        print(f"Error selecting target column: {response.text}")
        return
    
    target_result = response.json()
    problem_type = target_result["problem_type"]
    print(f"Target column selected. Detected problem type: {problem_type}")
    
    # 3. Generate model
    print("\n3. Generating model...")
    response = requests.post(f"{API_URL}/generate-model")
    
    if response.status_code != 200:
        print(f"Error generating model: {response.text}")
        return
    
    model_result = response.json()
    print(f"Model generated successfully. Problem type: {model_result['problem_type']}")
    
    # 4. Train model
    print("\n4. Training model...")
    response = requests.post(f"{API_URL}/train-model")
    
    if response.status_code != 200:
        print(f"Error training model: {response.text}")
        return
    
    train_result = response.json()
    print("Model trained successfully.")
    print("\nTraining summary:")
    pprint(train_result["training_summary"])
    
    # 5. Get insights
    print("\n5. Getting insights...")
    response = requests.get(f"{API_URL}/insights")
    
    if response.status_code != 200:
        print(f"Error getting insights: {response.text}")
        return
    
    insights = response.json()
    print("\nModel Insights:")
    pprint(insights["insights"])
    
    # 6. Make a prediction
    # Sample input matching automotive data features (excluding the target)
    print("\n6. Making a prediction...")
    sample_input = {
        "registration_date": "03/03/2021",
        "nationality_e": "United States",
        "gender_e": "MALE",
        "person_birth_year": 1990,
        "vechile_type": "Light Vehicle",
        "cylinders_num": 6,
        "cylinder_capacity": 3000.0,
        "color": "Black",
        "business_individual": "Private",
        "fuel_type": "Benzene",
        "transmission_manual_automatic": "Yes",
        "number_of_passenger_seating_capcity": 5.0,
        "number_of_doors": 4.0,
        "brand_model": "CAMARO",
        "empty_weight": 1500,
        "orgin_country_the_place_where_assembled": "United States",
        "manufacturer_brand_name": "CHEVROLET"
    }
    
    response = requests.post(
        f"{API_URL}/predict",
        json=sample_input
    )
    
    if response.status_code != 200:
        print(f"Error making prediction: {response.text}")
        return
    
    prediction = response.json()
    print("\nPrediction result:")
    pprint(prediction["prediction"])
    
    # Try another prediction with different input
    sample_input_2 = {
        "registration_date": "05/10/2021",
        "nationality_e": "Japan",
        "gender_e": "FEMALE",
        "person_birth_year": 1985,
        "vechile_type": "Light Vehicle",
        "cylinders_num": 4,
        "cylinder_capacity": 2000.0,
        "color": "White",
        "business_individual": "Private",
        "fuel_type": "Benzene",
        "transmission_manual_automatic": "Yes",
        "number_of_passenger_seating_capcity": 5.0,
        "number_of_doors": 4.0,
        "brand_model": "COROLLA",
        "empty_weight": 1200,
        "orgin_country_the_place_where_assembled": "Japan",
        "manufacturer_brand_name": "TOYOTA"
    }
    
    response = requests.post(
        f"{API_URL}/predict",
        json=sample_input_2
    )
    
    if response.status_code == 200:
        prediction_2 = response.json()
        print("\nPrediction result for second sample:")
        pprint(prediction_2["prediction"])
    
    # 7. Get model code (optional)
    print("\n7. Getting model code...")
    response = requests.get(f"{API_URL}/model-code")
    
    if response.status_code != 200:
        print(f"Error getting model code: {response.text}")
        return
    
    model_code = response.json()
    print("\nGenerated Model Code (first 10 lines):")
    print("\n".join(model_code["model_code"].split("\n")[:10]) + "\n...")

if __name__ == "__main__":
    main() 