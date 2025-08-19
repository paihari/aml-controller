import pandas as pd
import mlflow
import mlflow.sklearn
import xgboost as xgb
from pyspark.sql import functions as F
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score, precision_recall_curve
from sklearn.preprocessing import LabelEncoder
import json

# Configuration
MODEL_NAME = "aml_alert_triage"
EXPERIMENT_NAME = "/aml/triage_model"

# Set MLflow experiment
mlflow.set_experiment(EXPERIMENT_NAME)

# Load alerts with case outcomes for training
alerts = spark.read.table("aml.gold.alerts")
cases = (spark.read
         .format("jdbc")
         .option("url", "jdbc:sqlserver://<server>.database.windows.net:1433;database=amlcases")
         .option("dbtable", "aml.cases")
         .option("authentication", "ActiveDirectoryPassword")
         .load()
         .select("alert_id", "status", "disposition"))

# Join alerts with case outcomes
labeled = (alerts.join(cases, "alert_id", "inner")
           .filter(F.col("disposition").isNotNull())
           .withColumn("label", F.when(F.col("disposition") == "SAR", 1).otherwise(0)))

# Feature engineering
def extract_evidence_features(df):
    """Extract features from evidence JSON"""
    df = df.withColumn("evidence_parsed", F.from_json(F.col("evidence"), "struct<sum7:double,sum30:double,tx_count:int,origin_country:string,beneficiary_country:string>"))
    
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
    
    return df

# Apply feature engineering
labeled_features = extract_evidence_features(labeled)

# Convert to Pandas for ML training
feature_cols = ["risk_score", "velocity_ratio", "tx_count", "is_high_risk_corridor", 
                "is_sanctions", "is_structuring"]

pdf = labeled_features.select(feature_cols + ["label", "typology"]).toPandas()

# Handle missing values
pdf = pdf.fillna(0)

# Prepare features and target
X = pdf[feature_cols]
y = pdf["label"]

# Add typology encoding
le_typology = LabelEncoder()
X["typology_encoded"] = le_typology.fit_transform(pdf["typology"])

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

print(f"Training samples: {len(X_train)}")
print(f"Test samples: {len(X_test)}")
print(f"Positive class ratio: {y.mean():.3f}")

# Model training with MLflow tracking
with mlflow.start_run():
    # Model parameters
    params = {
        "max_depth": 6,
        "n_estimators": 200,
        "learning_rate": 0.1,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "random_state": 42
    }
    
    # Log parameters
    mlflow.log_params(params)
    
    # Train model
    model = xgb.XGBClassifier(**params)
    model.fit(X_train, y_train)
    
    # Predictions
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    
    # Metrics
    auc = roc_auc_score(y_test, y_pred_proba)
    
    # Precision at different thresholds
    precision, recall, thresholds = precision_recall_curve(y_test, y_pred_proba)
    
    # Find precision at top 20% threshold
    top_20_threshold = sorted(y_pred_proba, reverse=True)[int(0.2 * len(y_pred_proba))]
    top_20_pred = (y_pred_proba >= top_20_threshold).astype(int)
    
    from sklearn.metrics import precision_score, recall_score
    precision_at_20 = precision_score(y_test, top_20_pred)
    recall_at_20 = recall_score(y_test, top_20_pred)
    
    # Log metrics
    mlflow.log_metric("auc", auc)
    mlflow.log_metric("precision_at_20", precision_at_20)
    mlflow.log_metric("recall_at_20", recall_at_20)
    
    # Feature importance
    feature_importance = dict(zip(X.columns, model.feature_importances_))
    mlflow.log_dict(feature_importance, "feature_importance.json")
    
    # Log model
    mlflow.sklearn.log_model(
        model, 
        artifact_path="model",
        registered_model_name=MODEL_NAME,
        input_example=X_train.head(5)
    )
    
    # Log classification report
    report = classification_report(y_test, y_pred, output_dict=True)
    mlflow.log_dict(report, "classification_report.json")
    
    print(f"AUC: {auc:.3f}")
    print(f"Precision @ Top 20%: {precision_at_20:.3f}")
    print(f"Recall @ Top 20%: {recall_at_20:.3f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    
    print("\nFeature Importance:")
    for feature, importance in sorted(feature_importance.items(), key=lambda x: x[1], reverse=True):
        print(f"{feature}: {importance:.3f}")