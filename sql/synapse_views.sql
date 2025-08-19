USE aml_bi;
GO

-- Base alerts view
CREATE OR ALTER VIEW vw_alerts AS
SELECT
  TRY_CAST(JSON_VALUE(evidence, '$.sum7') AS DECIMAL(18,2))        AS sum7,
  TRY_CAST(JSON_VALUE(evidence, '$.sum30') AS DECIMAL(18,2))       AS sum30,
  JSON_VALUE(evidence, '$.origin_country')                         AS origin_country,
  JSON_VALUE(evidence, '$.beneficiary_country')                    AS beneficiary_country,
  a.alert_id,
  a.subject_id,
  a.typology,
  a.risk_score,
  a.created_ts,
  CAST(a.created_ts AS date) AS created_d
FROM OPENROWSET(
  BULK 'alerts',
  DATA_SOURCE = 'ds_gold',
  FORMAT = 'DELTA'
) WITH (
  alert_id     VARCHAR(128),
  subject_id   VARCHAR(128),
  typology     VARCHAR(64),
  risk_score   FLOAT,
  evidence     VARCHAR(8000),
  created_ts   DATETIME2
) AS a;
GO

-- Daily counts by typology
CREATE OR ALTER VIEW vw_typology_daily AS
SELECT created_d, typology, COUNT(*) AS alerts
FROM vw_alerts
GROUP BY created_d, typology;
GO

-- 7-day investigator queue (latest)
CREATE OR ALTER VIEW vw_investigator_queue AS
SELECT *
FROM vw_alerts
WHERE created_ts >= DATEADD(day, -7, SYSUTCDATETIME());
GO

-- Corridor heatmap (origin -> beneficiary)
CREATE OR ALTER VIEW vw_corridors AS
SELECT
  UPPER(origin_country)      AS origin_country,
  UPPER(beneficiary_country) AS beneficiary_country,
  COUNT(*)                   AS alerts
FROM vw_alerts
WHERE origin_country IS NOT NULL AND beneficiary_country IS NOT NULL
GROUP BY UPPER(origin_country), UPPER(beneficiary_country);
GO

-- Scored alerts view (includes ML triage scores)
CREATE OR ALTER VIEW vw_alerts_scored AS
SELECT a.*, s.triage_score
FROM vw_alerts a
LEFT JOIN OPENROWSET(
  BULK 'alerts_scored',
  DATA_SOURCE = 'ds_gold',
  FORMAT='DELTA'
) WITH (
  alert_id     VARCHAR(128),
  triage_score FLOAT
) AS s
ON a.alert_id = s.alert_id;
GO