# Enable AWS Config if not already enabled
resource "aws_config_configuration_recorder" "recorder" {
  name     = "access-analyzer-recorder"
  role_arn = aws_iam_role.config_role.arn
  
  recording_group {
    all_supported                 = true
    include_global_resource_types = true
  }
}

resource "aws_config_configuration_recorder_status" "recorder_status" {
  name       = aws_config_configuration_recorder.recorder.name
  is_enabled = true
  depends_on = [aws_config_delivery_channel.delivery_channel]
}

resource "aws_config_delivery_channel" "delivery_channel" {
  name           = "access-analyzer-delivery-channel"
  s3_bucket_name = aws_s3_bucket.config_bucket.bucket
  
  depends_on = [aws_config_configuration_recorder.recorder]
}

# S3 bucket for AWS Config
resource "aws_s3_bucket" "config_bucket" {
  bucket = "config-bucket-${data.aws_caller_identity.current.account_id}"
  
  tags = {
    Name        = "AWSConfigBucket"
    Environment = "Production"
    Project     = "SecurityAvenue"
  }
}

resource "aws_s3_bucket_policy" "config_bucket_policy" {
  bucket = aws_s3_bucket.config_bucket.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AWSConfigBucketPermissionsCheck"
        Effect = "Allow"
        Principal = {
          Service = "config.amazonaws.com"
        }
        Action   = "s3:GetBucketAcl"
        Resource = "arn:aws:s3:::${aws_s3_bucket.config_bucket.bucket}"
      },
      {
        Sid    = "AWSConfigBucketDelivery"
        Effect = "Allow"
        Principal = {
          Service = "config.amazonaws.com"
        }
        Action   = "s3:PutObject"
        Resource = "arn:aws:s3:::${aws_s3_bucket.config_bucket.bucket}/AWSLogs/${data.aws_caller_identity.current.account_id}/Config/*"
        Condition = {
          StringEquals = {
            "s3:x-amz-acl" = "bucket-owner-full-control"
          }
        }
      }
    ]
  })
}

# IAM role for AWS Config
resource "aws_iam_role" "config_role" {
  name = "aws-config-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "config.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "config_policy_attachment" {
  role       = aws_iam_role.config_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWS_ConfigRole"
}

# IAM role for Lambda remediation
resource "aws_iam_role" "remediation_role" {
  name = "remediation-lambda-role"
  
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

resource "aws_iam_policy" "remediation_policy" {
  name        = "remediation-lambda-policy"
  description = "Policy for IAM Access Analyzer remediation Lambda"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutBucketPublicAccessBlock",
          "s3:PutBucketPolicy",
          "iam:UpdateAssumeRolePolicy",
          "accessanalyzer:*"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "remediation_policy_attachment" {
  role       = aws_iam_role.remediation_role.name
  policy_arn = aws_iam_policy.remediation_policy.arn
}

# Lambda function for remediation
resource "aws_lambda_function" "remediation_lambda" {
  filename      = "${path.module}/lambda_function.zip"
  function_name = "access-analyzer-remediation"
  role          = aws_iam_role.remediation_role.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.9"
  timeout       = 300
  
  # This requires you to create and zip the Lambda function
  # You can use a null_resource to do this or create it separately
  
  tags = {
    Name        = "AccessAnalyzerRemediation"
    Environment = "Production"
    Project     = "SecurityAvenue"
  }
}

# Config Rules
resource "aws_config_config_rule" "s3_bucket_public_access" {
  name        = "s3-bucket-public-access-prohibited"
  description = "Checks if Amazon S3 buckets have public access enabled"
  
  source {
    owner             = "AWS"
    source_identifier = "S3_BUCKET_PUBLIC_READ_PROHIBITED"
  }
  
  depends_on = [aws_config_configuration_recorder.recorder]
}

resource "aws_config_config_rule" "iam_root_access_key" {
  name        = "iam-root-access-key-check"
  description = "Checks if the root user access key is available"
  
  source {
    owner             = "AWS"
    source_identifier = "IAM_ROOT_ACCESS_KEY_CHECK"
  }
  
  depends_on = [aws_config_configuration_recorder.recorder]
}

resource "aws_config_config_rule" "iam_user_mfa" {
  name        = "iam-user-mfa-enabled"
  description = "Checks if MFA is enabled for all IAM users"
  
  source {
    owner             = "AWS"
    source_identifier = "IAM_USER_MFA_ENABLED"
  }
  
  depends_on = [aws_config_configuration_recorder.recorder]
}

# Remediation for S3 public access
# Configure AWS Systems Manager association for remediation
resource "aws_ssm_association" "s3_remediation" {
  name = "AWS-DisableS3BucketPublicReadWrite"
  
  automation_target_parameter_name = "S3BucketName"
  
  targets {
    key    = "tag:Name"
    values = [aws_s3_bucket.config_bucket.id]
  }
  
  parameters = {
    AutomationAssumeRole = aws_iam_role.remediation_role.arn
    S3BucketName = aws_s3_bucket.config_bucket.id
  }
  
  depends_on = [aws_config_config_rule.s3_bucket_public_access]
}

data "aws_caller_identity" "current" {}