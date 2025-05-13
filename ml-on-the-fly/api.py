import os
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
import traceback
import json

from ml_service import MLService

# Load environment variables
load_dotenv()

app = FastAPI(title="ML on the Fly API", description="API for dynamic ML model generation and training")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create ML service instance
ml_service = MLService()

@app.get("/")
async def root():
    return {"message": "ML on the Fly API is running"}

@app.post("/upload-csv")
async def upload_csv(file: UploadFile = File(...)):
    """Upload and process a CSV file"""
    try:
        file_content = await file.read()
        result = ml_service.process_csv(file_content)
        
        if not result["success"]:
            return JSONResponse(status_code=400, content=result)
            
        return result
    except Exception as e:
        traceback_str = traceback.format_exc()
        return JSONResponse(
            status_code=500, 
            content={"success": False, "error": str(e), "traceback": traceback_str}
        )

@app.post("/select-target")
async def select_target(target_column: str = Form(...)):
    """Select the target column for prediction"""
    try:
        result = ml_service.select_target_column(target_column)
        
        if not result["success"]:
            return JSONResponse(status_code=400, content=result)
            
        return result
    except Exception as e:
        traceback_str = traceback.format_exc()
        return JSONResponse(
            status_code=500, 
            content={"success": False, "error": str(e), "traceback": traceback_str}
        )

@app.post("/generate-model")
async def generate_model(problem_type: Optional[str] = Form(None)):
    """Generate a model based on the dataset and problem type"""
    try:
        result = ml_service.generate_model(problem_type)
        
        if not result["success"]:
            return JSONResponse(status_code=400, content=result)
            
        return result
    except Exception as e:
        traceback_str = traceback.format_exc()
        return JSONResponse(
            status_code=500, 
            content={"success": False, "error": str(e), "traceback": traceback_str}
        )

@app.post("/train-model")
async def train_model():
    """Train the generated model"""
    try:
        result = ml_service.train_model()
        
        if not result["success"]:
            return JSONResponse(status_code=400, content=result)
            
        return result
    except Exception as e:
        traceback_str = traceback.format_exc()
        return JSONResponse(
            status_code=500, 
            content={"success": False, "error": str(e), "traceback": traceback_str}
        )

@app.get("/insights")
async def get_insights():
    """Get insights from the trained model"""
    try:
        result = ml_service.get_insights()
        
        if not result["success"]:
            return JSONResponse(status_code=400, content=result)
            
        return result
    except Exception as e:
        traceback_str = traceback.format_exc()
        return JSONResponse(
            status_code=500, 
            content={"success": False, "error": str(e), "traceback": traceback_str}
        )

@app.post("/predict")
async def predict(input_data: Dict[str, Any] = Body(...)):
    """Make predictions using the trained model"""
    try:
        result = ml_service.predict(input_data)
        
        if not result["success"]:
            return JSONResponse(status_code=400, content=result)
            
        return result
    except Exception as e:
        traceback_str = traceback.format_exc()
        return JSONResponse(
            status_code=500, 
            content={"success": False, "error": str(e), "traceback": traceback_str}
        )

@app.get("/model-code")
async def get_model_code():
    """Get the generated model code"""
    try:
        result = ml_service.get_model_code()
        
        if not result["success"]:
            return JSONResponse(status_code=400, content=result)
            
        return result
    except Exception as e:
        traceback_str = traceback.format_exc()
        return JSONResponse(
            status_code=500, 
            content={"success": False, "error": str(e), "traceback": traceback_str}
        )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run("api:app", host="0.0.0.0", port=port, reload=True) 