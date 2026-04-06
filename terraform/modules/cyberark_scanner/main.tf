locals {
  bucket_name = var.scanner_bucket_name != "" ? var.scanner_bucket_name : "${var.name_prefix}-cyberark-scanner-${data.aws_caller_identity.current.account_id}"
}

data "aws_caller_identity" "current" {}

# --- S3 Bucket for Scanner Artifacts ---

resource "aws_s3_bucket" "scanner" {
  bucket        = local.bucket_name
  force_destroy = true

  tags = merge(var.tags, {
    Purpose = "CyberArk Secure AI Agents scanner artifacts"
  })
}

resource "aws_s3_bucket_versioning" "scanner" {
  bucket = aws_s3_bucket.scanner.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "scanner" {
  bucket = aws_s3_bucket.scanner.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "scanner" {
  bucket = aws_s3_bucket.scanner.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Upload scanner artifacts to S3 if local path is provided
resource "aws_s3_object" "discovery_script" {
  count  = var.scanner_artifacts_path != "" ? 1 : 0
  bucket = aws_s3_bucket.scanner.id
  key    = "cyberark-discovery/discovery.py"
  source = "${var.scanner_artifacts_path}/discovery.py"
  etag   = filemd5("${var.scanner_artifacts_path}/discovery.py")
}

resource "aws_s3_object" "dependencies" {
  count  = var.scanner_artifacts_path != "" ? 1 : 0
  bucket = aws_s3_bucket.scanner.id
  key    = "cyberark-discovery/dependencies.zip"
  source = "${var.scanner_artifacts_path}/dependencies.zip"
  etag   = filemd5("${var.scanner_artifacts_path}/dependencies.zip")
}

# --- Secrets Manager for CyberArk Service User Credentials ---

resource "aws_secretsmanager_secret" "cyberark_credentials" {
  name        = "${var.name_prefix}/cyberark-scanner-credentials"
  description = "CyberArk Identity service user credentials for the Secure AI Agents scanner"

  tags = merge(var.tags, {
    Purpose = "CyberArk scanner authentication"
  })
}

resource "aws_secretsmanager_secret_version" "cyberark_credentials" {
  secret_id = aws_secretsmanager_secret.cyberark_credentials.id

  secret_string = jsonencode({
    tenant_name      = var.cyberark_tenant_name
    service_user     = var.cyberark_service_user
    service_password = var.cyberark_service_password
  })
}

# --- IAM Role for Glue Scanner Job ---

resource "aws_iam_role" "scanner_glue" {
  name = "${var.name_prefix}-cyberark-scanner"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "glue.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

resource "aws_iam_role_policy" "scanner_permissions" {
  name = "${var.name_prefix}-scanner-permissions"
  role = aws_iam_role.scanner_glue.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "BedrockDiscovery"
        Effect = "Allow"
        Action = [
          "bedrock:Get*",
          "bedrock:List*",
          "bedrock-agentcore:Get*",
          "bedrock-agentcore:List*",
        ]
        Resource = "*"
      },
      {
        Sid    = "ScannerArtifacts"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket",
        ]
        Resource = [
          aws_s3_bucket.scanner.arn,
          "${aws_s3_bucket.scanner.arn}/*",
        ]
      },
      {
        Sid    = "ScannerSecrets"
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
        ]
        Resource = [
          aws_secretsmanager_secret.cyberark_credentials.arn,
        ]
      },
      {
        Sid    = "ScannerLogs"
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
        ]
        Resource = "arn:aws:logs:${var.region}:${data.aws_caller_identity.current.account_id}:log-group:/aws-glue/*"
      }
    ]
  })
}

# --- Glue Job for Scanner Execution ---

resource "aws_glue_job" "scanner" {
  name     = "${var.name_prefix}-cyberark-scanner"
  role_arn = aws_iam_role.scanner_glue.arn

  command {
    name            = "pythonshell"
    script_location = "s3://${aws_s3_bucket.scanner.id}/cyberark-discovery/discovery.py"
    python_version  = "3.9"
  }

  default_arguments = {
    "--extra-py-files"                 = "s3://${aws_s3_bucket.scanner.id}/cyberark-discovery/dependencies.zip"
    "--CYBERARK_SECRET_ARN"            = aws_secretsmanager_secret.cyberark_credentials.arn
    "--enable-continuous-cloudwatch-log" = "true"
    "--enable-metrics"                  = "true"
  }

  max_retries       = 1
  timeout           = 30
  glue_version      = "3.0"
  max_capacity      = 0.0625

  tags = merge(var.tags, {
    Purpose = "CyberArk Secure AI Agents discovery scanner"
  })
}

# --- Scheduled Trigger (every 12 hours by default) ---

resource "aws_glue_trigger" "scanner_schedule" {
  name     = "${var.name_prefix}-scanner-schedule"
  type     = "SCHEDULED"
  schedule = var.scanner_schedule
  enabled  = true

  actions {
    job_name = aws_glue_job.scanner.name
  }

  tags = var.tags
}

# --- On-Demand Trigger for Initial Scan ---

resource "aws_glue_trigger" "scanner_ondemand" {
  name    = "${var.name_prefix}-scanner-ondemand"
  type    = "ON_DEMAND"
  enabled = true

  actions {
    job_name = aws_glue_job.scanner.name
  }

  tags = var.tags
}
