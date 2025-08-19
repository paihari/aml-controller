terraform {
  required_version = ">= 1.6.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.116"
    }
  }
}

provider "azurerm" {
  features {}
}

# ---------- Variables ----------
locals {
  location         = var.location
  rg_net_name      = "rg-aml-net-hub"
  rg_sec_name      = "rg-aml-sec"
  rg_data_name     = "rg-aml-data"
  vnet_name        = "vnet-aml-hub"
  pe_subnet_name   = "snet-pe"
  kv_name          = "kv-aml-plat-${random_id.suffix.hex}"
  sa_name          = var.sa_name
  tags             = { env = var.env, workload = "aml-platform", owner = var.owner }
}

# Generate random suffix for unique naming
resource "random_id" "suffix" {
  byte_length = 4
}

# ---------- Resource Groups ----------
resource "azurerm_resource_group" "net" {
  name     = local.rg_net_name
  location = local.location
  tags     = local.tags
}

resource "azurerm_resource_group" "sec" {
  name     = local.rg_sec_name
  location = local.location
  tags     = local.tags
}

resource "azurerm_resource_group" "data" {
  name     = local.rg_data_name
  location = local.location
  tags     = local.tags
}

# ---------- Networking: Hub VNet + Private Endpoint Subnet ----------
resource "azurerm_virtual_network" "hub" {
  name                = local.vnet_name
  location            = local.location
  resource_group_name = azurerm_resource_group.net.name
  address_space       = [var.vnet_cidr]
  tags                = local.tags
}

resource "azurerm_subnet" "pe" {
  name                 = local.pe_subnet_name
  resource_group_name  = azurerm_resource_group.net.name
  virtual_network_name = azurerm_virtual_network.hub.name
  address_prefixes     = [var.pe_subnet_cidr]
  private_endpoint_network_policies = "Enabled"
}

# ---------- Key Vault (without CMK initially) ----------
data "azurerm_client_config" "current" {}

resource "azurerm_key_vault" "kv" {
  name                        = local.kv_name
  location                    = local.location
  resource_group_name         = azurerm_resource_group.sec.name
  tenant_id                   = data.azurerm_client_config.current.tenant_id
  sku_name                    = "standard"
  purge_protection_enabled    = false  # Simplified for dev
  soft_delete_retention_days  = 7      # Minimum for dev
  enable_rbac_authorization   = true
  
  # Allow current user to manage Key Vault
  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = data.azurerm_client_config.current.object_id
    
    key_permissions = [
      "Create", "Get", "List", "Update", "Delete", "Recover", "Backup", "Restore"
    ]
    
    secret_permissions = [
      "Get", "List", "Set", "Delete", "Recover", "Backup", "Restore"
    ]
  }
  
  tags = local.tags
}

# ---------- ADLS Gen2 (simplified without CMK) ----------
resource "azurerm_storage_account" "adls" {
  name                     = local.sa_name
  resource_group_name      = azurerm_resource_group.data.name
  location                 = local.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"
  is_hns_enabled           = true
  min_tls_version          = "TLS1_2"
  allow_nested_items_to_be_public = false
  
  tags = local.tags
}

# -------- ADLS containers for medallion --------
resource "azurerm_storage_container" "raw" {
  name                  = "raw"
  storage_account_name  = azurerm_storage_account.adls.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "silver" {
  name                  = "silver"
  storage_account_name  = azurerm_storage_account.adls.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "gold" {
  name                  = "gold"
  storage_account_name  = azurerm_storage_account.adls.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "logs" {
  name                  = "logs"
  storage_account_name  = azurerm_storage_account.adls.name
  container_access_type = "private"
}