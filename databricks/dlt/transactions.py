import dlt
from pyspark.sql.functions import col, to_timestamp, regexp_replace

# ---- Paths (UC external locations) ----
RAW   = "abfss://raw@<STORAGE>.dfs.core.windows.net/transactions/"
SILVER= "abfss://silver@<STORAGE>.dfs.core.windows.net/transactions/"
GOLD  = "abfss://gold@<STORAGE>.dfs.core.windows.net/features/"

@dlt.table(
  name="aml_raw_transactions",
  comment="Landing of transactions (auto loader).",
  table_properties={"quality": "bronze"}
)
def raw_transactions():
  return (
    spark.readStream.format("cloudFiles")
      .option("cloudFiles.format","json")          # or "csv"/"parquet"
      .option("cloudFiles.inferColumnTypes","true")
      .load(RAW)
      .withColumn("ingest_ts", to_timestamp(col("_metadata.file_modification_time")/1000))
  )

@dlt.view(name="txn_clean")
def txn_clean():
  df = dlt.read_stream("aml_raw_transactions")
  return (
    df
      .withColumn("amount", col("amount").cast("decimal(18,2)"))
      .withColumn("value_date", to_timestamp("value_date"))
      .withColumn("currency", regexp_replace(col("currency"), r"[^A-Z]", ""))
  )

@dlt.table(
  name="aml_transactions",
  comment="Conformed transactions (deduped).",
  table_properties={"quality": "silver"}
)
def transactions_silver():
  return (
    dlt.read_stream("txn_clean")
      .dropDuplicates(["tx_id"])
  )

@dlt.table(
  name="aml_txn_features",
  comment="Simple AML features per account per day.",
  table_properties={"quality": "gold"}
)
def txn_features():
  from pyspark.sql.functions import sum as _sum, countDistinct, date_trunc
  df = dlt.read("aml_transactions")
  return (
    df.groupBy(
      col("account_id"),
      date_trunc("DAY", col("value_date")).alias("d")
    ).agg(
      _sum("amount").alias("sum_amt"),
      countDistinct("counterparty_id").alias("cp_count")
    )
  )