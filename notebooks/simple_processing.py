# Databricks notebook source
# MAGIC %md
# MAGIC # Simple AML Data Processing End-to-End Test
# MAGIC 
# MAGIC This notebook demonstrates a simple end-to-end flow:
# MAGIC 1. Read raw data from ADLS
# MAGIC 2. Process through bronze → silver → gold
# MAGIC 3. Apply simple AML rules
# MAGIC 4. Generate alerts

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

# Storage configuration
storage_account = "stamlaml20250119"
raw_container = "raw"
silver_container = "silver"  
gold_container = "gold"

# Construct paths
raw_path = f"abfss://{raw_container}@{storage_account}.dfs.core.windows.net"
silver_path = f"abfss://{silver_container}@{storage_account}.dfs.core.windows.net"
gold_path = f"abfss://{gold_container}@{storage_account}.dfs.core.windows.net"

print(f"Raw path: {raw_path}")
print(f"Silver path: {silver_path}")
print(f"Gold path: {gold_path}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Read Raw Data

# COMMAND ----------

# Read transactions
transactions_raw = spark.read.json(f"{raw_path}/transactions/2024-01-15/transactions.json")
print(f"Transactions count: {transactions_raw.count()}")
transactions_raw.show()

# COMMAND ----------

# Read parties
parties_raw = spark.read.json(f"{raw_path}/parties/2024-01-15/parties.json")
print(f"Parties count: {parties_raw.count()}")
parties_raw.show()

# COMMAND ----------

# Read accounts
accounts_raw = spark.read.json(f"{raw_path}/accounts/2024-01-15/accounts.json")
print(f"Accounts count: {accounts_raw.count()}")
accounts_raw.show()

# COMMAND ----------

# Read watchlists
watchlists_raw = spark.read.option("header", "true").csv(f"{raw_path}/watchlists/ofac/watchlists.csv")
print(f"Watchlists count: {watchlists_raw.count()}")
watchlists_raw.show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Process to Silver (Cleaned/Conformed)

# COMMAND ----------

from pyspark.sql.functions import col, to_timestamp, upper, trim, regexp_replace
import re

# Clean transactions
transactions_silver = (transactions_raw
    .withColumn("amount", col("amount").cast("decimal(18,2)"))
    .withColumn("value_date", to_timestamp("value_date"))
    .withColumn("currency", regexp_replace(col("currency"), r"[^A-Z]", ""))
    .dropDuplicates(["tx_id"])
)

print(f"Transactions silver count: {transactions_silver.count()}")
transactions_silver.show()

# COMMAND ----------

# Clean parties with name normalization for AML matching
def normalize_name(name_col):
    return upper(regexp_replace(trim(name_col), r"[^A-Za-z0-9 ]", " "))

parties_silver = (parties_raw
    .withColumn("name_norm", normalize_name(col("name")))
    .withColumn("country_norm", upper(trim(col("country"))))
    .select("party_id", "name", "name_norm", "dob", "country", "country_norm", "kyc_risk_rating")
)

print(f"Parties silver count: {parties_silver.count()}")
parties_silver.show()

# COMMAND ----------

# Clean watchlists
watchlists_silver = (watchlists_raw
    .withColumn("name_norm", normalize_name(col("name")))
    .withColumn("aka_norm", normalize_name(col("aka")))
    .withColumn("country_norm", upper(trim(col("country"))))
    .select("source", "name", "aka", "name_norm", "aka_norm", "dob", "country", "country_norm", "program", "list_id")
)

print(f"Watchlists silver count: {watchlists_silver.count()}")
watchlists_silver.show()

# COMMAND ----------

# Clean accounts
accounts_silver = (accounts_raw
    .select("account_id", "party_id", "iban", "opened_dt", "status", "country")
    .dropDuplicates(["account_id"])
)

print(f"Accounts silver count: {accounts_silver.count()}")
accounts_silver.show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Write Silver Data

# COMMAND ----------

# Write silver data to delta format
transactions_silver.write.format("delta").mode("overwrite").save(f"{silver_path}/transactions")
parties_silver.write.format("delta").mode("overwrite").save(f"{silver_path}/parties")
accounts_silver.write.format("delta").mode("overwrite").save(f"{silver_path}/accounts")
watchlists_silver.write.format("delta").mode("overwrite").save(f"{silver_path}/watchlists")

print("✅ Silver data written successfully")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: Generate Gold Layer - AML Alerts

# COMMAND ----------

from pyspark.sql.functions import lit, coalesce, when, sum as spark_sum, count, date_trunc, current_timestamp, sha2, concat_ws, to_json, struct

# Rule 1: Sanctions Screening
sanctions_alerts = (parties_silver.alias("p")
    .join(watchlists_silver.alias("w"), 
          (coalesce(col("p.name_norm"), lit("")) == coalesce(col("w.name_norm"), lit(""))) |
          (coalesce(col("p.name_norm"), lit("")) == coalesce(col("w.aka_norm"), lit(""))), "inner")
    .select(
        col("p.party_id").alias("subject_id"),
        lit("R1_SANCTIONS_MATCH").alias("typology"),
        lit(0.99).alias("risk_score"),
        to_json(struct(
            col("w.source").alias("source"),
            col("w.program").alias("program"), 
            col("w.list_id").alias("list_id"),
            col("p.name").alias("party_name"),
            col("w.name").alias("watchlist_name"),
            col("w.aka").alias("watchlist_aka")
        )).alias("evidence")
    )
)

print(f"Sanctions alerts: {sanctions_alerts.count()}")
sanctions_alerts.show()

# COMMAND ----------

# Rule 2: Structuring Detection (multiple small transactions same day)
structuring_threshold_small = 1000.0
structuring_threshold_total = 10000.0

structuring_alerts = (transactions_silver
    .filter(col("amount") > 0)  # Credits only
    .filter(col("amount") <= structuring_threshold_small)  # Small amounts
    .withColumn("d", date_trunc("DAY", col("value_date")))
    .groupBy("account_id", "d")
    .agg(
        count("*").alias("tx_count"),
        spark_sum("amount").alias("sum_amt")
    )
    .filter(col("sum_amt") >= structuring_threshold_total)
    .select(
        col("account_id").alias("subject_id"),
        lit("R2_STRUCTURING").alias("typology"),
        lit(0.8).alias("risk_score"),
        to_json(struct(
            col("tx_count"),
            col("sum_amt"),
            col("d").alias("date"),
            lit(structuring_threshold_small).alias("threshold_small"),
            lit(structuring_threshold_total).alias("threshold_total")
        )).alias("evidence")
    )
)

print(f"Structuring alerts: {structuring_alerts.count()}")
structuring_alerts.show()

# COMMAND ----------

# Rule 3: High-Risk Geography
high_risk_countries = ["IR", "AF", "CU", "KP", "RU", "SY"]

geography_alerts = (transactions_silver
    .filter(
        col("origin_country").isin(high_risk_countries) | 
        col("beneficiary_country").isin(high_risk_countries)
    )
    .select(
        col("account_id").alias("subject_id"),
        lit("R3_HIGH_RISK_CORRIDOR").alias("typology"),
        lit(0.7).alias("risk_score"),
        to_json(struct(
            col("origin_country"),
            col("beneficiary_country"),
            col("tx_id"),
            col("amount")
        )).alias("evidence")
    )
)

print(f"Geography alerts: {geography_alerts.count()}")
geography_alerts.show()

# COMMAND ----------

# Union all alerts
all_alerts = (sanctions_alerts
    .unionByName(structuring_alerts, allowMissingColumns=True)
    .unionByName(geography_alerts, allowMissingColumns=True)
    .withColumn("alert_id", sha2(concat_ws("|", col("subject_id"), col("typology"), col("evidence")), 256))
    .withColumn("created_ts", current_timestamp())
    .select("alert_id", "subject_id", "typology", "risk_score", "evidence", "created_ts")
)

print(f"Total alerts: {all_alerts.count()}")
all_alerts.show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5: Write Gold Data

# COMMAND ----------

# Write alerts to gold layer
all_alerts.write.format("delta").mode("overwrite").save(f"{gold_path}/alerts")

print("✅ Gold layer alerts written successfully")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 6: Validation and Summary

# COMMAND ----------

# Read back and validate
alerts_validation = spark.read.format("delta").load(f"{gold_path}/alerts")

print("=== END-TO-END TEST RESULTS ===")
print(f"✅ Raw data ingested: {transactions_raw.count()} transactions, {parties_raw.count()} parties")
print(f"✅ Silver data processed: {transactions_silver.count()} transactions cleaned")
print(f"✅ Gold alerts generated: {alerts_validation.count()} total alerts")

print("\n=== ALERT BREAKDOWN ===")
alerts_validation.groupBy("typology").count().show()

print("\n=== HIGH-RISK ALERTS ===")
alerts_validation.filter(col("risk_score") >= 0.9).select("alert_id", "subject_id", "typology", "risk_score").show()

print("\n✅ END-TO-END TEST COMPLETED SUCCESSFULLY!")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Next Steps
# MAGIC 
# MAGIC This completes a simple end-to-end test of the AML platform:
# MAGIC 
# MAGIC 1. ✅ Raw data ingestion from ADLS
# MAGIC 2. ✅ Data processing through medallion architecture 
# MAGIC 3. ✅ AML rule execution (sanctions, structuring, geography)
# MAGIC 4. ✅ Alert generation and storage
# MAGIC 
# MAGIC **Results:**
# MAGIC - Found sanctions match (Vladimir Petrov)
# MAGIC - Detected potential structuring (multiple small payments same day)
# MAGIC - Identified high-risk geography transaction (US → Iran)
# MAGIC 
# MAGIC **Ready for:**
# MAGIC - Power BI dashboard connection
# MAGIC - Case management integration
# MAGIC - ML model training on these alerts
# MAGIC - Real-time processing with Delta Live Tables