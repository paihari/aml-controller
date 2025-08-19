from mlflow.tracking import MlflowClient
import mlflow
from pyspark.sql import functions as F

MODEL_NAME = "aml_alert_triage"

def promote_model_to_staging():
    """Promote latest model version to Staging"""
    client = MlflowClient()
    
    # Get latest version
    latest_versions = client.get_latest_versions(MODEL_NAME, stages=["None"])
    if not latest_versions:
        print("No model versions found")
        return False
    
    latest_version = latest_versions[0]
    
    # Transition to Staging
    client.transition_model_version_stage(
        name=MODEL_NAME,
        version=latest_version.version,
        stage="Staging"
    )
    
    print(f"✅ Promoted model {MODEL_NAME} version {latest_version.version} to Staging")
    return True

def evaluate_staging_model():
    """Evaluate staging model performance"""
    client = MlflowClient()
    
    # Get staging version
    staging_versions = client.get_latest_versions(MODEL_NAME, stages=["Staging"])
    if not staging_versions:
        print("No staging model found")
        return False, {}
    
    staging_version = staging_versions[0]
    
    # Load model metrics from MLflow
    run = client.get_run(staging_version.run_id)
    metrics = run.data.metrics
    
    print(f"Staging Model {MODEL_NAME} v{staging_version.version} Metrics:")
    print(f"  AUC: {metrics.get('auc', 0):.3f}")
    print(f"  Precision @ Top 20%: {metrics.get('precision_at_20', 0):.3f}")
    print(f"  Recall @ Top 20%: {metrics.get('recall_at_20', 0):.3f}")
    
    # Define acceptance criteria
    min_auc = 0.75
    min_precision_at_20 = 0.6
    
    passes_criteria = (
        metrics.get('auc', 0) >= min_auc and
        metrics.get('precision_at_20', 0) >= min_precision_at_20
    )
    
    print(f"Model passes acceptance criteria: {passes_criteria}")
    
    return passes_criteria, metrics

def promote_model_to_production():
    """Promote staging model to production after evaluation"""
    client = MlflowClient()
    
    # Evaluate staging model
    passes_evaluation, metrics = evaluate_staging_model()
    
    if not passes_evaluation:
        print("❌ Model failed evaluation criteria, not promoting to Production")
        return False
    
    # Get current production model (if any)
    prod_versions = client.get_latest_versions(MODEL_NAME, stages=["Production"])
    
    # Get staging model
    staging_versions = client.get_latest_versions(MODEL_NAME, stages=["Staging"])
    staging_version = staging_versions[0]
    
    # Archive current production model
    if prod_versions:
        current_prod = prod_versions[0]
        client.transition_model_version_stage(
            name=MODEL_NAME,
            version=current_prod.version,
            stage="Archived"
        )
        print(f"Archived previous production model version {current_prod.version}")
    
    # Promote staging to production
    client.transition_model_version_stage(
        name=MODEL_NAME,
        version=staging_version.version,
        stage="Production"
    )
    
    print(f"✅ Promoted model {MODEL_NAME} version {staging_version.version} to Production")
    
    # Add description with metrics
    description = f"AUC: {metrics.get('auc', 0):.3f}, Precision@20%: {metrics.get('precision_at_20', 0):.3f}"
    client.update_model_version(
        name=MODEL_NAME,
        version=staging_version.version,
        description=description
    )
    
    return True

def run_model_validation():
    """Run validation on recent data"""
    print("Running model validation on recent alerts...")
    
    # Get recent scored alerts for validation
    recent_alerts = (spark.read.table("aml.gold.alerts_scored")
                    .filter(F.col("created_ts") >= F.current_date() - 7))
    
    alert_count = recent_alerts.count()
    if alert_count == 0:
        print("No recent scored alerts for validation")
        return True
    
    # Basic validation checks
    score_stats = recent_alerts.agg(
        F.min("triage_score").alias("min_score"),
        F.max("triage_score").alias("max_score"),
        F.count("triage_score").alias("total_scored"),
        F.sum(F.when(F.col("triage_score").isNull(), 1).otherwise(0)).alias("null_scores")
    ).collect()[0]
    
    print(f"Validation Results:")
    print(f"  Total alerts scored: {score_stats['total_scored']}")
    print(f"  Null scores: {score_stats['null_scores']}")
    print(f"  Score range: {score_stats['min_score']:.3f} - {score_stats['max_score']:.3f}")
    
    # Validation criteria
    validation_passed = (
        score_stats['null_scores'] == 0 and  # No null scores
        0 <= score_stats['min_score'] <= 1 and  # Scores in valid range
        0 <= score_stats['max_score'] <= 1
    )
    
    print(f"Validation passed: {validation_passed}")
    return validation_passed

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python model_promotion.py [staging|production|validate]")
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action == "staging":
        promote_model_to_staging()
    elif action == "production":
        promote_model_to_production()
    elif action == "validate":
        run_model_validation()
    else:
        print("Invalid action. Use 'staging', 'production', or 'validate'")