import os
import traceback
from typing import Dict, Any, Optional, List, Tuple
import json
import pandas as pd
import numpy as np

from csv_handler import CSVHandler
from model_generator import ModelGenerator

class MLService:
    def __init__(self):
        self.csv_handler = CSVHandler()
        self.model_generator = ModelGenerator()
        self.dynamic_model = None
        self.model_code = None
        self.model_source = None  # Track which LLM generated the code
        self.target_column = None
        self.problem_type = None
        self.is_trained = False
        self.training_summary = None
        
    def process_csv(self, file_content: bytes) -> Dict[str, Any]:
        """Process a CSV file and return data summary"""
        try:
            success = self.csv_handler.load_csv(file_content)
            if not success:
                return {"success": False, "error": "Failed to load CSV file"}
                
            data_summary = self.csv_handler.get_data_summary()
            return {"success": True, "data_summary": data_summary}
            
        except Exception as e:
            traceback_str = traceback.format_exc()
            return {"success": False, "error": str(e), "traceback": traceback_str}
            
    def select_target_column(self, target_column: str) -> Dict[str, Any]:
        """Set the target column and suggest problem type"""
        try:
            if self.csv_handler.df is None:
                return {"success": False, "error": "No data loaded. Please upload a CSV file first."}
                
            if target_column not in self.csv_handler.df.columns:
                return {"success": False, "error": f"Column '{target_column}' not found in the dataset"}
                
            self.target_column = target_column
            self.problem_type = self.csv_handler.suggest_problem_type(target_column)
            
            return {
                "success": True, 
                "target_column": target_column, 
                "problem_type": self.problem_type
            }
            
        except Exception as e:
            traceback_str = traceback.format_exc()
            return {"success": False, "error": str(e), "traceback": traceback_str}
            
    def generate_model(self, problem_type: Optional[str] = None) -> Dict[str, Any]:
        """Generate a model based on the dataset and problem type"""
        try:
            if self.csv_handler.df is None:
                return {"success": False, "error": "No data loaded. Please upload a CSV file first."}
                
            if self.target_column is None:
                return {"success": False, "error": "Target column not set. Please select a target column first."}
                
            # Override problem_type if specified
            if problem_type:
                self.problem_type = problem_type
                
            data_summary = self.csv_handler.get_data_summary()
            self.model_code, self.model_source = self.model_generator.generate_model_code(
                data_summary, 
                self.target_column, 
                self.problem_type
            )
            
            # Attempt to instantiate the model
            try:
                self.dynamic_model = self.model_generator.instantiate_model(self.model_code)
                return {
                    "success": True,
                    "message": f"Model generated successfully using {self.model_source}",
                    "problem_type": self.problem_type,
                    "model_source": self.model_source
                }
            except Exception as model_error:
                # Try to refine the model if instantiation fails
                error_message = str(model_error)
                refined_code, refiner_model = self.model_generator.refine_model_code(self.model_code, error_message)
                self.model_code = refined_code
                self.model_source = f"{self.model_source} (refined by {refiner_model})"
                
                # Try again with refined code
                self.dynamic_model = self.model_generator.instantiate_model(self.model_code)
                return {
                    "success": True,
                    "message": f"Model generated successfully after refinement using {self.model_source}",
                    "problem_type": self.problem_type,
                    "model_source": self.model_source
                }
                
        except Exception as e:
            traceback_str = traceback.format_exc()
            return {"success": False, "error": str(e), "traceback": traceback_str}
            
    def train_model(self) -> Dict[str, Any]:
        """Train the generated model on the dataset"""
        try:
            if self.csv_handler.df is None:
                return {"success": False, "error": "No data loaded. Please upload a CSV file first."}
                
            if self.target_column is None:
                return {"success": False, "error": "Target column not set. Please select a target column first."}
                
            if self.dynamic_model is None:
                return {"success": False, "error": "Model not generated. Please generate a model first."}
            
            print(f"Training model for target: {self.target_column}, problem type: {self.problem_type}")
                
            # Get feature and target data
            X, y = self.csv_handler.get_feature_target_split(self.target_column)
            
            print(f"Features shape: {X.shape}, Target shape: {y.shape}")
            print(f"First 5 feature columns: {list(X.columns)[:5]}...")
            
            # Verify the model has all required methods
            required_methods = ['fit_preprocessing', 'preprocess_data', 'train', 'evaluate', 'predict']
            missing_methods = []
            for method in required_methods:
                if not hasattr(self.dynamic_model, method) or not callable(getattr(self.dynamic_model, method)):
                    missing_methods.append(method)
            
            if missing_methods:
                error_msg = f"Model is missing required methods: {', '.join(missing_methods)}"
                print(f"CRITICAL ERROR: {error_msg}")
                return {"success": False, "error": error_msg}
            
            # Step 1: Fit preprocessing transformers
            try:
                print("Fitting preprocessing transformers...")
                self.dynamic_model.fit_preprocessing(X)
                print("Preprocessing transformers fitted successfully.")
            except Exception as prep_error:
                error_msg = f"Error during preprocessing fit: {str(prep_error)}"
                traceback_str = traceback.format_exc()
                print(f"PREPROCESSING ERROR: {error_msg}")
                print(f"Traceback: {traceback_str}")
                return {"success": False, "error": error_msg, "traceback": traceback_str}
            
            # Step 2: Transform the data
            try:
                print("Preprocessing data...")
                X_processed = self.dynamic_model.preprocess_data(X)
                print(f"Data preprocessed successfully. Shape after preprocessing: {X_processed.shape}")
            except Exception as transform_error:
                error_msg = f"Error during data preprocessing: {str(transform_error)}"
                traceback_str = traceback.format_exc()
                print(f"TRANSFORMATION ERROR: {error_msg}")
                print(f"Traceback: {traceback_str}")
                return {"success": False, "error": error_msg, "traceback": traceback_str}
            
            # Step 3: Train the model
            try:
                print("Training model...")
                self.dynamic_model.train(X_processed, y)
                print("Model trained successfully.")
            except Exception as train_error:
                error_msg = f"Error during model training: {str(train_error)}"
                traceback_str = traceback.format_exc()
                print(f"TRAINING ERROR: {error_msg}")
                print(f"Traceback: {traceback_str}")
                return {"success": False, "error": error_msg, "traceback": traceback_str}
            
            # Step 4: Evaluate the model
            try:
                print("Evaluating model performance...")
                metrics = self.dynamic_model.evaluate(X_processed, y)
                print(f"Model evaluated successfully. Metrics: {metrics}")
            except Exception as eval_error:
                error_msg = f"Error during evaluation: {str(eval_error)}"
                traceback_str = traceback.format_exc()
                print(f"EVALUATION ERROR: {error_msg}")
                return {"success": False, "error": error_msg, "traceback": traceback_str}
            
            # Step 5: Get feature importance if available
            try:
                print("Getting feature importance...")
                feature_importance = self.dynamic_model.get_feature_importance()
                print("Feature importance retrieved successfully.")
            except Exception as feat_error:
                print(f"WARNING: Could not get feature importance: {str(feat_error)}")
                feature_importance = {"warning": f"Feature importance not available: {str(feat_error)}"}
                
            self.is_trained = True
            self.training_summary = {
                "metrics": metrics,
                "feature_importance": feature_importance
            }
            
            return {
                "success": True,
                "message": "Model trained successfully",
                "training_summary": self.training_summary
            }
            
        except Exception as e:
            traceback_str = traceback.format_exc()
            print(f"GENERAL TRAINING ERROR: {str(e)}")
            print(f"Traceback: {traceback_str}")
            return {"success": False, "error": str(e), "traceback": traceback_str}
            
    def get_insights(self) -> Dict[str, Any]:
        """Get insights from the trained model"""
        try:
            if not self.is_trained:
                return {"success": False, "error": "Model not trained. Please train the model first."}
                
            insights = {
                "model_type": self.problem_type,
                "training_metrics": self.training_summary["metrics"],
                "feature_importance": self.training_summary.get("feature_importance", {})
            }
            
            # Add problem-specific insights
            if self.problem_type == "classification":
                # Try to get class distribution if available
                try:
                    y = self.csv_handler.df[self.target_column]
                    class_distribution = y.value_counts().to_dict()
                    insights["class_distribution"] = class_distribution
                except:
                    pass
                    
            elif self.problem_type == "regression":
                # Try to get target distribution statistics if available
                try:
                    y = self.csv_handler.df[self.target_column]
                    target_stats = {
                        "min": float(y.min()),
                        "max": float(y.max()),
                        "mean": float(y.mean()),
                        "median": float(y.median()),
                        "std": float(y.std())
                    }
                    insights["target_statistics"] = target_stats
                except:
                    pass
            
            return {
                "success": True,
                "insights": insights
            }
            
        except Exception as e:
            traceback_str = traceback.format_exc()
            return {"success": False, "error": str(e), "traceback": traceback_str}
            
    def predict(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Make predictions using the trained model"""
        try:
            if not self.is_trained:
                return {"success": False, "error": "Model not trained. Please train the model first."}
                
            # Convert input dictionary to DataFrame
            input_df = pd.DataFrame([input_data])
            
            # Preprocess the input data - this should use the already fitted preprocessor
            # and return a DataFrame with named columns (feature_names_out_)
            processed_input_df = self.dynamic_model.preprocess_data(input_df)
            
            # Make prediction - this returns a NumPy array
            prediction_array = self.dynamic_model.predict(processed_input_df)
            
            # For a single input, prediction_array should have one element.
            # Extract it to be a scalar for JSON serialization and for example_sales.py.
            if isinstance(prediction_array, np.ndarray) and prediction_array.ndim > 0:
                # If it's an array of one element, get that element.
                # Otherwise, if it's a multi-output or something unexpected, convert to list.
                prediction_to_return = prediction_array[0] if prediction_array.size == 1 else prediction_array.tolist()
            else:
                # If it's already a scalar (e.g. np.float64), it's fine
                prediction_to_return = prediction_array 

            # Ensure the prediction is a Python native type for JSON
            if hasattr(prediction_to_return, 'item'): # Handles numpy scalar types like np.float64, np.int64
                prediction_to_return = prediction_to_return.item()
                
            return {
                "success": True,
                "prediction": prediction_to_return
            }
            
        except Exception as e:
            traceback_str = traceback.format_exc()
            print(f"PREDICTION ERROR in MLService: {str(e)}")
            print(f"Traceback: {traceback_str}")
            return {"success": False, "error": str(e), "traceback": traceback_str}
            
    def get_model_code(self) -> Dict[str, Any]:
        """Return the generated model code"""
        if self.model_code is None:
            return {"success": False, "error": "No model has been generated yet."}
            
        return {
            "success": True,
            "model_code": self.model_code,
            "model_source": self.model_source
        } 