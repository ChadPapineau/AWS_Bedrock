output "scanner_bucket_name" {
  description = "S3 bucket name for scanner artifacts"
  value       = aws_s3_bucket.scanner.id
}

output "scanner_bucket_arn" {
  description = "S3 bucket ARN"
  value       = aws_s3_bucket.scanner.arn
}

output "scanner_secret_arn" {
  description = "Secrets Manager ARN storing CyberArk service user credentials"
  value       = aws_secretsmanager_secret.cyberark_credentials.arn
}

output "scanner_glue_job_name" {
  description = "Glue job name for the CyberArk scanner"
  value       = aws_glue_job.scanner.name
}

output "scanner_role_arn" {
  description = "IAM role ARN used by the scanner Glue job"
  value       = aws_iam_role.scanner_glue.arn
}
