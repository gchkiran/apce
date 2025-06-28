output "resource_group_name" {
  value = azurerm_resource_group.apce_rg.name
}

output "storage_account_name" {
  value = azurerm_storage_account.apce_storage.name
}

output "postgresql_server_name" {
  value = azurerm_postgresql_flexible_server.apce_postgres.name
}
