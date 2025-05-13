import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
import io
import json

class CSVHandler:
    def __init__(self):
        self.df = None
        self.data_summary = None
        
    def load_csv(self, file_content: bytes) -> bool:
        """Load CSV data from uploaded file content"""
        try:
            self.df = pd.read_csv(io.BytesIO(file_content))
            self._analyze_data()
            return True
        except Exception as e:
            print(f"Error loading CSV: {str(e)}")
            return False
            
    def upload_csv(self, file_content: bytes) -> bool:
        """Alias for load_csv for backward compatibility"""
        return self.load_csv(file_content)
            
    def _analyze_data(self) -> None:
        """Analyze the loaded dataframe and generate summary statistics"""
        if self.df is None:
            return
            
        # Basic dataframe info
        num_rows, num_cols = self.df.shape
        columns = list(self.df.columns)
        
        # Data types per column
        dtypes = self.df.dtypes.apply(lambda x: str(x)).to_dict()
        
        # Count of null values
        null_counts = self.df.isnull().sum().to_dict()
        
        # Basic statistics for numeric columns
        numeric_columns = self.df.select_dtypes(include=[np.number]).columns.tolist()
        stats = {}
        if numeric_columns:
            stats = self.df[numeric_columns].describe().to_dict()
        
        # Value counts for categorical columns (limited to top values)
        categorical_columns = self.df.select_dtypes(include=['object', 'category']).columns.tolist()
        categorical_counts = {}
        for col in categorical_columns:
            categorical_counts[col] = self.df[col].value_counts().head(5).to_dict()
        
        # Store summary
        self.data_summary = {
            "num_rows": num_rows,
            "num_cols": num_cols,
            "columns": columns,
            "dtypes": dtypes,
            "null_counts": null_counts,
            "stats": stats,
            "categorical_counts": categorical_counts
        }
    
    def get_data_summary(self) -> Dict[str, Any]:
        """Return the data summary"""
        return self.data_summary
    
    def get_feature_target_split(self, target_column: str) -> Tuple[pd.DataFrame, pd.Series]:
        """Split data into features and target"""
        if self.df is None or target_column not in self.df.columns:
            raise ValueError(f"Target column '{target_column}' not found in dataframe")
        
        X = self.df.drop(columns=[target_column])
        y = self.df[target_column]
        return X, y
    
    def get_dataframe(self) -> pd.DataFrame:
        """Return the loaded dataframe"""
        return self.df
    
    def suggest_problem_type(self, target_column: str) -> str:
        """Suggest whether this is a regression or classification problem"""
        if self.df is None:
            return "unknown"
            
        if target_column not in self.df.columns:
            return "unknown"
            
        # Get the target series
        target = self.df[target_column]
        
        # Check if target is numeric
        if np.issubdtype(target.dtype, np.number):
            # If few unique values, likely classification
            if len(target.unique()) < 10:
                return "classification"
            else:
                return "regression"
        else:
            # Non-numeric targets are typically for classification
            return "classification" 