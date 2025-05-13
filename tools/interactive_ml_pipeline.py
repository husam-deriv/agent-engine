import os
import json
import pandas as pd
from pprint import pprint
import sys
import dotenv
from openai import OpenAI

from agents import function_tool

# Load environment variables from .env file
dotenv.load_dotenv()


import os
import traceback
from typing import Dict, Any, Optional, List, Tuple
import json
import pandas as pd
import numpy as np

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
import io
import json
import os

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
            
    def load_csv_from_path(self, file_path: str) -> bool:
        """Load CSV data directly from a file path"""
        try:
            if not os.path.exists(file_path):
                print(f"Error: File not found at path: {file_path}")
                return False
                
            self.df = pd.read_csv(file_path)
            self._analyze_data()
            return True
        except Exception as e:
            print(f"Error loading CSV from path {file_path}: {str(e)}")
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
        

import os
import requests
import json
from typing import Dict, Any, Optional, List, Tuple
import importlib.util
import sys
import tempfile
import time
import ast
import re
import numpy as np

class ModelGenerator:
    def __init__(self, max_retries=3):
        """
        Initialize the ModelGenerator class
        
        Parameters:
        -----------
        max_retries : int, optional
            Maximum number of retries for model code generation. Default is 3.
            
        Note:
        -----
        This class works with the MLService class, which can now process CSV files
        directly from paths in the 'backend/user_uploaded_files/' directory.
        """
        # Set up API connection details
        self.api_base_url = "https://litellm.deriv.ai/v1"
        self.api_key = os.environ.get("LITELLM_API_KEY")
        self.model_name = "claude-3-7-sonnet-latest"
        
        # Set up Gemini fallback
        self.google_api_key = os.environ.get("GOOGLE_API_KEY")
        self.gemini_model = "gemini-1.5-pro"
        self.gemini_api_url = "https://generativelanguage.googleapis.com/v1beta/models"
        
        # Track which model generated the code
        self.last_used_model = None
        self.max_retries = max_retries
        
        # Required methods for DynamicModel
        self.required_methods = [
            "__init__", 
            "fit_preprocessing", 
            "preprocess_data", 
            "train", 
            "predict", 
            "evaluate", 
            "get_feature_importance"
        ]
        
        if not self.api_key:
            raise ValueError("LITELLM_API_KEY environment variable is not set")
            
    def _call_llm(self, prompt: str, model_name: str, api_url: str, is_gemini: bool) -> str:
        """Helper function to call either Claude or Gemini LLM."""
        headers = {"Authorization": f"Bearer {self.api_key}" if not is_gemini else None, 
                   "Content-Type": "application/json"}
        
        if is_gemini:
            if not self.google_api_key:
                raise ValueError("GOOGLE_API_KEY environment variable not set for Gemini fallback.")
            api_url_with_key = f"{api_url}/{self.gemini_model}:generateContent?key={self.google_api_key}"
            payload = {
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.1, "topP": 0.8, "topK": 40}
            }
        else:
            api_url_with_key = f"{api_url}/chat/completions"
            payload = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": "You are an expert ML engineer. Your primary goal is to write syntactically correct, complete, and robust Python code for a 'DynamicModel' class. This class MUST include ALL specified methods. Pay EXTREME attention to f-string syntax and ensure all try-except blocks are complete."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1
            }

        print(f"Calling LLM ({model_name})...")
        response = requests.post(api_url_with_key, headers=headers, json=payload)
        
        if response.status_code != 200:
            raise Exception(f"API request to {model_name} failed with status code {response.status_code}: {response.text}")
            
        response_data = response.json()
        
        if is_gemini:
            model_code = response_data["candidates"][0]["content"]["parts"][0]["text"]
        else:
            model_code = response_data["choices"][0]["message"]["content"]
            
        # Extract code block
        if "```python" in model_code:
            model_code = model_code.split("```python")[1].split("```")[0].strip()
        elif "```" in model_code: # Fallback for cases where ```python is missing
            model_code = model_code.split("```")[1].split("```")[0].strip()
            
        return model_code

    def _attempt_code_generation_and_validation(self, prompt: str, is_refinement: bool = False, original_code_for_refinement: str = "", error_for_refinement: str = "") -> Tuple[str, str]:
        """Attempts to generate/refine and validate code, with retries."""
        for attempt in range(self.max_retries):
            print(f"Code generation/refinement attempt {attempt + 1}/{self.max_retries}")
            current_model_name = self.model_name
            api_url_to_use = self.api_base_url
            use_gemini_fallback = False

            try:
                if is_refinement:
                    current_prompt = self._create_refinement_prompt(original_code_for_refinement, error_for_refinement)
                else:
                    current_prompt = prompt
                
                generated_code = self._call_llm(current_prompt, current_model_name, api_url_to_use, is_gemini=False)
                
                # Validate (syntax and methods)
                validation_error = self._validate_code_structure(generated_code)
                if not validation_error:
                    print(f"Code from {current_model_name} passed structural validation.")
                    self.last_used_model = current_model_name
                    return generated_code, current_model_name 
                else:
                    print(f"Structural validation failed for {current_model_name} code: {validation_error}")
                    if not is_refinement: # If initial generation fails, allow refinement in next loop iteration
                        original_code_for_refinement = generated_code
                        error_for_refinement = validation_error
                        is_refinement = True # Next attempt will be a refinement
                        continue # Go to next attempt which will now be a refinement call
                    # If refinement itself fails validation, it will be caught and retried

            except Exception as e_claude:
                print(f"Error with {current_model_name}: {str(e_claude)}")
                use_gemini_fallback = True

            if use_gemini_fallback:
                try:
                    print("Trying Gemini fallback...")
                    current_model_name = self.gemini_model
                    if is_refinement: # If claude refinement failed, gemini also refines
                         current_prompt = self._create_refinement_prompt(original_code_for_refinement, error_for_refinement) # Use original code for gemini refine
                    else: # Gemini does initial generation if claude failed initial
                        current_prompt = prompt

                    generated_code = self._call_llm(current_prompt, current_model_name, self.gemini_api_url, is_gemini=True)
                    
                    validation_error = self._validate_code_structure(generated_code)
                    if not validation_error:
                        print(f"Code from {current_model_name} (fallback) passed structural validation.")
                        self.last_used_model = current_model_name
                        return generated_code, current_model_name
                    else:
                        print(f"Structural validation failed for {current_model_name} (fallback) code: {validation_error}")
                        if not is_refinement:
                            original_code_for_refinement = generated_code
                            error_for_refinement = validation_error
                            is_refinement = True
                            continue
                        # If gemini refinement itself fails validation

                except Exception as e_gemini:
                    print(f"Error with Gemini fallback: {str(e_gemini)}")
            
            print(f"Attempt {attempt + 1} failed. Retrying if possible...")
            time.sleep(2) # Wait a bit before retrying

        raise Exception(f"Failed to generate valid code after {self.max_retries} attempts.")

    def generate_model_code(self, data_summary: Dict[str, Any], target_column: str, problem_type: str) -> Tuple[str, str]:
        start_time = time.time()
        generation_prompt = self._create_model_generation_prompt(data_summary, target_column, problem_type)
        
        model_code, model_source = self._attempt_code_generation_and_validation(generation_prompt)
        
        generation_time = time.time() - start_time
        print(f"Code generated and validated successfully using {model_source} in {generation_time:.2f} seconds")
        return model_code, model_source

    def refine_model_code(self, model_code: str, error_message: str) -> Tuple[str, str]:
        """Refines model code using the attempt_code_generation_and_validation flow."""
        print(f"Attempting to refine code due to error: {error_message}")
        # The _attempt_code_generation_and_validation handles LLM calls and retries
        refined_code, model_source = self._attempt_code_generation_and_validation(
            prompt="", # Not used when is_refinement is True
            is_refinement=True,
            original_code_for_refinement=model_code,
            error_for_refinement=error_message
        )
        print(f"Code refined and validated successfully using {model_source}")
        return refined_code, model_source

    def _validate_code_structure(self, code: str) -> Optional[str]:
        """
        Validates code for syntax errors and required DynamicModel structure.
        Returns None if valid, or an error message string if invalid.
        """
        # 1. Syntax Check
        try:
            parsed_ast = ast.parse(code)
        except SyntaxError as e:
            return f"Syntax error: {e.msg} at line {e.lineno}, offset {e.offset}. Problematic text: '{e.text.strip()}'"

        # 2. DynamicModel Class and Method Check
        found_class = False
        present_methods = set()
        for node in ast.walk(parsed_ast):
            if isinstance(node, ast.ClassDef) and node.name == "DynamicModel":
                found_class = True
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        present_methods.add(item.name)
                break 
        
        if not found_class:
            return "DynamicModel class definition not found."

        missing_methods = set(self.required_methods) - present_methods
        if missing_methods:
            return f"DynamicModel class is missing required methods: {', '.join(sorted(list(missing_methods)))}"
        
        return None # All checks passed

    def _final_code_verification(self, code: str) -> bool:
        """
        Perform a final verification on the code structure (already known to be syntactically valid).
        Returns True if code passes all checks, False otherwise.
        This is more of a sanity check for issues ast.parse might not catch contextually.
        """
        # Re-check structure, though _validate_code_structure should have caught this.
        # This acts as a redundant check before exec.
        structural_error = self._validate_code_structure(code)
        if structural_error:
            print(f"ERROR (final_code_verification): Structural error found: {structural_error}")
            return False

        # Temporarily disabling the aggressive f-string and unsafe indexing checks
        # as they were causing too many false positives. The main ast.parse()
        # should catch true syntax errors including malformed f-strings.
        # We can add more nuanced checks here later if specific patterns of
        # runtime errors (not syntax errors) emerge.

        # Example of a more nuanced check (can be expanded later):
        # if "some_problematic_pattern" in code:
        #     print("ERROR (final_code_verification): Detected problematic pattern.")
        #     return False
            
        return True
            
    def _create_model_generation_prompt(self, data_summary: Dict[str, Any], target_column: str, problem_type: str) -> str:
        columns_info = []
        for col in data_summary["columns"]:
            dtype = data_summary["dtypes"].get(col, "unknown")
            null_count = data_summary["null_counts"].get(col, 0)
            
            if col == target_column:
                columns_info.append(f"- {col}: TARGET COLUMN, dtype={dtype}, nulls={null_count}")
                continue

            examples_str = ""
            col_type_desc = ""
            if dtype == 'object' or dtype == 'bool': # Heuristic for categorical or date
                if 'date' in col.lower() or 'time' in col.lower() or (data_summary.get("categorical_counts", {}).get(col) and any(re.match(r'\d{4}-\d{2}-\d{2}', str(k)) for k in data_summary["categorical_counts"][col].keys())):
                    col_type_desc = "date-like (handle by extracting year, month, day, etc.)"
                else:
                    cat_values = list(data_summary.get("categorical_counts", {}).get(col, {}).keys())
                    unique_count = len(cat_values)
                    examples_str = f", examples: {cat_values[:3]}"
                    col_type_desc = f"categorical, unique_values={unique_count}"
            elif np.issubdtype(np.dtype(dtype), np.number):
                stats = data_summary.get("stats", {}).get(col, {})
                min_val = stats.get('min', 'N/A')
                max_val = stats.get('max', 'N/A')
                mean_val = stats.get('mean', 'N/A')
                if isinstance(mean_val, float): mean_val = round(mean_val, 2)
                col_type_desc = f"numerical, min={min_val}, max={max_val}, mean={mean_val}"
            else:
                col_type_desc = f"other (dtype: {dtype}, consider dropping or special handling)"
            
            columns_info.append(f"- {col}: type_hint='{col_type_desc}', original_dtype={dtype}, nulls={null_count}{examples_str}")
        
        columns_description = "\n".join(columns_info)
        
        example_fstring_literal = "my_dict[f'prefix_{{a_variable_name}}'] = value" # Double braces for literal

        prompt = f"""
You are an expert ML engineer. Generate a CLEAN, ROBUST, and CORRECT Python class `DynamicModel`.

Dataset Summary:
- Target Column: '{target_column}' (Problem Type: {problem_type})

Available Features (Analyze 'type_hint' and examples to decide handling):
{columns_description}

MANDATORY REQUIREMENTS & WORKFLOW FOR `DynamicModel` CLASS:

1.  **Libraries**: `pandas` as pd, `numpy` as np. From `sklearn`:
    *   `compose.ColumnTransformer`
    *   `preprocessing.StandardScaler`, `preprocessing.OneHotEncoder`
    *   Model (e.g., `ensemble.RandomForestRegressor` or `linear_model.LogisticRegression`)
    *   Metrics (e.g., `mean_squared_error`, `r2_score`, `accuracy_score`, `f1_score`)

2.  **`__init__(self)`**:
    *   `self.model`: Initialize a scikit-learn model for "{problem_type}" (e.g., `RandomForestRegressor(random_state=42)`).
    *   `self.preprocessor: ColumnTransformer = None`.
    *   `self.identified_date_features: list = []` (original names of date-like columns).
    *   `self.engineered_date_feature_names: list = []` (names of NEW year, month, day etc. columns).
    *   `self.numerical_features: list = []` (original numerical cols + engineered date cols if numerical).
    *   `self.categorical_features: list = []` (original categorical cols).
    *   `self.training_columns_: list = None` (Order of columns in `X` DataFrame seen by `fit_preprocessing` BEFORE any processing within that method).
    *   `self.feature_names_out_: list = None` (Final feature names AFTER all preprocessing, from `ColumnTransformer`).
    *   **DO NOT FIT ANYTHING HERE.**

3.  **`_data_type_identifier(self, X: pd.DataFrame)` (Private helper, called by `fit_preprocessing`)**:
    *   Clears and populates `self.identified_date_features`, `self.numerical_features` (non-date numerics), `self.categorical_features` by iterating `X.columns` and `X.dtypes`.
    *   For date-like columns (e.g., names with 'date', 'time', or object dtype with date-like string values), add to `self.identified_date_features`.
    *   For other numerical types (int, float), add to `self.numerical_features`.
    *   For object, bool, or category dtypes not identified as dates, add to `self.categorical_features`.

4.  **`_engineer_date_features(self, X_df: pd.DataFrame, fit_mode: bool) -> pd.DataFrame` (Private helper)**:
    *   `df = X_df.copy()`.
    *   If `fit_mode` is True, clear `self.engineered_date_feature_names`.
    *   For each `col_name` in `self.identified_date_features`:
        *   `df[col_name] = pd.to_datetime(df[col_name], errors='coerce')`.
        *   Create new columns: `year_col = f'{{col_name}}_year'`, `month_col = f'{{col_name}}_month'`, etc. (LLM: Note the double curly braces `{{col_name}}` to make `col_name` a literal for your generated f-string template).
        *   `df[year_col] = df[col_name].dt.year` (similarly for month, day, dayofweek, dayofyear).
        *   **IMPORTANT for NaNs in new date parts**: Fill NaNs using direct assignment, e.g., `df[year_col] = df[year_col].fillna(0)`. **DO NOT use `inplace=True` for these `fillna` operations.**
        *   If `fit_mode` is True, add these new names (e.g., `year_col`) to `self.engineered_date_feature_names`.
    *   `df.drop(columns=self.identified_date_features, inplace=True, errors='ignore')` (Drop original date string columns).
    *   Return `df`.

5.  **`fit_preprocessing(self, X: pd.DataFrame)`**:
    *   `self.training_columns_ = X.columns.tolist()`.
    *   Call `self._data_type_identifier(X)`.
    *   `X_dates_engineered = self._engineer_date_features(X, fit_mode=True)`.
    *   Now, update `self.numerical_features` to include `self.engineered_date_feature_names` (as these are now numerical).
       (Ensure no overlap with `self.categorical_features` if some date parts were made categorical - for now, assume date parts are numerical).
    *   `transformers_list = []`.
    *   If `self.numerical_features` (original numerics + engineered date parts): `transformers_list.append(('num_scaler', StandardScaler(), self.numerical_features))`
    *   If `self.categorical_features`: `transformers_list.append(('cat_encoder', OneHotEncoder(handle_unknown='ignore', sparse_output=False), self.categorical_features))`
    *   `self.preprocessor = ColumnTransformer(transformers=transformers_list, remainder='drop')`.
    *   Fit `self.preprocessor` on `X_dates_engineered` (which only contains numerical and categorical columns for the ColumnTransformer).
    *   Store final feature names: `self.feature_names_out_ = self.preprocessor.get_feature_names_out()`.

6.  **`preprocess_data(self, X: pd.DataFrame) -> pd.DataFrame`**:
    *   `X_aligned = X.copy()`
    *   `X_aligned = X_aligned.reindex(columns=self.training_columns_, fill_value=np.nan)` (Align to original training columns).
    *   `X_dates_engineered = self._engineer_date_features(X_aligned, fit_mode=False)`.
    *   `X_transformed_array = self.preprocessor.transform(X_dates_engineered)`.
    *   Return `pd.DataFrame(X_transformed_array, columns=self.feature_names_out_, index=X_dates_engineered.index)`.
    *   **CRITICAL**: This method must NOT re-fit `self.preprocessor` or change feature identification lists.

7.  **`train(self, X_processed: pd.DataFrame, y: pd.Series)`**: Train `self.model` on `X_processed`, `y`.
8.  **`predict(self, X_processed: pd.DataFrame) -> np.ndarray`**: Return `self.model.predict(X_processed)`.
9.  **`evaluate(self, X_processed: pd.DataFrame, y: pd.Series) -> dict`**: Calculate and return metrics dict.
10. **`get_feature_importance(self) -> dict`**: Use `self.feature_names_out_` for keys. Return dict.

11. **Code Quality**: Clean, simple, docstrings, basic try-except. Correct f-string syntax (example for dict key: `{example_fstring_literal}`). Complete `try-except` blocks.

Return ONLY the complete Python code for `DynamicModel` class.
"""

        if "**`evaluate(self, X_processed: pd.DataFrame, y: pd.Series) -> dict`**: Calculate and return metrics dict." in prompt:
            # Replace with more detailed instructions for the evaluate method
            prompt = prompt.replace(
                "9.  **`evaluate(self, X_processed: pd.DataFrame, y: pd.Series) -> dict`**: Calculate and return metrics dict.",
                """9.  **`evaluate(self, X_processed: pd.DataFrame, y: pd.Series) -> dict`**:
    *   Use proper sklearn metrics to calculate actual performance (NOT HARDCODED VALUES).
    *   For classification: Use `sklearn.metrics.accuracy_score`, `f1_score`, `precision_score`, `recall_score` with actual predictions:
        ```python
        from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
        y_pred = self.model.predict(X_processed)  # Get ACTUAL predictions
        metrics = {
            'accuracy': accuracy_score(y, y_pred),
            'f1_score': f1_score(y, y_pred, average='weighted'),
            'precision': precision_score(y, y_pred, average='weighted'),
            'recall': recall_score(y, y_pred, average='weighted')
        }
        ```
    *   For regression: Use `sklearn.metrics.mean_squared_error`, `r2_score`:
        ```python
        from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
        y_pred = self.model.predict(X_processed)  # Get ACTUAL predictions
        metrics = {
            'mse': mean_squared_error(y, y_pred),
            'rmse': np.sqrt(mean_squared_error(y, y_pred)),
            'mae': mean_absolute_error(y, y_pred),
            'r2': r2_score(y, y_pred)
        }
        ```
    *   IMPORTANT: DO NOT return hardcoded values of 1.0 or any other constants.""")
        
        return prompt

    def _create_refinement_prompt(self, model_code: str, error_message: str) -> str:
        example_fstring_literal = "my_dict[f'prefix_{{a_variable_name}}'] = value" # Double braces for literal
        return f"""
The Python code for `DynamicModel` has an error or is incomplete.
ERROR: "{error_message}"

Original Flawed Code:
```python
{model_code}
```

CRITICAL INSTRUCTIONS FOR FIXING:
1.  **FIX THE ERROR**: Directly address the ERROR message.
2.  **RE-CHECK ALL REQUIREMENTS**: Review the original prompt's "MANDATORY REQUIREMENTS & WORKFLOW" section (points 1-11). Pay strict attention to:
    *   **Date Feature Engineering**: `_engineer_date_features` must create NEW columns (e.g., `f'{{col_name}}_year'` where `col_name` is the original date column name). Fill NaNs in new date part columns using direct assignment (e.g., `df[date_part_col] = df[date_part_col].fillna(0)`), **NOT** with `inplace=True`. `fit_preprocessing` must call `_engineer_date_features` with `fit_mode=True`, and `preprocess_data` with `fit_mode=False`. The `ColumnTransformer` should be defined AFTER date features are engineered.
    *   **Feature Lists**: `self.numerical_features` should include original numerics AND newly engineered numerical date parts.
    *   **Feature Names**: `self.feature_names_out_` MUST be set in `fit_preprocessing` from `self.preprocessor.get_feature_names_out()`.
    *   **Column Alignment in `preprocess_data`**: Must reindex to `self.training_columns_` BEFORE date engineering.
    *   **No Re-fitting**: `preprocess_data` MUST NOT re-fit.
3.  **SYNTAX & COMPLETENESS**: Correct all syntax. ALL f-strings (e.g., for dict keys: `{example_fstring_literal}`, for new column names `f'prefix_{{some_variable}}'`). Complete `try-except`. All methods MUST be present.

Return ONLY the fully corrected, complete Python code for `DynamicModel`.
"""
        
    def instantiate_model(self, model_code: str) -> Any:
        """Dynamically instantiate a model class from generated code"""
        try:
            # Final structural and content verification of code before instantiation
            if not self._final_code_verification(model_code):
                # If final verification fails, attempt one last refinement
                print("Final code verification failed. Attempting one last refinement...")
                model_code, _ = self.refine_model_code(model_code, "Final code verification check failed. Review all method implementations and syntax.")
                
                # Re-verify after the last refinement attempt
                if not self._final_code_verification(model_code):
                    raise ValueError("Generated code failed final verification checks even after targeted refinement.")

            # Create a temporary module
            spec = importlib.util.spec_from_loader("dynamic_model", loader=None)
            module = importlib.util.module_from_spec(spec)
            
            # Execute the model code in the module's context
            exec(model_code, module.__dict__)
            
            # Get the model class from the module
            if hasattr(module, "DynamicModel"):
                model_instance = module.DynamicModel()
                
                # Verify all required methods exist in the instantiated object
                for method_name in self.required_methods:
                    if not hasattr(model_instance, method_name) or not callable(getattr(model_instance, method_name)):
                        raise ValueError(f"Instantiated model is missing required method or it's not callable: {method_name}")
                
                return model_instance
            else:
                raise ValueError("Generated code does not contain a DynamicModel class after execution.")
                
        except Exception as e:
            print(f"Critical error during model instantiation: {str(e)}")
            print("--- Problematic Code ---")
            # Print code with line numbers for easier debugging
            for i, line in enumerate(model_code.split('\n'), 1):
                print(f"{i:03d}: {line}")
            print("------------------------")
            raise e

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
            
    def process_csv_from_path(self, file_path: str) -> Dict[str, Any]:
        """Process a CSV file from a file path and return data summary"""
        try:
            if not os.path.exists(file_path):
                return {"success": False, "error": f"File not found at path: {file_path}"}
                
            success = self.csv_handler.load_csv_from_path(file_path)
            if not success:
                return {"success": False, "error": f"Failed to load CSV file from path: {file_path}"}
                
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
                
                # Verify metrics aren't all suspiciously perfect
                all_perfect = all(value == 1.0 for value in metrics.values() if isinstance(value, (int, float)))
                if all_perfect and len(metrics) > 0:
                    print("WARNING: All metrics are exactly 1.0, which is suspicious for real-world data.")
                    print("Recalculating metrics to verify...")
                    
                    # Manually recalculate metrics as a sanity check
                    try:
                        # Get predictions directly
                        y_pred = self.dynamic_model.predict(X_processed)
                        
                        if self.problem_type == "classification":
                            # For classification problems
                            from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
                            verified_metrics = {
                                'accuracy': accuracy_score(y, y_pred),
                                'f1_score': f1_score(y, y_pred, average='weighted'),
                                'precision': precision_score(y, y_pred, average='weighted'),
                                'recall': recall_score(y, y_pred, average='weighted')
                            }
                        else:
                            # For regression problems
                            from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
                            verified_metrics = {
                                'mse': mean_squared_error(y, y_pred),
                                'rmse': np.sqrt(mean_squared_error(y, y_pred)),
                                'mae': mean_absolute_error(y, y_pred),
                                'r2': r2_score(y, y_pred)
                            }
                        
                        print(f"Verified metrics: {verified_metrics}")
                        
                        # Update metrics if they were suspiciously perfect
                        if all_perfect:
                            metrics = verified_metrics
                            print("Using verified metrics instead of suspicious perfect scores.")
                    except Exception as verify_error:
                        print(f"Warning: Could not verify metrics independently: {str(verify_error)}")
                
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



def display_dict(data: dict, indent=1):
    for key, value in data.items():
        print('\t' * indent + str(key) + ':', end='')
        if isinstance(value, dict):
            print()
            display_dict(value, indent + 1)
        else:
            print('\t' * (indent + 1) + str(value))

def analyze_query_compatibility(csv_path, user_query, data_summary):
    """
    Analyze if the user query is compatible with the CSV data using OpenAI.
    
    Parameters:
    -----------
    csv_path : str
        Path to the CSV file
    user_query : str
        User's natural language query about the data
    data_summary : dict
        Summary of the CSV data
        
    Returns:
    --------
    dict
        Compatibility result with required fields
    """
    try:
        # Initialize OpenAI client
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Create prompt for analyzing compatibility
        prompt = f"""
You are an AI assistant that helps determine if a user's query about a CSV dataset can be answered using machine learning.

CSV Data Summary:
- Rows: {data_summary['num_rows']}
- Columns: {data_summary['num_cols']}

Available columns:
{json.dumps(data_summary['columns'], indent=2)}

Column data types:
{json.dumps(data_summary['dtypes'], indent=2)}

If categorical columns are present, here are some example values:
{json.dumps(data_summary.get('categorical_counts', {}), indent=2)}

User Query:
"{user_query}"

INSTRUCTIONS:
1. Determine if the user is asking to predict a specific column value based on other columns.
2. Identify which column the user wants to predict (target column).
3. Identify which column values the user has provided for making the prediction.

RESPOND WITH VALID JSON ONLY in this format:
If compatible:
{{
  "compatible": 1,
  "target_column": "column_name_from_csv_which_user_wants_to_predict_value_of",
  "model_input_values": {{column_name1: value1, column_name2: value2, ...}}
}}

If not compatible or if insufficient information:
{{
  "compatible": 0,
  "reason": "Explain what more column values are needed to predict target or any clarifications"
}}
"""
        
        # Call OpenAI API
        print("Calling OpenAI API to analyze query compatibility...")
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are an AI assistant that helps analyze data queries and determine if they can be answered using machine learning. Respond with valid JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        # Extract response
        analysis = completion.choices[0].message.content
        
        try:
            # Remove any extra text and only keep JSON
            json_str = analysis
            if "```json" in analysis:
                json_str = analysis.split("```json")[1].split("```")[0].strip()
            elif "```" in analysis:
                json_str = analysis.split("```")[1].split("```")[0].strip()
            
            compatibility_result = json.loads(json_str)
            
            # Ensure the response has the required fields
            if "compatible" not in compatibility_result:
                return {"compatible": 0, "reason": "Invalid LLM response format. Missing 'compatible' field."}
                
            if compatibility_result["compatible"] == 1:
                if "target_column" not in compatibility_result or "model_input_values" not in compatibility_result:
                    return {"compatible": 0, "reason": "Invalid LLM response format. Missing required fields for compatible=1."}
            elif "reason" not in compatibility_result:
                compatibility_result["reason"] = "Insufficient information provided to make a prediction."
                
            return compatibility_result
            
        except json.JSONDecodeError:
            print("Error: LLM did not return valid JSON")
            print("Raw LLM response:", analysis)
            return {"compatible": 0, "reason": "Failed to parse LLM response as JSON."}
            
    except Exception as e:
        print(f"Error in query compatibility analysis: {str(e)}")
        return {"compatible": 0, "reason": f"Error analyzing query compatibility: {str(e)}"}

@function_tool
def run_interactive_pipeline(
    csv_filename: str = None,
    user_query: str = None
):
    """Process CSV data files to dynamically build, train, and execute machine learning models based on natural language queries, allowing an AI Agent to perform predictive analytics on tabular data without requiring the user to have ML expertise or write code; Args: csv_filename (str): name of the CSV file in the backend/rag_files directory, user_query (str): natural language query describing the prediction to make; Returns: str: JSON string with prediction results or compatibility information."""
    print("===== ML-on-the-Fly: Automated Pipeline =====")
    ml_service = MLService()
    result_data = {"success": True}
    print("Here1")
    # 1. Validate inputs and prepare CSV path
    if csv_filename is None:
        return {"success": False, "error": "No CSV filename provided"}
    
    # Get the current working directory
    cwd = os.getcwd()
    # Check if we're already in the backend directory
    if cwd.endswith('/backend'):
        csv_path = f"user_uploaded_files/{csv_filename}"
    else:
        csv_path = f"backend/user_uploaded_files/{csv_filename}"
    
    print(f"Checking file path: {csv_path}")
    print(f"File exists: {os.path.exists(csv_path)}")
    print(f"Current working directory: {cwd}")
    
    if not os.path.exists(csv_path):
        return {"success": False, "error": f"File not found at '{csv_path}'"}
    
    if not csv_path.lower().endswith('.csv'):
        return {"success": False, "error": f"File does not appear to be a CSV file (expected .csv extension)"}
    
    print("Here2")
    
    # 2. Process CSV using the new path-based method
    print(f"Using file: {csv_path}")
    print("\nProcessing CSV file...")
    result = ml_service.process_csv_from_path(csv_path)
    
    if not result.get("success"):
        print(f"Error processing CSV: {result.get('error', 'Unknown error')}")
        if result.get('traceback'):
            print("Traceback:")
            print(result['traceback'])
        return result
    
    print("CSV processed successfully!")
    data_summary = result["data_summary"]
    result_data["data_summary"] = data_summary
    
    # 3. If user query is provided, analyze compatibility
    if user_query:
        print("\nAnalyzing user query compatibility...")
        compatibility = analyze_query_compatibility(csv_path, user_query, data_summary)
        
        # IMPORTANT: If not compatible, immediately return the compatibility result and end the pipeline
        if compatibility.get("compatible") != 1:
            print(f"Query is not compatible with CSV: {compatibility.get('reason', 'Unknown reason')}")
            # Return only the compatibility information
            return compatibility
            
        # Only proceed if compatible
        target_column = compatibility.get("target_column")
        prediction_data = compatibility.get("model_input_values", {})
        make_prediction = True
        
        print(f"Query is compatible with CSV. Target column: {target_column}")
        print(f"Input values: {json.dumps(prediction_data, indent=2)}")
    else:
        return {"compatible": 0, "reason": "No user query provided"}
    
    # 4. Select target column (from query analysis)
    target_column_result = None
    if target_column and target_column in data_summary['columns']:
        print(f"Using '{target_column}' as the target column.")
        target_column_result = ml_service.select_target_column(target_column)
    else:
        return {"compatible": 0, "reason": f"Target column '{target_column}' could not be determined or is not in the dataset"}
    
    if not target_column_result or not target_column_result.get("success"):
        error_msg = target_column_result.get("error", "Error selecting target column")
        print(f"Error selecting target column: {error_msg}")
        return {"compatible": 0, "reason": error_msg}
    
    problem_type = target_column_result['problem_type']
    result_data["problem_type"] = problem_type
    print(f"Target column '{target_column}' selected. Detected problem type: {problem_type}")

    # 5. Generate Model
    print("\nGenerating model...")
    gen_result = ml_service.generate_model()
    if not gen_result.get("success"):
        print(f"Error generating model: {gen_result.get('error', 'Unknown error')}")
        if gen_result.get('traceback'):
            print("Traceback:")
            print(gen_result['traceback'])
        return {"compatible": 0, "reason": f"Failed to generate model: {gen_result.get('error', 'Unknown error')}"}
    
    result_data["model_generation"] = gen_result
    print(gen_result.get("message", "Model generated."))
    if gen_result.get("model_source"):
        print(f"Model code was generated by: {gen_result['model_source']}")

    # 6. Train Model
    print("\nTraining model...")
    train_result = ml_service.train_model()
    if not train_result.get("success"):
        print(f"Error training model: {train_result.get('error', 'Unknown error')}")
        if train_result.get('traceback'):
            print("Traceback:")
            print(train_result['traceback'])
        return {"compatible": 0, "reason": f"Failed to train model: {train_result.get('error', 'Unknown error')}"}
    
    result_data["training_result"] = train_result
    print(train_result.get("message", "Model trained."))
    print("\nTraining Summary:")
    if 'metrics' in train_result.get("training_summary", {}):
        print("Metrics:")
        for metric_name, metric_value in train_result["training_summary"]["metrics"].items():
            if isinstance(metric_value, float):
                print(f"  {metric_name}: {metric_value:.6f}")
            else:
                print(f"  {metric_name}: {metric_value}")

    # 7. Make prediction with provided data
    print("\nMaking prediction with input data...")
    predict_result = ml_service.predict(prediction_data)
    result_data["prediction"] = predict_result
    
    if predict_result.get("success"):
        print("\nPrediction Result:")
        print(f"  Predicted value for '{target_column}': {predict_result['prediction']}")
        
        # Return simplified result with compatible=1 to indicate success
        return str({
            "compatible": 1,
            "target_column": target_column,
            "model_input_values": prediction_data,
            "prediction": predict_result['prediction'],
            "problem_type": problem_type
        })
    else:
        print(f"Error making prediction: {predict_result.get('error', 'Unknown error')}")
        if predict_result.get('traceback'):
            print("Traceback:")
            print(predict_result['traceback'])
        return str({"compatible": 0, "reason": f"Failed to make prediction: {predict_result.get('error', 'Unknown error')}"})

# if __name__ == "__main__":
#     # Example usage: python interactive_ml_pipeline.py csv_filename "user query about prediction"
#     # if len(sys.argv) > 2:
#     #     csv_filename = sys.argv[1]
#     #     user_query = sys.argv[2]
#     #     result = run_interactive_pipeline(csv_filename=csv_filename, user_query=user_query)
#     #     print(json.dumps(result, indent=2))
#     # else:
#     #     print("Usage: python interactive_ml_pipeline.py <csv_filename> \"<user_query>\"")

#     run_interactive_pipeline("iris_train.csv", "What is the sepal length for sepal width (cm),3.6 and petal length (cm),1.0 and petal width (cm),0.2 and species,setosa")