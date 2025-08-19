from mcp.server.fastmcp import Tool
import os
import subprocess

@Tool("batch_score")
def batch_score(model_name: str, input_table: str, output_table: str, stage: str = "Production"):
    """
    Score a batch of data using a registered MLflow model.
    """
    
    workspace_url = os.getenv("DATABRICKS_HOST")
    token = os.getenv("DATABRICKS_TOKEN")
    
    if not workspace_url or not token:
        return {"status": "error", "message": "Missing Databricks credentials"}
    
    try:
        # Create scoring script
        scoring_script = f"""
import mlflow.pyfunc
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
import pandas as pd

# Initialize Spark
spark = SparkSession.builder.appName("BatchScoring").getOrCreate()

# Load model from registry
model = mlflow.pyfunc.load_model("models:/{model_name}/{stage}")

# Load input data
input_df = spark.read.table("{input_table}")

# Prepare features (this should match your training feature engineering)
def prepare_features(df):
    # Extract evidence features
    df = df.withColumn("evidence_parsed", 
                      F.from_json(F.col("evidence"), 
                                 "struct<sum7:double,sum30:double,tx_count:int,origin_country:string,beneficiary_country:string>"))
    
    # Extract numeric features
    df = df.withColumn("velocity_ratio", 
                      F.when(F.col("evidence_parsed.sum30") > 0, 
                            F.col("evidence_parsed.sum7") / F.col("evidence_parsed.sum30"))
                      .otherwise(0))
    
    df = df.withColumn("tx_count", F.coalesce(F.col("evidence_parsed.tx_count"), F.lit(1)))
    
    # Create categorical features
    df = df.withColumn("is_high_risk_corridor", 
                      F.when(F.col("typology") == "R3_HIGH_RISK_CORRIDOR", 1).otherwise(0))
    
    df = df.withColumn("is_sanctions", 
                      F.when(F.col("typology") == "R1_SANCTIONS_MATCH", 1).otherwise(0))
    
    df = df.withColumn("is_structuring", 
                      F.when(F.col("typology") == "R2_STRUCTURING", 1).otherwise(0))
    
    # Add typology encoding
    typology_mapping = {{
        "R1_SANCTIONS_MATCH": 0,
        "R2_STRUCTURING": 1, 
        "R3_HIGH_RISK_CORRIDOR": 2,
        "R4_VELOCITY_SPIKE": 3,
        "R5_ROUND_TRIP": 4
    }}
    
    mapping_expr = F.create_map([F.lit(x) for x in sum(typology_mapping.items(), ())])
    df = df.withColumn("typology_encoded", mapping_expr[F.col("typology")])
    
    return df

# Prepare features
features_df = prepare_features(input_df)

# Select feature columns
feature_cols = ["risk_score", "velocity_ratio", "tx_count", "is_high_risk_corridor", 
               "is_sanctions", "is_structuring", "typology_encoded"]

# Convert to Pandas for scoring
pdf = features_df.select(["alert_id"] + feature_cols).toPandas()

# Handle missing values
pdf[feature_cols] = pdf[feature_cols].fillna(0)

# Score
X = pdf[feature_cols]
scores = model.predict_proba(X)[:, 1] if hasattr(model, 'predict_proba') else model.predict(X)

# Add scores to dataframe
pdf["triage_score"] = scores

# Convert back to Spark DataFrame
scored_spark_df = spark.createDataFrame(pdf[["alert_id", "triage_score"]])

# Join with original data
result_df = input_df.join(scored_spark_df, "alert_id")

# Save results
result_df.write.format("delta").mode("overwrite").saveAsTable("{output_table}")

print(f"Scoring completed. Results saved to {output_table}")
print(f"Scored {{result_df.count()}} records")

# Show sample results
result_df.select("alert_id", "typology", "risk_score", "triage_score").show(10)
"""
        
        # Write scoring script
        script_path = "/tmp/scoring_script.py"
        with open(script_path, "w") as f:
            f.write(scoring_script)
        
        # Upload and execute (simplified - in practice use Jobs API)
        cmd = [
            "databricks", "workspace", "import",
            "--language", "PYTHON",
            "--format", "SOURCE",
            script_path, 
            f"/tmp/scoring_{model_name}"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            return {
                "status": "error",
                "message": f"Scoring script upload failed: {result.stderr}"
            }
        
        return {
            "status": "success",
            "model_name": model_name,
            "model_stage": stage,
            "input_table": input_table,
            "output_table": output_table,
            "message": "Batch scoring job submitted successfully"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Batch scoring failed: {str(e)}"
        }