terraform {
  required_providers {
    databricks = { source = "databricks/databricks", version = "~> 1.45" }
  }
}

# Account-level provider (for metastore)
provider "databricks" {
  alias      = "accounts"
  host       = "https://accounts.azuredatabricks.net"
  account_id = var.databricks_account_id
  auth_type  = "azure-cli"   # uses your az login
}

# Workspace-level provider (for catalogs/schemas/grants/pipeline)
provider "databricks" {
  alias                         = "ws"
  host                          = azurerm_databricks_workspace.ws.workspace_url
  azure_workspace_resource_id   = azurerm_databricks_workspace.ws.id
  auth_type                     = "azure-cli"
}