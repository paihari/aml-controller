# -------- Databricks Workspace (simplified) --------
resource "azurerm_resource_group" "dbx" {
  name     = "rg-aml-dbx"
  location = local.location
  tags     = local.tags
}

resource "azurerm_databricks_workspace" "ws" {
  name                = "dbw-aml-${var.env}"
  resource_group_name = azurerm_resource_group.dbx.name
  location            = local.location
  sku                 = "premium"
  
  tags = local.tags
}