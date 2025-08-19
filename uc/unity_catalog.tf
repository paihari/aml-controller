# ----- Create a UC Metastore and assign it to this workspace -----
resource "databricks_metastore" "aml" {
  provider  = databricks.accounts
  name      = "ms-aml"
  region    = azurerm_resource_group.dbx.location  # must match workspace region
  storage_root = "abfss://logs@${var.sa_name}.dfs.core.windows.net/uc/ms-aml"
}

resource "databricks_metastore_assignment" "ws_assign" {
  provider     = databricks.accounts
  metastore_id = databricks_metastore.aml.id
  workspace_id = azurerm_databricks_workspace.ws.workspace_id
  default_catalog_name = "hive_metastore" # or leave default; we'll use catalog "aml"
}

# ----- Storage credential using Azure Access Connector MI -----
resource "databricks_storage_credential" "aml" {
  provider = databricks.ws
  name     = "sc-aml"
  azure_managed_identity {
    access_connector_id = azurerm_databricks_access_connector.uc.id
  }
  comment = "UC credential to ADLS via Access Connector"
}

# ----- External locations (one per container) -----
resource "databricks_external_location" "raw" {
  provider             = databricks.ws
  name                 = "loc-raw"
  url                  = "abfss://raw@${var.sa_name}.dfs.core.windows.net/"
  credential_name      = databricks_storage_credential.aml.name
}

resource "databricks_external_location" "silver" {
  provider             = databricks.ws
  name                 = "loc-silver"
  url                  = "abfss://silver@${var.sa_name}.dfs.core.windows.net/"
  credential_name      = databricks_storage_credential.aml.name
}

resource "databricks_external_location" "gold" {
  provider             = databricks.ws
  name                 = "loc-gold"
  url                  = "abfss://gold@${var.sa_name}.dfs.core.windows.net/"
  credential_name      = databricks_storage_credential.aml.name
}

# ----- Catalog & schemas mapped to the locations -----
resource "databricks_catalog" "aml" {
  provider = databricks.ws
  name     = "aml"
  comment  = "AML analytics catalog"
}

resource "databricks_schema" "raw" {
  provider         = databricks.ws
  catalog_name     = databricks_catalog.aml.name
  name             = "raw"
  comment          = "Bronze landing"
  storage_location = databricks_external_location.raw.url
}

resource "databricks_schema" "silver" {
  provider         = databricks.ws
  catalog_name     = databricks_catalog.aml.name
  name             = "silver"
  comment          = "Conformed layer"
  storage_location = databricks_external_location.silver.url
}

resource "databricks_schema" "gold" {
  provider         = databricks.ws
  catalog_name     = databricks_catalog.aml.name
  name             = "gold"
  comment          = "Serving layer"
  storage_location = databricks_external_location.gold.url
}

# ----- Grants (adjust to your groups) -----
# Expect that your Entra groups are SCIM-synced into Databricks with same names:
# grp-aml-data-engineers, grp-aml-data-scientists, grp-aml-investigators
data "databricks_group" "eng" { provider = databricks.ws, display_name = "grp-aml-data-engineers" }
data "databricks_group" "sci" { provider = databricks.ws, display_name = "grp-aml-data-scientists" }
data "databricks_group" "inv" { provider = databricks.ws, display_name = "grp-aml-investigators" }

resource "databricks_grants" "catalog" {
  provider = databricks.ws
  catalog  = databricks_catalog.aml.name
  grant {
    principal  = data.databricks_group.eng.display_name
    privileges = ["USE_CATALOG", "CREATE_SCHEMA"]
  }
  grant {
    principal  = data.databricks_group.sci.display_name
    privileges = ["USE_CATALOG"]
  }
  grant {
    principal  = data.databricks_group.inv.display_name
    privileges = ["USE_CATALOG"]
  }
}

resource "databricks_grants" "schema_raw" {
  provider = databricks.ws
  schema   = "${databricks_catalog.aml.name}.${databricks_schema.raw.name}"
  grant { principal = data.databricks_group.eng.display_name  privileges = ["USE_SCHEMA","CREATE_TABLE","MODIFY","SELECT"] }
}

resource "databricks_grants" "schema_silver" {
  provider = databricks.ws
  schema   = "${databricks_catalog.aml.name}.${databricks_schema.silver.name}"
  grant { principal = data.databricks_group.eng.display_name  privileges = ["USE_SCHEMA","CREATE_TABLE","MODIFY","SELECT"] }
  grant { principal = data.databricks_group.sci.display_name  privileges = ["USE_SCHEMA","SELECT","CREATE_TABLE"] }
}

resource "databricks_grants" "schema_gold" {
  provider = databricks.ws
  schema   = "${databricks_catalog.aml.name}.${databricks_schema.gold.name}"
  grant { principal = data.databricks_group.inv.display_name  privileges = ["USE_SCHEMA","SELECT"] }
  grant { principal = data.databricks_group.sci.display_name  privileges = ["USE_SCHEMA","SELECT"] }
}