variable "name_prefix" {
  type = string
}

resource "aws_cognito_user_pool" "agent_pool" {
  name = "${var.name_prefix}-agent-pool"

  password_policy {
    minimum_length    = 12
    require_lowercase = true
    require_numbers   = true
    require_symbols   = true
    require_uppercase = true
  }

  admin_create_user_config {
    allow_admin_create_user_only = true
  }
}

resource "aws_cognito_user_pool_domain" "agent_domain" {
  domain       = var.name_prefix
  user_pool_id = aws_cognito_user_pool.agent_pool.id
}

resource "aws_cognito_resource_server" "agent_api" {
  identifier   = "agentcore-api"
  name         = "${var.name_prefix}-api"
  user_pool_id = aws_cognito_user_pool.agent_pool.id

  scope {
    scope_name        = "invoke"
    scope_description = "Invoke the agent swarm"
  }
}

resource "aws_cognito_user_pool_client" "agent_client" {
  name         = "${var.name_prefix}-client"
  user_pool_id = aws_cognito_user_pool.agent_pool.id

  generate_secret              = true
  allowed_oauth_flows          = ["client_credentials"]
  allowed_oauth_scopes         = ["agentcore-api/invoke"]
  allowed_oauth_flows_user_pool_client = true

  explicit_auth_flows = [
    "ALLOW_REFRESH_TOKEN_AUTH",
  ]

  depends_on = [aws_cognito_resource_server.agent_api]
}

output "user_pool_id" {
  value = aws_cognito_user_pool.agent_pool.id
}

output "user_pool_arn" {
  value = aws_cognito_user_pool.agent_pool.arn
}

output "client_id" {
  value = aws_cognito_user_pool_client.agent_client.id
}
