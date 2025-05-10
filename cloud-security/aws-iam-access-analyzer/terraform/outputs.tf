output "access_analyzer_arn" {
  description = "ARN of the created IAM Access Analyzer"
  value       = module.access_analyzer.analyzer_arn
}

output "cloudwatch_dashboard_arn" {
  description = "ARN of the CloudWatch Dashboard"
  value       = module.cloudwatch_dashboard.dashboard_arn
}

output "config_rules_arns" {
  description = "ARNs of the AWS Config Rules"
  value       = module.config_rules.config_rule_arns
}