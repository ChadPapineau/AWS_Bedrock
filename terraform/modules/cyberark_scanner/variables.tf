variable "name_prefix" {
  description = "Name prefix for all scanner resources"
  type        = string
}

variable "region" {
  description = "AWS region for scanner deployment. The scanner discovers agents across all regions."
  type        = string
}

variable "cyberark_tenant_name" {
  description = "CyberArk Identity tenant name (from Identity Administration > Account Settings > About)"
  type        = string
}

variable "cyberark_service_user" {
  description = "Login name of the CyberArk Identity service user created for scanner authentication"
  type        = string
}

variable "cyberark_service_password" {
  description = "Password for the CyberArk Identity service user"
  type        = string
  sensitive   = true
}

variable "scanner_bucket_name" {
  description = "S3 bucket name for scanner deployment artifacts. Must be globally unique. Leave empty to auto-generate."
  type        = string
  default     = ""
}

variable "scanner_schedule" {
  description = "Cron expression for scanner execution schedule (AWS Glue trigger format)"
  type        = string
  default     = "cron(0 */12 * * ? *)"
}

variable "scanner_artifacts_path" {
  description = "Local path to the downloaded CyberArk scanner package directory containing discovery.py and dependencies.zip"
  type        = string
  default     = ""
}

variable "cloudformation_stack_name" {
  description = "Name for the CyberArk scanner CloudFormation stack"
  type        = string
  default     = "cyberark-discovery"
}

variable "tags" {
  description = "Additional tags for scanner resources"
  type        = map(string)
  default     = {}
}
