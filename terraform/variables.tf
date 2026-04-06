variable "project_name" {
  description = "Name prefix for all resources"
  type        = string
  default     = "agentcore-swarm"
}

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "bedrock_model_id" {
  description = "Bedrock model ID for the agents"
  type        = string
  default     = "us.anthropic.claude-3-5-sonnet-20241022-v2:0"
}

variable "runtime_memory_mb" {
  description = "Memory allocation for the AgentCore runtime (MB)"
  type        = number
  default     = 1024
}

variable "runtime_timeout_seconds" {
  description = "Timeout for agent runtime invocations (seconds)"
  type        = number
  default     = 300
}

variable "ecr_image_tag" {
  description = "Docker image tag for the agent container in ECR"
  type        = string
  default     = "latest"
}

variable "tavily_api_key_secret_arn" {
  description = "ARN of the Secrets Manager secret containing the Tavily API key"
  type        = string
  default     = ""
}

variable "github_token_secret_arn" {
  description = "ARN of the Secrets Manager secret containing the GitHub token"
  type        = string
  default     = ""
}

# --- CyberArk Secure AI Agents ---

variable "enable_cyberark_scanner" {
  description = "Whether to deploy the CyberArk Secure AI Agents scanner"
  type        = bool
  default     = false
}

variable "cyberark_tenant_name" {
  description = "CyberArk Identity tenant name"
  type        = string
  default     = ""
}

variable "cyberark_service_user" {
  description = "CyberArk Identity service user login name for scanner authentication"
  type        = string
  default     = ""
}

variable "cyberark_service_password" {
  description = "CyberArk Identity service user password"
  type        = string
  default     = ""
  sensitive   = true
}

variable "cyberark_scanner_bucket" {
  description = "S3 bucket name for CyberArk scanner artifacts (auto-generated if empty)"
  type        = string
  default     = ""
}

variable "cyberark_scanner_artifacts_path" {
  description = "Local path to the downloaded CyberArk scanner package"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default     = {}
}
