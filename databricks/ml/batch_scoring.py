from mlflow.tracking import MlflowClient
import mlflow.pyfunc
from pyspark.sql import functions as F
import pandas as pd

MODEL_NAME = "aml_alert_triage"
MODEL_STAGE = "Production"  # or "Staging" for testing

def load_model():
    """Load the latest model from MLflow Registry"""
    client = MlflowClient()
    
    # Get latest version in Production stage
    try:
        latest_version = client.get_latest_versions(MODEL_NAME, stages=[MODEL_STAGE])[0]
        model = mlflow.pyfunc.load_model(f"models:/{MODEL_NAME}/{latest_version.version}")
        print(f"Loaded model {MODEL_NAME} version {latest_version.version}")
        return model
    except Exception as e:
        print(f"Error loading model: {e}")
        return None

def prepare_features(df):
    """Prepare features for scoring - must match training feature engineering"""
    
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
    
    # Add typology encoding (simplified - in production, save the encoder)
    typology_mapping = {
        "R1_SANCTIONS_MATCH": 0,
        "R2_STRUCTURING": 1, 
        "R3_HIGH_RISK_CORRIDOR": 2,
        "R4_VELOCITY_SPIKE": 3,
        "R5_ROUND_TRIP": 4
    }
    
    mapping_expr = F.create_map([F.lit(x) for x in sum(typology_mapping.items(), ())])
    df = df.withColumn("typology_encoded", mapping_expr[F.col("typology")])
    
    return df

def score_alerts():
    """Score new alerts and save results"""
    
    model = load_model()
    if model is None:
        print("Failed to load model, exiting")
        return
    
    # Read new alerts (last 24 hours or alerts not yet scored)
    alerts_to_score = (spark.read.table("aml.gold.alerts")
                      .filter(F.col("created_ts") >= F.current_date() - 1))
    
    # Check if we have any alerts to score
    alert_count = alerts_to_score.count()
    if alert_count == 0:
        print("No new alerts to score")
        return
    
    print(f"Scoring {alert_count} alerts...")
    
    # Prepare features
    alerts_features = prepare_features(alerts_to_score)
    
    # Select feature columns (must match training)
    feature_cols = ["risk_score", "velocity_ratio", "tx_count", "is_high_risk_corridor", 
                   "is_sanctions", "is_structuring", "typology_encoded"]
    
    # Convert to Pandas for scoring
    pdf_features = alerts_features.select(["alert_id"] + feature_cols).toPandas()
    
    # Handle missing values
    pdf_features[feature_cols] = pdf_features[feature_cols].fillna(0)
    
    # Score alerts
    X = pdf_features[feature_cols]
    triage_scores = model.predict_proba(X)[:, 1]  # Probability of positive class
    
    # Add scores back to dataframe
    pdf_features["triage_score"] = triage_scores
    
    # Convert back to Spark DataFrame
    scored_df = spark.createDataFrame(pdf_features[["alert_id", "triage_score"]])
    
    # Join back with original alerts data
    alerts_scored = alerts_to_score.join(scored_df, "alert_id")
    
    # Write to scored table
    (alerts_scored
     .write
     .format("delta")
     .mode("append")
     .option("mergeSchema", "true")
     .saveAsTable("aml.gold.alerts_scored"))
    
    print(f"✅ Scored {alert_count} alerts and saved to aml.gold.alerts_scored")
    
    # Show scoring statistics
    score_stats = scored_df.agg(
        F.min("triage_score").alias("min_score"),
        F.max("triage_score").alias("max_score"), 
        F.mean("triage_score").alias("avg_score"),
        F.expr("percentile_approx(triage_score, 0.9)").alias("p90_score")
    ).collect()[0]
    
    print(f"Score Statistics:")
    print(f"  Min: {score_stats['min_score']:.3f}")
    print(f"  Max: {score_stats['max_score']:.3f}")
    print(f"  Avg: {score_stats['avg_score']:.3f}")
    print(f"  P90: {score_stats['p90_score']:.3f}")

if __name__ == "__main__":
    score_alerts()