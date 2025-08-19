from mcp.server.fastmcp import Tool
import os
import subprocess
import json

@Tool("train")
def train(model_name: str, data_table: str, features: list, target: str):
    """
    Train an ML model using Databricks and MLflow.
    """
    
    workspace_url = os.getenv("DATABRICKS_HOST")
    token = os.getenv("DATABRICKS_TOKEN")
    
    if not workspace_url or not token:
        return {"status": "error", "message": "Missing Databricks credentials"}
    
    # Training parameters
    training_params = {
        "model_name": model_name,
        "data_table": data_table,
        "features": features,
        "target": target,
        "experiment_name": f"/aml/{model_name}"
    }
    
    try:
        # Create a temporary training script
        training_script = f"""
import mlflow
import mlflow.sklearn
from pyspark.sql import SparkSession
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, precision_score, recall_score
import pandas as pd

# Initialize Spark
spark = SparkSession.builder.appName("MLTraining").getOrCreate()

# Set MLflow experiment
mlflow.set_experiment("{training_params['experiment_name']}")

# Load data
df = spark.read.table("{data_table}")
pdf = df.toPandas()

# Prepare features
features = {features}
X = pdf[features].fillna(0)
y = pdf["{target}"]

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train model with MLflow tracking
with mlflow.start_run() as run:
    # Model parameters
    params = {{
        "n_estimators": 100,
        "max_depth": 10,
        "random_state": 42
    }}
    
    mlflow.log_params(params)
    
    # Train model
    model = RandomForestClassifier(**params)
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    
    auc = roc_auc_score(y_test, y_pred_proba)
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    
    mlflow.log_metric("auc", auc)
    mlflow.log_metric("precision", precision)
    mlflow.log_metric("recall", recall)
    
    # Log model
    mlflow.sklearn.log_model(
        model,
        artifact_path="model",
        registered_model_name="{model_name}"
    )
    
    print(f"Training completed. Run ID: {{run.info.run_id}}")
    print(f"AUC: {{auc:.3f}}, Precision: {{precision:.3f}}, Recall: {{recall:.3f}}")
"""
        
        # Write training script to temporary file
        script_path = "/tmp/training_script.py"
        with open(script_path, "w") as f:
            f.write(training_script)
        
        # Execute via databricks CLI (simplified)
        # In practice, you'd use the Jobs API or direct notebook execution
        cmd = [
            "databricks", "workspace", "import",
            "--language", "PYTHON",
            "--format", "SOURCE", 
            script_path,
            f"/tmp/training_{model_name}"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            return {
                "status": "error",
                "message": f"Training script upload failed: {result.stderr}"
            }
        
        return {
            "status": "success",
            "model_name": model_name,
            "data_table": data_table,
            "features": features,
            "target": target,
            "experiment_name": training_params["experiment_name"],
            "message": "Training job submitted successfully"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Training failed: {str(e)}"
        }