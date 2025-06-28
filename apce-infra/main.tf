provider "azurerm" {
  features {}
  subscription_id = "b28d3c26-ef18-4c28-8aa0-19492134ee8b"
}

resource "azurerm_resource_group" "apce_rg" {
  name     = "apce-resource-group"
  location = "canadacentral"
}


resource "azurerm_storage_account" "apce_storage" {
  name                     = "apcestorageacct123"
  resource_group_name      = azurerm_resource_group.apce_rg.name
  location                 = azurerm_resource_group.apce_rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

resource "azurerm_postgresql_flexible_server" "apce_postgres" {
  name                   = "apce-postgres-db123"
  resource_group_name    = azurerm_resource_group.apce_rg.name
  location               = "canadacentral"
  sku_name               = "GP_Standard_D4s_v3"
  storage_mb             = 32768
  version                = "15"

  zone                   = "1"  # Primary zone

  high_availability {
    mode                      = "ZoneRedundant"
    standby_availability_zone = "2"  # Standby zone, must be different from primary
  }

  administrator_login    = "adminuser"
  administrator_password = "SecurePassword123!"
}



resource "azurerm_search_service" "apce_search" {
  name                = "apcesearchservice-123"
  resource_group_name = azurerm_resource_group.apce_rg.name
  location            = azurerm_resource_group.apce_rg.location
  sku = "standard"
}

resource "azurerm_service_plan" "apce_plan" {
  name                = "apce-app-service-plan-123"
  resource_group_name = azurerm_resource_group.apce_rg.name
  location            = azurerm_resource_group.apce_rg.location
  os_type             = "Windows"
  sku_name            = "B1"
}


# -------------------------------
# Ollama VM (simple, in Canada Central)
# -------------------------------

resource "azurerm_public_ip" "ollama_public_ip" {
  name                = "ollama-public-ip"
  location            = azurerm_resource_group.apce_rg.location
  resource_group_name = azurerm_resource_group.apce_rg.name
  allocation_method   = "Dynamic"
}

resource "azurerm_network_interface" "ollama_nic" {
  name                = "ollama-nic"
  location            = azurerm_resource_group.apce_rg.location
  resource_group_name = azurerm_resource_group.apce_rg.name

  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.ollama_subnet.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.ollama_public_ip.id
  }
}

resource "azurerm_virtual_network" "ollama_vnet" {
  name                = "ollama-vnet"
  address_space       = ["10.20.0.0/16"]
  location            = azurerm_resource_group.apce_rg.location
  resource_group_name = azurerm_resource_group.apce_rg.name
}

resource "azurerm_subnet" "ollama_subnet" {
  name                 = "ollama-subnet"
  resource_group_name  = azurerm_resource_group.apce_rg.name
  virtual_network_name = azurerm_virtual_network.ollama_vnet.name
  address_prefixes     = ["10.20.1.0/24"]
}

resource "azurerm_linux_virtual_machine" "ollama_vm" {
  name                = "ollama-vm"
  resource_group_name = azurerm_resource_group.apce_rg.name
  location            = azurerm_resource_group.apce_rg.location
  size                = "Standard_D4s_v3" # Good for CPU workloads; use NC-series for GPU if needed
  admin_username      = "azureuser"

  network_interface_ids = [
    azurerm_network_interface.ollama_nic.id,
  ]

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Premium_LRS"
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-focal"
    sku       = "20_04-lts"
    version   = "latest"
  }

  tags = {
    environment = "production"
  }
}