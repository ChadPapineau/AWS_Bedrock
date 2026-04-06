output "ecr_repository_url" {
  description = "ECR repository URL for the agent container image"
  value       = aws_ecr_repository.agent.repository_url
}

output "runtime_endpoint" {
  description = "AgentCore Runtime invocation endpoint"
  value       = module.agentcore_runtime.runtime_endpoint
}

output "gateway_endpoint" {
  description = "AgentCore Gateway MCP endpoint"
  value       = module.agentcore_gateway.gateway_endpoint
}

output "memory_id" {
  description = "AgentCore Memory resource ID"
  value       = module.agentcore_memory.memory_id
}

output "cognito_user_pool_id" {
  description = "Cognito User Pool ID for agent authentication"
  value       = module.cognito.user_pool_id
}

output "cognito_client_id" {
  description = "Cognito App Client ID"
  value       = module.cognito.client_id
}

# --- CyberArk Scanner Outputs ---

output "cyberark_scanner_bucket" {
  description = "S3 bucket for CyberArk scanner artifacts"
  value       = var.enable_cyberark_scanner ? module.cyberark_scanner[0].scanner_bucket_name : null
}

output "cyberark_scanner_job_name" {
  description = "Glue job name for the CyberArk scanner"
  value       = var.enable_cyberark_scanner ? module.cyberark_scanner[0].scanner_glue_job_name : null
}

output "cyberark_scanner_secret_arn" {
  description = "Secrets Manager ARN for CyberArk credentials"
  value       = var.enable_cyberark_scanner ? module.cyberark_scanner[0].scanner_secret_arn : null
  sensitive   = true
}
