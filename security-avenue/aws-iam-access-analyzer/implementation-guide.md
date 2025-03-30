# AWS IAM Access Analyzer - Implementation Guide

## Project Overview
This project implements AWS IAM Access Analyzer to identify resources shared with external entities, monitors security findings using CloudWatch dashboards, and automates remediation using AWS Config rules.

**Core Topics:** AWS Security, IAM Governance, Security Automation
**Difficulty:** Intermediate
**Deployment Method:** Terraform

## Prerequisites
- AWS Account with Administrator access
- AWS CLI configured
- Terraform installed (v1.0+)
- Git for version control

## Implementation Steps

### 1. Project Setup

#### Directory Structure
```
security-avenue/aws-iam-access-analyzer/
├── README.md
├── architecture.png
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── modules/
│   │   ├── access_analyzer/
│   │   ├── cloudwatch_dashboard/
│   │   └── config_rules/
├── scripts/
│   └── remediation.py
└── docs/
    └── blog-post.md
```

#### Initialize the Repository
```bash
# Create the project directory
mkdir -p security-avenue/aws-iam-access-analyzer/terraform/modules/{access_analyzer,cloudwatch_dashboard,config_rules}
mkdir -p security-avenue/aws-iam-access-analyzer/{scripts,docs}
touch security-avenue/aws-iam-access-analyzer/README.md
```

### 2. Terraform Configuration for AWS IAM Access Analyzer

### Testing the Implementation

1. Deploy the infrastructure:
```bash
cd terraform
terraform init
terraform apply
```

2. Create a test bucket with public access:
```bash
# Create a test bucket
aws s3 mb s3://access-analyzer-test-bucket-$(date +%s)

# Disable Block Public Access
aws s3api put-public-access-block --bucket <YOUR-BUCKET-NAME> --public-access-block-configuration "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false"

# Add a public bucket policy
aws s3api put-bucket-policy --bucket <YOUR-BUCKET-NAME> --policy '{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::<YOUR-BUCKET-NAME>/*"
    }
  ]
}'
```

3. Monitor the results:
   - Check the CloudWatch dashboard for new findings
   - Verify that AWS Config detects the public bucket
   - Confirm that the SSM automation remediates the public access

#### Create the main Terraform files

**terraform/variables.tf**
```hcl
variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "analyzer_name" {
  description = "Name of the IAM Access Analyzer"
  type        = string
  default     = "account-analyzer"
}

variable "analyzer_type" {
  description = "Type of analyzer (ACCOUNT or ORGANIZATION)"
  type        = string
  default     = "ACCOUNT"
}

variable "finding_notification_enabled" {
  description = "Enable notifications for findings"
  type        = bool
  default     = true
}

variable "finding_notification_frequency" {
  description = "Frequency of finding notifications (FIFTEEN_MINUTES, ONE_HOUR, SIX_HOURS, DAILY)"
  type        = string
  default     = "DAILY"
}
```

**terraform/main.tf**
```hcl
provider "aws" {
  region = var.aws_region
}

# Configure Terraform backend (optional - for state management)
terraform {
  backend "s3" {
    bucket = "your-terraform-state-bucket"
    key    = "security-avenue/aws-iam-access-analyzer/terraform.tfstate"
    region = "us-east-1"
  }
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

# Create IAM Access Analyzer
module "access_analyzer" {
  source = "./modules/access_analyzer"
  
  analyzer_name                 = var.analyzer_name
  analyzer_type                 = var.analyzer_type
  finding_notification_enabled  = var.finding_notification_enabled
  finding_notification_frequency = var.finding_notification_frequency
}

# CloudWatch Dashboard for visualization
module "cloudwatch_dashboard" {
  source = "./modules/cloudwatch_dashboard"
  
  analyzer_name = module.access_analyzer.analyzer_name
  dashboard_name = "IAMAccessAnalyzerDashboard"
}

# AWS Config Rules for automated remediation
module "config_rules" {
  source = "./modules/config_rules"
  
  depends_on = [module.access_analyzer]
}
```

**terraform/outputs.tf**
```hcl
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
```

### 3. Module: IAM Access Analyzer

The Access Analyzer module sets up the analyzer and configures CloudWatch Events to capture findings.

**terraform/modules/access_analyzer/main.tf**
```hcl
resource "aws_accessanalyzer_analyzer" "analyzer" {
  analyzer_name = var.analyzer_name
  type          = var.analyzer_type
  
  tags = {
    Name        = var.analyzer_name
    Environment = "Production"
    Project     = "SecurityAvenue"
  }
}

# SNS Topic for notifications
resource "aws_sns_topic" "analyzer_notifications" {
  name = "access-analyzer-findings"
}

# CloudWatch Event Rule for Access Analyzer Findings
resource "aws_cloudwatch_event_rule" "analyzer_findings" {
  name        = "capture-access-analyzer-findings"
  description = "Capture IAM Access Analyzer Findings"

  event_pattern = jsonencode({
    "source": ["aws.access-analyzer"],
    "detail-type": ["Access Analyzer Finding"]
  })
}

# CloudWatch Event Target for SNS
resource "aws_cloudwatch_event_target" "sns" {
  rule      = aws_cloudwatch_event_rule.analyzer_findings.name
  target_id = "SendToSNS"
  arn       = aws_sns_topic.analyzer_notifications.arn
}
```

### 4. Module: CloudWatch Dashboard

The CloudWatch Dashboard module creates a dashboard to visualize Access Analyzer findings.

**terraform/modules/cloudwatch_dashboard/main.tf**
```hcl
resource "aws_cloudwatch_dashboard" "access_analyzer_dashboard" {
  dashboard_name = var.dashboard_name

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/AccessAnalyzer", "TotalFindings", "AnalyzerName", var.analyzer_name]
          ]
          region  = "us-east-1"
          title   = "Total Findings"
          period  = 86400
        }
      },
      {
        type   = "log"
        x      = 0
        y      = 9
        width  = 24
        height = 6
        properties = {
          query = "SOURCE '/aws/events/access-analyzer' | fields @timestamp, detail.findingDetails, detail.resource, detail.status, detail.resourceType | sort @timestamp desc | limit 20"
          region  = "us-east-1"
          title   = "Recent Access Analyzer Findings"
          view    = "table"
        }
      }
    ]
  })
}
```

### 5. Module: AWS Config Rules

The Config Rules module sets up automated remediation for security findings.

**terraform/modules/config_rules/main.tf**
```hcl
# AWS Config Recorder and S3 bucket for storing configuration history
resource "aws_config_configuration_recorder" "recorder" {
  name     = "access-analyzer-recorder"
  role_arn = aws_iam_role.config_role.arn

  recording_group {
    all_supported = true
    include_global_resources = true
  }
}

# Config Rules for security checks
resource "aws_config_config_rule" "s3_bucket_public_access" {
  name        = "s3-bucket-public-access-prohibited"
  description = "Checks if Amazon S3 buckets have public access enabled"

  source {
    owner             = "AWS"
    source_identifier = "S3_BUCKET_PUBLIC_READ_PROHIBITED"
  }
}

# SSM Automation for remediation
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
}
```

**terraform/modules/access_analyzer/main.tf**
```hcl
resource "aws_accessanalyzer_analyzer" "analyzer" {
  analyzer_name = var.analyzer_name
  type          = var.analyzer_type
  
  tags = {
    Name        = var.analyzer_name
    Environment = "Production"
    Project     = "SecurityAvenue"
  }
}

# SNS Topic for notifications
resource "aws_sns_topic" "analyzer_notifications" {
  name = "access-analyzer-findings"
  
  tags = {
    Name        = "AccessAnalyzerNotifications"
    Environment = "Production"
    Project     = "SecurityAvenue"
  }
}

# Configure notification for analyzer findings
resource "aws_accessanalyzer_archive_rule" "critical_findings" {
  analyzer_name = aws_accessanalyzer_analyzer.analyzer.analyzer_name
  rule_name     = "critical-findings"
  filter {
    property = "resourceType"
    eq       = ["AWS::S3::Bucket", "AWS::IAM::Role"]
  }
  filter {
    property = "findingType"
    eq       = ["ExternalAccess"]
  }
}

# CloudWatch Event Rule for Access Analyzer Findings
resource "aws_cloudwatch_event_rule" "analyzer_findings" {
  name        = "capture-access-analyzer-findings"
  description = "Capture IAM Access Analyzer Findings"

  event_pattern = jsonencode({
    "source" : ["aws.access-analyzer"],
    "detail-type" : ["Access Analyzer Finding"]
  })
}

# CloudWatch Event Target for SNS
resource "aws_cloudwatch_event_target" "sns" {
  rule      = aws_cloudwatch_event_rule.analyzer_findings.name
  target_id = "SendToSNS"
  arn       = aws_sns_topic.analyzer_notifications.arn
}

# Configure finding notification
resource "aws_accessanalyzer_analyzer_configuration" "example" {
  count = var.finding_notification_enabled ? 1 : 0
  
  analyzer_name = aws_accessanalyzer_analyzer.analyzer.analyzer_name

  finding_notification_configuration {
    enabled = var.finding_notification_enabled
    frequency = var.finding_notification_frequency
  }
}
```

**terraform/modules/access_analyzer/variables.tf**
```hcl
variable "analyzer_name" {
  description = "Name of the IAM Access Analyzer"
  type        = string
}

variable "analyzer_type" {
  description = "Type of analyzer (ACCOUNT or ORGANIZATION)"
  type        = string
}

variable "finding_notification_enabled" {
  description = "Enable notifications for findings"
  type        = bool
}

variable "finding_notification_frequency" {
  description = "Frequency of finding notifications"
  type        = string
}
```

**terraform/modules/access_analyzer/outputs.tf**
```hcl
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
```

### 4. Module: CloudWatch Dashboard

**terraform/modules/cloudwatch_dashboard/main.tf**
```hcl
resource "aws_cloudwatch_dashboard" "access_analyzer_dashboard" {
  dashboard_name = var.dashboard_name
  
  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/AccessAnalyzer", "FindingsCount", "AnalyzerName", var.analyzer_name, "FindingType", "ExternalAccess", { "stat" = "Sum" }]
          ]
          view    = "timeSeries"
          stacked = false
          region  = "us-east-1"
          title   = "External Access Findings"
          period  = 86400
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/AccessAnalyzer", "FindingsCount", "AnalyzerName", var.analyzer_name, "ResourceType", "AWS::S3::Bucket", { "stat" = "Sum" }],
            ["AWS/AccessAnalyzer", "FindingsCount", "AnalyzerName", var.analyzer_name, "ResourceType", "AWS::IAM::Role", { "stat" = "Sum" }],
            ["AWS/AccessAnalyzer", "FindingsCount", "AnalyzerName", var.analyzer_name, "ResourceType", "AWS::KMS::Key", { "stat" = "Sum" }],
            ["AWS/AccessAnalyzer", "FindingsCount", "AnalyzerName", var.analyzer_name, "ResourceType", "AWS::Lambda::Function", { "stat" = "Sum" }],
            ["AWS/AccessAnalyzer", "FindingsCount", "AnalyzerName", var.analyzer_name, "ResourceType", "AWS::SQS::Queue", { "stat" = "Sum" }]
          ]
          view    = "timeSeries"
          stacked = false
          region  = "us-east-1"
          title   = "Findings by Resource Type"
          period  = 86400
        }
      },
      {
        type   = "text"
        x      = 0
        y      = 6
        width  = 24
        height = 3
        properties = {
          markdown = "# IAM Access Analyzer Findings\nThis dashboard shows findings from AWS IAM Access Analyzer, highlighting potential security risks in your AWS environment."
        }
      },
      {
        type   = "log"
        x      = 0
        y      = 9
        width  = 24
        height = 6
        properties = {
          query = "SOURCE '/aws/events/access-analyzer' | fields @timestamp, detail.findingDetails, detail.resource, detail.status, detail.resourceType | sort @timestamp desc | limit 20"
          region  = "us-east-1"
          title   = "Recent Access Analyzer Findings"
          view    = "table"
        }
      }
    ]
  })
}
```

**terraform/modules/cloudwatch_dashboard/variables.tf**
```hcl
variable "dashboard_name" {
  description = "Name of the CloudWatch Dashboard"
  type        = string
}

variable "analyzer_name" {
  description = "Name of the IAM Access Analyzer to monitor"
  type        = string
}
```

**terraform/modules/cloudwatch_dashboard/outputs.tf**
```hcl
output "dashboard_arn" {
  description = "ARN of the CloudWatch Dashboard"
  value       = aws_cloudwatch_dashboard.access_analyzer_dashboard.dashboard_arn
}

output "dashboard_name" {
  description = "Name of the CloudWatch Dashboard"
  value       = aws_cloudwatch_dashboard.access_analyzer_dashboard.dashboard_name
}
```

### 5. Module: AWS Config Rules for Remediation

**terraform/modules/config_rules/main.tf**
```hcl
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
  filename      = "lambda_function.zip"
  function_name = "access-analyzer-remediation"
  role          = aws_iam_role.remediation_role.arn
  handler       = "index.handler"
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
resource "aws_config_remediation_configuration" "s3_remediation" {
  config_rule_name = aws_config_config_rule.s3_bucket_public_access.name
  target_type      = "SSM_DOCUMENT"
  target_id        = "AWS-DisableS3BucketPublicReadWrite"
  
  parameter {
    name         = "AutomationAssumeRole"
    value        = aws_iam_role.remediation_role.arn
    resource_value = "RESOURCE_ID"
  }
  
  parameter {
    name         = "S3BucketName"
    resource_value = "RESOURCE_ID"
  }
  
  automatic = true
  maximum_automatic_attempts = 3
  retry_attempt_seconds = 60
  
  depends_on = [aws_config_config_rule.s3_bucket_public_access]
}

data "aws_caller_identity" "current" {}
```

**terraform/modules/config_rules/variables.tf**
```hcl
# No variables required for this module in this example
```

**terraform/modules/config_rules/outputs.tf**
```hcl
output "config_rule_arns" {
  description = "ARNs of the created AWS Config Rules"
  value = [
    aws_config_config_rule.s3_bucket_public_access.arn,
    aws_config_config_rule.iam_root_access_key.arn,
    aws_config_config_rule.iam_user_mfa.arn
  ]
}
```

### 6. Lambda Function for Custom Remediation

Create a Python script that will be used in the Lambda function for advanced remediation:

**scripts/remediation.py**
```python
import boto3
import json
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

access_analyzer = boto3.client('accessanalyzer')
s3 = boto3.client('s3')
iam = boto3.client('iam')

def handler(event, context):
    """
    Lambda function to automatically remediate IAM Access Analyzer findings
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    # Get finding details from event
    if 'detail' in event and 'resourceType' in event['detail']:
        finding_id = event['detail']['id']
        resource_type = event['detail']['resourceType']
        resource_arn = event['detail']['resource']
        
        logger.info(f"Processing finding {finding_id} for {resource_type}: {resource_arn}")
        
        # Get full finding details
        finding = access_analyzer.get_finding(
            analyzerId=event['detail']['analyzerId'],
            id=finding_id
        )
        
        # Remediate based on resource type
        if resource_type == 'AWS::S3::Bucket':
            remediate_s3_bucket(resource_arn, finding)
        elif resource_type == 'AWS::IAM::Role':
            remediate_iam_role(resource_arn, finding)
        else:
            logger.info(f"No automated remediation available for {resource_type}")
            
        return {
            'statusCode': 200,
            'body': json.dumps(f'Successfully processed finding {finding_id}')
        }
    else:
        logger.error("Invalid event structure")
        return {
            'statusCode': 400,
            'body': json.dumps('Invalid event structure')
        }

def remediate_s3_bucket(bucket_arn, finding):
    """
    Remediate S3 bucket with public access
    """
    bucket_name = bucket_arn.split(':')[-1]
    logger.info(f"Remediating S3 bucket: {bucket_name}")
    
    try:
        # Block public access
        s3.put_public_access_block(
            Bucket=bucket_name,
            PublicAccessBlockConfiguration={
                'BlockPublicAcls': True,
                'IgnorePublicAcls': True,
                'BlockPublicPolicy': True,
                'RestrictPublicBuckets': True
            }
        )
        logger.info(f"Successfully blocked public access for bucket {bucket_name}")
        
        # Archive the finding after remediation
        access_analyzer.update_findings(
            analyzerArn=finding['analyzerId'],
            ids=[finding['id']],
            status='ARCHIVED'
        )
        logger.info(f"Successfully archived finding {finding['id']}")
        
    except Exception as e:
        logger.error(f"Error remediating S3 bucket {bucket_name}: {str(e)}")
        raise

def remediate_iam_role(role_arn, finding):
    """
    Remediate IAM role with external access
    """
    role_name = role_arn.split('/')[-1]
    logger.info(f"Remediating IAM role: {role_name}")
    
    try:
        # Get current trust policy
        role = iam.get_role(RoleName=role_name)
        trust_policy = json.loads(role['Role']['AssumeRolePolicyDocument'])
        
        # Analyze and modify trust policy
        modified = False
        if 'Statement' in trust_policy:
            for statement in trust_policy['Statement']:
                if 'Principal' in statement and 'AWS' in statement['Principal']:
                    principal = statement['Principal']['AWS']
                    
                    # If principal is a list, filter out external accounts
                    if isinstance(principal, list):
                        account_id = boto3.client('sts').get_caller_identity()['Account']
                        filtered_principals = [p for p in principal if account_id in p]
                        
                        if len(filtered_principals) != len(principal):
                            statement['Principal']['AWS'] = filtered_principals
                            modified = True
                    
                    # If principal is a string and refers to external account
                    elif isinstance(principal, str) and not principal.startswith(f"arn:aws:iam::{boto3.client('sts').get_caller_identity()['Account']}"):
                        # This is potentially risky, so log it and don't automatically modify
                        logger.warning(f"External principal found in role {role_name}: {principal}")
                        logger.warning("Not automatically removing as this could break functionality")
        
        # If we've modified the policy, update it
        if modified:
            iam.update_assume_role_policy(
                RoleName=role_name,
                PolicyDocument=json.dumps(trust_policy)
            )
            logger.info(f"Successfully updated trust policy for role {role_name}")
            
            # Archive the finding after remediation
            access_analyzer.update_findings(
                analyzerArn=finding['analyzerId'],
                ids=[finding['id']],
                status='ARCHIVED'
            )
            logger.info(f"Successfully archived finding {finding['id']}")
        else:
            logger.info(f"No changes needed for role {role_name} or potentially risky to automatically remediate")
        
    except Exception as e:
        logger.error(f"Error remediating IAM role {role_name}: {str(e)}")
        raise
```
