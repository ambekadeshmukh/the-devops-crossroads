provider "aws" {
  region = var.aws_region
}

# Configure Terraform backend (optional - for state management)
terraform {
  backend "s3" {
    bucket = "my-email-templates-bucket"
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
}

# AWS Config Rules for automated remediation
module "config_rules" {
  source = "./modules/config_rules"
  
  depends_on = [module.access_analyzer]
}