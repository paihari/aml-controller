variable "tenant_id" {
  type = string
}

variable "location" {
  type    = string
  default = "westeurope"
}

variable "env" {
  type    = string
  default = "plat"
}

variable "owner" {
  type    = string
  default = "aml-team"
}

# Choose globally unique storage name (lowercase, 3-24 chars)
variable "sa_name" {
  type = string
}

# Networking
variable "vnet_cidr" {
  type    = string
  default = "10.10.0.0/16"
}

variable "pe_subnet_cidr" {
  type    = string
  default = "10.10.1.0/24"
}