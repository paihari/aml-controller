import dlt, re, unicodedata
from pyspark.sql.functions import col, upper, regexp_replace, trim, to_date, lit

ST_RAW  = "abfss://raw@<STORAGE>.dfs.core.windows.net/watchlists/"
CAT = "aml"; SCH_SILVER = "silver"

def norm_name(c):
    if c is None: return None
    x = unicodedata.normalize("NFKD", c)
    x = "".join(ch for ch in x if not unicodedata.combining(ch))
    x = re.sub(r"[^A-Za-z0-9 ]", " ", x).upper()
    x = re.sub(r"\s+", " ", x).strip()
    return x

@dlt.table(name="wl_raw", table_properties={"quality":"bronze"})
def wl_raw():
    return (spark.readStream
      .format("cloudFiles").option("cloudFiles.format","csv").option("header","true")
      .load(ST_RAW)
      .withColumn("source", regexp_replace(col("_metadata.file_path"), r".*/watchlists/([^/]+)/.*", r"$1"))
    )

@dlt.table(name=f"{CAT}.{SCH_SILVER}.watchlists", table_properties={"quality":"silver"})
def watchlists():
    from pyspark.sql.functions import udf
    norm = udf(norm_name)
    df = dlt.read_stream("wl_raw")
    return (df
      .withColumn("name_norm", norm(trim(col("name"))))
      .withColumn("aka_norm",  norm(trim(col("aka"))))
      .withColumn("dob", to_date("dob"))
      .withColumn("country_norm", upper(trim(col("country"))))
      .select("source","name","aka","name_norm","aka_norm","dob","country","country_norm","program","list_id")
    )

@dlt.table(name="aml.silver.parties", table_properties={"quality":"silver"})
def parties():
    df = spark.read.table("aml.raw.parties_raw")  # or your raw name
    return (df
      .withColumn("name_norm", upper(regexp_replace(trim(col("name")), r"[^A-Za-z0-9 ]"," ")))
      .withColumn("country_norm", upper(trim(col("country"))))
      .select("party_id","name","name_norm","dob","country","country_norm","kyc_risk_rating")
    )

@dlt.table(name="aml.silver.accounts", table_properties={"quality":"silver"})
def accounts():
    df = spark.read.table("aml.raw.accounts_raw")
    return df.select("account_id","party_id","iban","opened_dt","status","country").dropDuplicates(["account_id"])