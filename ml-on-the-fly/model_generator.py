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
            raise 