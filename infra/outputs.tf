output "key_vault_name" {
  value = azurerm_key_vault.kv.name
}

output "storage_account_name" {
  value = azurerm_storage_account.adls.name
}

output "vnet_id" {
  value = azurerm_virtual_network.hub.id
}

output "resource_group_names" {
  value = {
    network = azurerm_resource_group.net.name
    security = azurerm_resource_group.sec.name
    data = azurerm_resource_group.data.name
    databricks = azurerm_resource_group.dbx.name
  }
}

output "databricks_workspace_id" {
  value = azurerm_databricks_workspace.ws.workspace_id
}

output "databricks_workspace_url" {
  value = azurerm_databricks_workspace.ws.workspace_url
}