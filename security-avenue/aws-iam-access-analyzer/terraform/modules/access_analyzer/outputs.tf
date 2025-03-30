output "analyzer_name" {
  description = "Name of the created IAM Access Analyzer"
  value       = aws_accessanalyzer_analyzer.analyzer.analyzer_name
}

output "analyzer_arn" {
  description = "ARN of the created IAM Access Analyzer"
  value       = aws_accessanalyzer_analyzer.analyzer.arn
}

output "sns_topic_arn" {
  description = "ARN of the SNS topic for findings notifications"
  value       = aws_sns_topic.analyzer_notifications.arn
}