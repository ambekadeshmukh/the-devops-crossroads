output "lambda_function_name" {
  value = aws_lambda_function.s3_security_analyzer.function_name
}

output "sns_topic_arn" {
  value = aws_sns_topic.security_alerts.arn
}