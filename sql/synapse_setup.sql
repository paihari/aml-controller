-- In Synapse Serverless
CREATE DATABASE aml_bi;
GO
USE aml_bi;
GO

IF NOT EXISTS (SELECT * FROM sys.symmetric_keys WHERE name = '##MS_DatabaseMasterKey##')
  CREATE MASTER KEY ENCRYPTION BY PASSWORD = 'Temp#Password_Only_For_This_Step';

CREATE DATABASE SCOPED CREDENTIAL msi_cred WITH IDENTITY = 'Managed Identity';

IF NOT EXISTS (SELECT * FROM sys.external_data_sources WHERE name = 'ds_gold')
CREATE EXTERNAL DATA SOURCE ds_gold
WITH ( TYPE = HADOOP,
       LOCATION = 'abfss://gold@<STORAGE>.dfs.core.windows.net',
       CREDENTIAL = msi_cred );
GO