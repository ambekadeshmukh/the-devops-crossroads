output "dashboard_arn" {
  description = "ARN of the CloudWatch Dashboard"
  value       = aws_cloudwatch_dashboard.access_analyzer_dashboard.dashboard_arn
}

output "dashboard_name" {
  description = "Name of the CloudWatch Dashboard"
  value       = aws_cloudwatch_dashboard.access_analyzer_dashboard.dashboard_name
}