variable "name_prefix" {
  type = string
}

variable "region" {
  type = string
}

variable "account_id" {
  type = string
}

variable "tavily_api_key_secret_arn" {
  type    = string
  default = ""
}

variable "github_token_secret_arn" {
  type    = string
  default = ""
}

# AgentCore Gateway transforms external APIs into MCP-compatible endpoints.
# This module creates a Lambda function that acts as the MCP tool server
# and an API Gateway (HTTP API) that fronts it.

data "archive_file" "gateway_lambda" {
  type        = "zip"
  output_path = "${path.module}/gateway_lambda.zip"

  source {
    content  = file("${path.module}/lambda_handler.py")
    filename = "handler.py"
  }
}

resource "aws_iam_role" "gateway_lambda" {
  name = "${var.name_prefix}-gateway-lambda"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "gateway_lambda_basic" {
  role       = aws_iam_role.gateway_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "gateway_secrets" {
  count = (var.tavily_api_key_secret_arn != "" || var.github_token_secret_arn != "") ? 1 : 0
  name  = "${var.name_prefix}-gateway-secrets"
  role  = aws_iam_role.gateway_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
        ]
        Resource = compact([
          var.tavily_api_key_secret_arn,
          var.github_token_secret_arn,
        ])
      }
    ]
  })
}

resource "aws_lambda_function" "gateway" {
  function_name    = "${var.name_prefix}-gateway"
  role             = aws_iam_role.gateway_lambda.arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.11"
  timeout          = 60
  memory_size      = 256
  filename         = data.archive_file.gateway_lambda.output_path
  source_code_hash = data.archive_file.gateway_lambda.output_base64sha256

  environment {
    variables = {
      TAVILY_API_KEY_SECRET_ARN = var.tavily_api_key_secret_arn
      GITHUB_TOKEN_SECRET_ARN  = var.github_token_secret_arn
    }
  }
}

resource "aws_apigatewayv2_api" "gateway" {
  name          = "${var.name_prefix}-gateway"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_integration" "gateway" {
  api_id                 = aws_apigatewayv2_api.gateway.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.gateway.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "gateway" {
  api_id    = aws_apigatewayv2_api.gateway.id
  route_key = "POST /mcp"
  target    = "integrations/${aws_apigatewayv2_integration.gateway.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.gateway.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_lambda_permission" "gateway" {
  statement_id  = "AllowAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.gateway.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.gateway.execution_arn}/*"
}

output "gateway_endpoint" {
  value = aws_apigatewayv2_api.gateway.api_endpoint
}

output "gateway_lambda_arn" {
  value = aws_lambda_function.gateway.arn
}
