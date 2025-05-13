# ML on the Fly

A dynamic ML model generation and training system that analyzes CSV data and creates appropriate models automatically.

## Overview

This system allows users to:
1. Upload CSV files
2. Analyze the data structure and features
3. Select a target column for prediction
4. Automatically generate appropriate ML models
5. Train the model on the data
6. Get insights from the trained model
7. Make predictions with new data

The system uses Claude 3.7 Sonnet to dynamically generate model code based on the data characteristics.

## Setup

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up environment variables:
   ```
   LITELLM_API_KEY=your_api_key_here
   ```

## API Endpoints

- `GET /`: Health check
- `POST /upload-csv`: Upload and process a CSV file
- `POST /select-target`: Select the target column for prediction
- `POST /generate-model`: Generate a model based on the dataset
- `POST /train-model`: Train the generated model
- `GET /insights`: Get insights from the trained model
- `POST /predict`: Make predictions using the trained model
- `GET /model-code`: Get the generated model code

## Usage Example

1. Start the server:
   ```
   python api.py
   ```

2. The API will be available at http://localhost:8000

3. You can use the FastAPI OpenAPI documentation at http://localhost:8000/docs to interact with the API

## How It Works

1. **CSV Handling**: The system uploads and analyzes the CSV file to understand data types, missing values, and other statistics.

2. **Problem Detection**: Based on the target column, the system determines if this is a classification or regression problem.

3. **Model Generation**: Using Claude 3.7 Sonnet, the system generates Python code for an appropriate ML model.

4. **Model Training**: The system trains the generated model on the provided data.

5. **Insights and Prediction**: The trained model can provide insights about the data and make predictions on new inputs. 