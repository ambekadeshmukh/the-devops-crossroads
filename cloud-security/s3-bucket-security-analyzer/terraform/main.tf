provider "aws" {
  region = var.aws_region
}

# SNS Topic for alerts
resource "aws_sns_topic" "security_alerts" {
  name = "s3-security-alerts"
}

# SNS Topic Subscription
resource "aws_sns_topic_subscription" "email_subscription" {
  topic_arn = aws_sns_topic.security_alerts.arn
  protocol  = "email"
  endpoint  = var.notification_email
}

# IAM Role for Lambda
resource "aws_iam_role" "lambda_role" {
  name = "s3_security_analyzer_role"

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

# Lambda Basic Execution Policy
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Lambda S3 and SNS Policy
resource "aws_iam_policy" "lambda_s3_sns_policy" {
  name        = "s3_security_analyzer_policy"
  description = "Policy for S3 Security Analyzer Lambda"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:ListAllMyBuckets",
          "s3:GetBucketPublicAccessBlock",
          "s3:GetBucketEncryption",
          "s3:GetBucketLogging",
          "s3:GetBucketPolicy"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = "sns:Publish"
        Resource = aws_sns_topic.security_alerts.arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_s3_sns" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.lambda_s3_sns_policy.arn
}

# Lambda Function
resource "aws_lambda_function" "s3_security_analyzer" {
  filename      = "s3_security_analyzer.zip"
  function_name = "s3_security_analyzer"
  role          = aws_iam_role.lambda_role.arn
  handler       = "s3_security_analyzer.lambda_handler"
  runtime       = "python3.9"
  timeout       = 300

  environment {
    variables = {
      SNS_TOPIC_ARN = aws_sns_topic.security_alerts.arn
    }
  }
}

# CloudWatch Event Rule for scheduled execution
resource "aws_cloudwatch_event_rule" "daily_scan" {
  name                = "s3-security-daily-scan"
  description         = "Trigger S3 Security Analyzer daily"
  schedule_expression = "rate(1 day)"
}

# CloudWatch Event Target
resource "aws_cloudwatch_event_target" "scan_target" {
  rule      = aws_cloudwatch_event_rule.daily_scan.name
  target_id = "S3SecurityAnalyzer"
  arn       = aws_lambda_function.s3_security_analyzer.arn
}

# Permission for CloudWatch to invoke Lambda
resource "aws_lambda_permission" "allow_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.s3_security_analyzer.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_scan.arn
}