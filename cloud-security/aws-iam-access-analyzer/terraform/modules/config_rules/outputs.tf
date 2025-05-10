output "config_rule_arns" {
  description = "ARNs of the created AWS Config Rules"
  value = [
    aws_config_config_rule.s3_bucket_public_access.arn,
    aws_config_config_rule.iam_root_access_key.arn,
    aws_config_config_rule.iam_user_mfa.arn
  ]
}