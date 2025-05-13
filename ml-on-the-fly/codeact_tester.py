# ML prediction tool using sample_data.csv
# This script uses ML to predict the target column in sample_data.csv

from openai import OpenAI
import os
import pandas as pd
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, r2_score
import numpy as np

# Configure OpenAI SDK to use LiteLLM
OPENAI_API_KEY = os.getenv("LITELLM_API_KEY")
API_BASE_URL = "https://litellm.deriv.ai/v1"
MODEL_NAME = "gpt-4.1"

# Initialize client with LiteLLM endpoint
client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=API_BASE_URL
)

def query_csv_predictor(csv_path: str, target_column: str, feature_columns: list) -> str:
    """
    Perform auto-ML prediction on a CSV (regression or classification).
    """
    print(f"Loading CSV from: {csv_path}")
    df = pd.read_csv(csv_path)
    print(f"Columns in dataset: {df.columns.tolist()}")
    
    # Ensure target column exists
    if target_column not in df.columns:
        return f"Error: Target column '{target_column}' not found in the dataset."
        
    # Ensure all feature columns exist
    missing_features = [col for col in feature_columns if col not in df.columns]
    if missing_features:
        return f"Error: Feature columns {missing_features} not found in the dataset."
    
    # Get features and target
    X = df[feature_columns]
    y = df[target_column]
    
    # Handle categorical features
    for col in X.columns:
        if X[col].dtype == 'object':
            X[col] = LabelEncoder().fit_transform(X[col])
    
    # Print dataset info for debugging
    print(f"Dataset shape: {df.shape}")
    print(f"Target column '{target_column}' - unique values: {y.nunique()}")
    print(f"Target column type: {y.dtype}")

    # Determine task type
    is_classification = False
    if y.dtype == 'object' or y.nunique() <= 10:
        print("Detected classification task")
        is_classification = True
        # Classification
        le = LabelEncoder()
        y_encoded = le.fit_transform(y)
        model = LogisticRegression(max_iter=1000)
        model.fit(X, y_encoded)
        
        # Make prediction on all data to show accuracy
        predictions = model.predict(X)
        accuracy = accuracy_score(y_encoded, predictions)
        
        # For demonstration, predict on first 3 rows
        sample_rows = 3
        prediction_inputs = X.iloc[:sample_rows]
        predictions = model.predict(prediction_inputs)
        
        # Convert numeric predictions back to original labels
        original_predictions = le.inverse_transform(predictions)
        
        results = f"Classification task for '{target_column}'\n"
        results += f"Model accuracy: {accuracy:.4f}\n"
        results += f"Sample predictions for first {sample_rows} rows:\n"
        
        for i, pred in enumerate(original_predictions):
            results += f"Row {i+1}: Predicted {target_column} = {pred} (Actual: {y.iloc[i]})\n"
            
        return results
    else:
        print("Detected regression task")
        # Regression
        model = LinearRegression()
        model.fit(X, y)
        
        # Make prediction on all data to show R²
        predictions = model.predict(X)
        r2 = r2_score(y, predictions)
        
        # For demonstration, predict on first 3 rows
        sample_rows = 3
        prediction_inputs = X.iloc[:sample_rows]
        predictions = model.predict(prediction_inputs)
        
        results = f"Regression task for '{target_column}'\n"
        results += f"Model R² score: {r2:.4f}\n"
        results += f"Sample predictions for first {sample_rows} rows:\n"
        
        for i, pred in enumerate(predictions):
            results += f"Row {i+1}: Predicted {target_column} = {pred:.2f} (Actual: {y.iloc[i]})\n"
            
        return results

def get_litellm_completion(prompt):
    """Get a completion from LiteLLM API"""
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant specialized in data science and machine learning."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error calling LiteLLM API: {str(e)}")
        return f"Error: {str(e)}"

if __name__ == "__main__":
    print("\n=== ML On-The-Fly using LiteLLM ===")
    
    # Test LiteLLM API
    print("\nTesting LiteLLM API connection...")
    response = get_litellm_completion("What is machine learning?")
    print(f"LiteLLM API response: {response[:100]}..." if len(response) > 100 else response)
    
    # Run ML prediction
    print("\n=== Running ML prediction on sample_data.csv ===")
    csv_path = "sample_data.csv"
    target_column = "target"
    feature_columns = ["sepal_length", "sepal_width", "petal_length", "petal_width"]
    
    result = query_csv_predictor(
        csv_path=csv_path,
        target_column=target_column,
        feature_columns=feature_columns
    )
    
    print("\nML Prediction Results:")
    print(result)
    
    # Get AI analysis of the results
    print("\n=== AI Analysis of Results ===")
    analysis_prompt = f"""
    I ran an ML prediction on the Iris dataset with these results:
    
    {result}
    
    Provide a brief analysis of these results in 3-4 sentences. What does the accuracy/score indicate?
    What might be the most important features for prediction?
    """
    
    analysis = get_litellm_completion(analysis_prompt)
    print(analysis)