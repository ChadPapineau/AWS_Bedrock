variable "name_prefix" {
  type = string
}

variable "region" {
  type = string
}

# AgentCore Memory provides both short-term (session) and long-term
# (cross-session) context persistence. This module provisions the
# underlying DynamoDB table that backs the memory store, along with
# the IAM role the runtime uses to read/write memory.

resource "aws_dynamodb_table" "agent_memory" {
  name         = "${var.name_prefix}-memory"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "pk"
  range_key    = "sk"

  attribute {
    name = "pk"
    type = "S"
  }

  attribute {
    name = "sk"
    type = "S"
  }

  attribute {
    name = "agent_id"
    type = "S"
  }

  global_secondary_index {
    name            = "agent-index"
    hash_key        = "agent_id"
    range_key       = "sk"
    projection_type = "ALL"
  }

  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }
}

resource "aws_iam_role" "memory_access" {
  name = "${var.name_prefix}-memory-access"

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

resource "aws_iam_role_policy" "memory_access" {
  name = "${var.name_prefix}-memory-policy"
  role = aws_iam_role.memory_access.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
        ]
        Resource = [
          aws_dynamodb_table.agent_memory.arn,
          "${aws_dynamodb_table.agent_memory.arn}/index/*",
        ]
      }
    ]
  })
}

output "memory_id" {
  value = aws_dynamodb_table.agent_memory.id
}

output "memory_table_arn" {
  value = aws_dynamodb_table.agent_memory.arn
}

output "memory_access_role_arn" {
  value = aws_iam_role.memory_access.arn
}
