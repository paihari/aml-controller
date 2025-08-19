# /Repos/aml/case_sync/alerts_to_cases.py
from pyspark.sql.functions import col, current_timestamp
import os

JDBC_URL  = dbutils.secrets.get("kv-aml", "sql-jdbc-url")     # e.g., jdbc:sqlserver://<server>.database.windows.net:1433;database=amlcases
JDBC_USER = dbutils.secrets.get("kv-aml", "sql-user")
JDBC_PWD  = dbutils.secrets.get("kv-aml", "sql-pass")

# Read CDF (inserts & updates) since checkpoint
df = (spark.readStream
      .format("delta")
      .option("readChangeData", "true")
      .table("aml.gold.alerts")
      .filter("_change_type IN ('insert','update_postimage')")   # CDF metadata columns
      .selectExpr("alert_id","subject_id","typology","risk_score","created_ts")
)

# Write to staging in-memory per microbatch and MERGE into SQL
def upsert_to_sql(batch_df, batch_id):
    batch_df.createOrReplaceTempView("v_new_alerts")
    # Write to a temporary table in SQL (staging) then MERGE into aml.cases
    tmp_table = "##incoming_alerts"  # SQL global temp table (session-scoped)
    (batch_df
      .write
      .format("jdbc")
      .mode("overwrite")
      .option("url", JDBC_URL)
      .option("user", JDBC_USER)
      .option("password", JDBC_PWD)
      .option("dbtable", tmp_table)
      .save())

    merge_sql = """
    MERGE aml.cases AS tgt
    USING (SELECT alert_id, subject_id, typology, risk_score, created_ts FROM ##incoming_alerts) AS src
      ON tgt.alert_id = src.alert_id
    WHEN NOT MATCHED THEN
      INSERT (alert_id, subject_id, typology, risk_score, status, created_ts, updated_ts)
      VALUES (src.alert_id, src.subject_id, src.typology, src.risk_score, 'Open', src.created_ts, SYSUTCDATETIME())
    WHEN MATCHED THEN
      UPDATE SET
        tgt.risk_score = src.risk_score,
        tgt.updated_ts = SYSUTCDATETIME();
    """
    # Execute MERGE via JDBC (small trick: use the same connection with a dummy write to run a query)
    from pyspark.sql import SparkSession
    spark._jsparkSession.sessionState().conf().setConfString("spark.datasource.jdbc.pushDownAggregate.enabled", "false")
    (spark.read
         .format("jdbc")
         .option("url", JDBC_URL)
         .option("user", JDBC_USER)
         .option("password", JDBC_PWD)
         .option("query", merge_sql)
         .load()
    )

(df.writeStream
  .foreachBatch(upsert_to_sql)
  .outputMode("update")
  .option("checkpointLocation", "abfss://logs@<STORAGE>.dfs.core.windows.net/checkpoints/case_sync")
  .start()
)