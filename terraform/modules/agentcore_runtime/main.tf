variable "name_prefix" {
  type = string
}

variable "region" {
  type = string
}

variable "account_id" {
  type = string
}

variable "ecr_repository_url" {
  type = string
}

variable "ecr_image_tag" {
  type    = string
  default = "latest"
}

variable "bedrock_model_id" {
  type = string
}

variable "memory_mb" {
  type    = number
  default = 1024
}

variable "timeout_seconds" {
  type    = number
  default = 300
}

variable "cognito_user_pool_id" {
  type = string
}

variable "agentcore_memory_id" {
  type = string
}

variable "gateway_endpoint" {
  type = string
}

# AgentCore Runtime deploys the agent container on serverless microVMs
# with per-session isolation. This module provisions the IAM role,
# the runtime configuration, and the CloudWatch log group.

resource "aws_iam_role" "runtime" {
  name = "${var.name_prefix}-runtime"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "bedrock.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "runtime_bedrock" {
  name = "${var.name_prefix}-runtime-bedrock"
  role = aws_iam_role.runtime.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream",
        ]
        Resource = "arn:aws:bedrock:${var.region}::foundation-model/*"
      },
      {
        Effect = "Allow"
        Action = [
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:GetAuthorizationToken",
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
        ]
        Resource = "${aws_cloudwatch_log_group.runtime.arn}:*"
      }
    ]
  })
}

resource "aws_cloudwatch_log_group" "runtime" {
  name              = "/agentcore/${var.name_prefix}"
  retention_in_days = 30
}

# The actual AgentCore Runtime resource is provisioned via the AgentCore CLI
# or API, since Terraform does not yet have a native aws_bedrockagentcore_runtime
# resource. This null_resource captures the deployment configuration for
# reference and can be extended with a local-exec provisioner.

resource "null_resource" "runtime_config" {
  triggers = {
    image_uri        = "${var.ecr_repository_url}:${var.ecr_image_tag}"
    model_id         = var.bedrock_model_id
    memory_mb        = var.memory_mb
    timeout_seconds  = var.timeout_seconds
    memory_id        = var.agentcore_memory_id
    gateway_endpoint = var.gateway_endpoint
  }
}

output "runtime_role_arn" {
  value = aws_iam_role.runtime.arn
}

output "runtime_endpoint" {
  description = "Placeholder -- actual endpoint is provisioned by AgentCore CLI after terraform apply"
  value       = "deploy-via-agentcore-cli"
}

output "log_group_name" {
  value = aws_cloudwatch_log_group.runtime.name
}
