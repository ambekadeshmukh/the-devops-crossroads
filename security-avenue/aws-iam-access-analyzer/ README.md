# AWS IAM Access Analyzer Project

> Part of the Security Avenue in the-devops-crossroads repository

## Overview

This project implements AWS IAM Access Analyzer to identify resources shared with external entities, monitors security findings using CloudWatch dashboards, and automates remediation using AWS Config rules.

## Features

- **IAM Access Analyzer Deployment**: Automatically detect overly permissive policies across your AWS account or organization
- **CloudWatch Dashboard**: Visualize security findings and monitor trends
- **Automated Remediation**: Implement AWS Config rules and Lambda functions to automatically remediate common issues
- **Notification System**: Get alerts for critical findings via SNS

## Architecture

![Architecture Diagram](./architecture.png)

## Prerequisites

- AWS Account with Administrator access
- AWS CLI configured
- Terraform installed (v1.0+)
- Git for version control

## Deployment

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/the-devops-crossroads.git
   cd the-devops-crossroads/security-avenue/aws-iam-access-analyzer
   ```

2. Update Terraform variables in `terraform/variables.tf` if needed

3. Initialize and apply Terraform:
   ```bash
   cd terraform
   terraform init
   terraform plan
   terraform apply
   ```

4. Verify the deployment:
   - Check IAM Access Analyzer in AWS Console
   - View the CloudWatch Dashboard
   - Verify AWS Config rules are enabled

## Understanding IAM Access Analyzer Findings

IAM Access Analyzer findings indicate resources that are accessible from outside your AWS account. Common findings include:

- **S3 Buckets**: Public access or access from other AWS accounts
- **IAM Roles**: Trust relationships with external principals
- **KMS Keys**: Key policies allowing cross-account access
- **Lambda Functions**: Resource-based policies with external access

## Remediation Strategies

This project provides two remediation approaches:

1. **Automated remediation** via AWS Config rules for common issues
2. **Semi-automated remediation** via Lambda functions for more complex scenarios

For production environments, always review automated remediation actions carefully.

## Maintenance

- Regularly check the CloudWatch Dashboard for new findings
- Update the Lambda remediation function as needed
- Review AWS Config rules for effectiveness

## References

- [AWS IAM Access Analyzer Documentation](https://docs.aws.amazon.com/IAM/latest/UserGuide/what-is-access-analyzer.html)
- [Terraform AWS Provider Documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [AWS Security Blog - IAM Access Analyzer](https://aws.amazon.com/blogs/security/identify-unintended-resource-access-aws-identity-access-analyzer/)