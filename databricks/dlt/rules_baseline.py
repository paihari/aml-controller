import dlt, json
from pyspark.sql import functions as F, Window as W

# Helpers
def param(name, default):
    return float(dlt.utils.get_pipeline_conf().get(name, default)) if str(default).replace('.','',1).isdigit() \
           else dlt.utils.get_pipeline_conf().get(name, default)

SMALL   = param("R_SMALL_TX", 950.0)
TOTAL   = param("R_STRUCTURING_TOTAL", 10000.0)
RT_DAYS = int(param("R_ROUND_TRIP_DAYS", 5))
WIN_D   = int(param("R_VELOCITY_WINDOW_DAYS", 7))
BASE_D  = int(param("R_VELOCITY_BASELINE_DAYS", 30))
RISK_C  = set(str(param("RISK_COUNTRIES","IR,AF,CU,KN,PA,YE,SO,LB,LY,SD,SY,IQ,UA,RU")).split(","))

tx = spark.read.table("aml.silver.aml_transactions")   # from Step 3
acct = spark.read.table("aml.silver.accounts")
party = spark.read.table("aml.silver.parties")
wl = spark.read.table("aml.silver.watchlists")

# R1 — Sanctions name/DOB/country match
@dlt.table(name="r1_sanctions", table_properties={"quality":"gold"})
def r1_sanctions():
    hits = (party.alias("p")
      .join(wl.alias("w"), 
            (F.coalesce(F.col("p.name_norm"),F.lit("")) == F.coalesce(F.col("w.name_norm"),F.lit(""))) |
            (F.coalesce(F.col("p.name_norm"),F.lit("")) == F.coalesce(F.col("w.aka_norm"),F.lit(""))), "inner")
      .where( (F.col("p.dob").isNull()) | (F.col("p.dob")==F.col("w.dob")) )
      .select(
          F.col("p.party_id").alias("subject_id"),
          F.lit("R1_SANCTIONS_MATCH").alias("typology"),
          F.lit(0.99).alias("risk_score"),
          F.to_json(F.struct("w.source","w.program","w.list_id","p.name","w.name","w.aka")).alias("evidence")
      )
    )
    return hits

# R2 — Structuring/smurfing: many small credits in 24h per account
@dlt.table(name="r2_structuring", table_properties={"quality":"gold"})
def r2_structuring():
    t = spark.read.table("aml.silver.aml_transactions").filter(F.col("amount")>0) # credits
    t = t.withColumn("d", F.to_date("value_date"))
    w = W.partitionBy("account_id","d")
    agg = (t.filter(F.col("amount") <= F.lit(SMALL))
        .groupBy("account_id","d")
        .agg(F.count("*").alias("tx_count"), F.sum("amount").alias("sum_amt"))
        .filter(F.col("sum_amt") >= F.lit(TOTAL))
        .select(
            F.col("account_id").alias("subject_id"),
            F.lit("R2_STRUCTURING").alias("typology"),
            F.lit(0.8).alias("risk_score"),
            F.to_json(F.struct("tx_count","sum_amt","day","threshold_small", "threshold_total")
                .withField("day", F.col("d"))
                .withField("threshold_small", F.lit(SMALL))
                .withField("threshold_total", F.lit(TOTAL))
            ).alias("evidence")
        )
    )
    return agg

# R3 — High-risk corridors by country (origin/destination)
@dlt.table(name="r3_high_risk_corridor", table_properties={"quality":"gold"})
def r3_high_risk_corridor():
    rc = F.udf(lambda c: c in RISK_C, "boolean")
    return (tx
      .where(rc(F.upper(F.col("beneficiary_country"))) | rc(F.upper(F.col("origin_country"))))
      .select(
        F.col("account_id").alias("subject_id"),
        F.lit("R3_HIGH_RISK_CORRIDOR").alias("typology"),
        F.lit(0.7).alias("risk_score"),
        F.to_json(F.struct("origin_country","beneficiary_country","tx_id","amount")).alias("evidence")
      )
    )

# R4 — Velocity spike (7d vs 30d baseline)
@dlt.table(name="r4_velocity_spike", table_properties={"quality":"gold"})
def r4_velocity_spike():
    t = tx.select("account_id","value_date","amount").withColumn("d", F.to_date("value_date"))
    win7  = W.partitionBy("account_id").orderBy(F.col("d").cast("long")).rangeBetween(-WIN_D*86400, 0)
    win30 = W.partitionBy("account_id").orderBy(F.col("d").cast("long")).rangeBetween(-BASE_D*86400, 0)
    s = (t
      .withColumn("sum7",  F.sum("amount").over(win7))
      .withColumn("sum30", F.sum("amount").over(win30))
      .withColumn("ratio", F.when(F.col("sum30")>0, F.col("sum7")/F.col("sum30")).otherwise(F.lit(0.0)))
      .filter(F.col("ratio") >= 0.6)   # tune
      .select(
        "account_id",
        F.lit("R4_VELOCITY_SPIKE").alias("typology"),
        F.lit(0.6).alias("risk_score"),
        F.to_json(F.struct("sum7","sum30","ratio")).alias("evidence")
      ).withColumnRenamed("account_id","subject_id")
    )
    return s

# R5 — Round-tripping: out & in between same pair, same amount within N days
@dlt.table(name="r5_round_tripping", table_properties={"quality":"gold"})
def r5_round_tripping():
    a = tx.select("tx_id","value_date","amount","account_id","counterparty_account_id")
    b = a.selectExpr("tx_id as tx_id2","value_date as vd2","amount as amount2",
                     "counterparty_account_id as account_id","account_id as counterparty_account_id")
    j = (a.join(b, (a.account_id==b.account_id) & (a.counterparty_account_id==b.counterparty_account_id) & (a.amount==b.amount2))
          .where(F.abs(F.datediff(a.value_date, b.vd2)) <= RT_DAYS)
          .select(
              a.account_id.alias("subject_id"),
              F.lit("R5_ROUND_TRIP").alias("typology"),
              F.lit(0.65).alias("risk_score"),
              F.to_json(F.struct(a.tx_id.alias("tx_out"), F.col("tx_id2").alias("tx_in"),
                                 a.amount.alias("amount"), "counterparty_account_id")).alias("evidence")
          ).dropDuplicates()
    )
    return j

# Union → gold.alerts
@dlt.table(name="aml.gold.alerts", table_properties={"quality":"gold"})
def alerts():
    from functools import reduce
    dfs = [dlt.read(t) for t in ["r1_sanctions","r2_structuring","r3_high_risk_corridor","r4_velocity_spike","r5_round_tripping"]]
    all_alerts = reduce(lambda x,y: x.unionByName(y, allowMissingColumns=True), dfs)
    return (all_alerts
      .withColumn("alert_id", F.sha2(F.concat_ws("|","subject_id","typology","evidence"),256))
      .withColumn("created_ts", F.current_timestamp())
      .select("alert_id","subject_id","typology","risk_score","evidence","created_ts")
    )