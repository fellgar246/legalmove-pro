# The azurerm_static_web_app resource exposes a sensitive `api_key` (deployment token) in
# Terraform state. It is intentionally NOT surfaced as an output here. Fetch it at deploy
# time via: az staticwebapp secrets list --name <name> --query "properties.apiKey" -o tsv

resource "azurerm_static_web_app" "this" {
  name                = var.name
  resource_group_name = var.resource_group_name
  location            = var.location
  sku_tier            = var.sku_tier
  sku_size            = var.sku_size
  tags                = var.tags
}
