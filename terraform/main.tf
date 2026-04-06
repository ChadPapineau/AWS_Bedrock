terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = merge(var.tags, {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    })
  }
}

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

locals {
  account_id  = data.aws_caller_identity.current.account_id
  region      = data.aws_region.current.name
  name_prefix = "${var.project_name}-${var.environment}"
}

# --- ECR Repository for Agent Container ---

resource "aws_ecr_repository" "agent" {
  name                 = "${local.name_prefix}-agent"
  image_tag_mutability = "MUTABLE"
  force_delete         = var.environment == "dev"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }
}

# --- Modules ---

module "cognito" {
  source = "./modules/cognito"

  name_prefix = local.name_prefix
}

module "agentcore_memory" {
  source = "./modules/agentcore_memory"

  name_prefix = local.name_prefix
  region      = local.region
}

module "agentcore_gateway" {
  source = "./modules/agentcore_gateway"

  name_prefix              = local.name_prefix
  region                   = local.region
  account_id               = local.account_id
  tavily_api_key_secret_arn = var.tavily_api_key_secret_arn
  github_token_secret_arn  = var.github_token_secret_arn
}

module "agentcore_runtime" {
  source = "./modules/agentcore_runtime"

  name_prefix             = local.name_prefix
  region                  = local.region
  account_id              = local.account_id
  ecr_repository_url      = aws_ecr_repository.agent.repository_url
  ecr_image_tag           = var.ecr_image_tag
  bedrock_model_id        = var.bedrock_model_id
  memory_mb               = var.runtime_memory_mb
  timeout_seconds         = var.runtime_timeout_seconds
  cognito_user_pool_id    = module.cognito.user_pool_id
  agentcore_memory_id     = module.agentcore_memory.memory_id
  gateway_endpoint        = module.agentcore_gateway.gateway_endpoint
}

# --- CyberArk Secure AI Agents Scanner ---

module "cyberark_scanner" {
  source = "./modules/cyberark_scanner"
  count  = var.enable_cyberark_scanner ? 1 : 0

  name_prefix               = local.name_prefix
  region                    = local.region
  cyberark_tenant_name      = var.cyberark_tenant_name
  cyberark_service_user     = var.cyberark_service_user
  cyberark_service_password = var.cyberark_service_password
  scanner_bucket_name       = var.cyberark_scanner_bucket
  scanner_artifacts_path    = var.cyberark_scanner_artifacts_path
}
