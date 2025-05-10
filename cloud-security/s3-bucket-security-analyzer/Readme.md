# S3 Bucket Security Analyzer

![s3-architecture-diagram](https://github.com/user-attachments/assets/4f3dc1e7-4339-4972-8279-5b561ee67895)


## Project Description

The S3 Bucket Security Analyzer is an automated AWS security tool that continuously monitors your S3 buckets for common security misconfigurations. It helps you maintain security best practices by detecting issues such as:

- Public access settings that could expose your data
- Missing encryption configurations
- Absent or insufficient logging
- Overly permissive bucket policies

When issues are detected, the tool sends detailed alerts via Amazon SNS, allowing you to quickly identify and remediate security vulnerabilities before they can be exploited.

## Features

- **Automated Scanning**: Runs daily (or on a schedule you define) to check all S3 buckets in your AWS account
- **Comprehensive Checks**: Validates multiple security configurations against best practices
- **Detailed Notifications**: Provides clear information about detected issues and their severity
- **Serverless Architecture**: Leverages AWS Lambda for cost-effective, scalable operation
- **Easy Deployment**: Ready-to-use CloudFormation and Terraform templates

## Architecture

The solution uses a serverless architecture with the following components:

- **AWS Lambda**: Executes the security scanning logic on a schedule
- **Amazon S3**: The target resources being scanned for security issues
- **Amazon SNS**: Delivers security alerts when issues are found
- **CloudWatch Events**: Triggers the Lambda function on a schedule
- **IAM Role**: Provides the necessary permissions for the Lambda function

## Setup Instructions

### Prerequisites

- AWS CLI installed and configured with appropriate permissions
- (If using Terraform) Terraform installed

### Option 1: Deployment Using CloudFormation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/the-devops-crossroads.git
   cd s3-bucket-security-analyzer
   ```

2. Deploy the CloudFormation stack:
   ```bash
   aws cloudformation create-stack \
     --stack-name s3-security-analyzer \
     --template-body file://cloudformation/template.yaml \
     --parameters ParameterKey=NotificationEmail,ParameterValue=your-email@example.com \
     --capabilities CAPABILITY_IAM
   ```

3. Confirm the SNS subscription by clicking the link in the email you receive.

### Option 2: Deployment Using Terraform

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/s3-bucket-security-analyzer.git
   cd s3-bucket-security-analyzer/terraform
   ```

2. Initialize Terraform:
   ```bash
   terraform init
   ```

3. Review and customize the configuration:
   ```bash
   # Edit terraform.tfvars with your specific settings
   nano terraform.tfvars
   ```

4. Deploy the infrastructure:
   ```bash
   terraform apply
   ```

5. Confirm the SNS subscription by clicking the link in the email you receive.

## Usage Instructions

### Viewing Scan Results

Scan results are sent to the email address you provided during setup. Each notification includes:

- The name of the affected S3 bucket
- A list of detected security issues
- Timestamps for when the issues were detected

### Manual Scan Execution

You can trigger a scan manually using the AWS CLI:

```bash
aws lambda invoke \
  --function-name s3-security-analyzer \
  --payload '{}' \
  output.txt
```

### Customizing the Analyzer

You can customize the analyzer by modifying the Lambda function code. For example:

- Adjust the severity thresholds
- Add additional security checks
- Change the notification format

After making changes to the Lambda function, update it using:

```bash
# For CloudFormation deployment
aws cloudformation update-stack \
  --stack-name s3-security-analyzer \
  --template-body file://cloudformation/template.yaml \
  --parameters ParameterKey=NotificationEmail,ParameterValue=your-email@example.com \
  --capabilities CAPABILITY_IAM

# For Terraform deployment
terraform apply
```

## Security Considerations

### Permissions

The Lambda function requires permissions to:
- List all S3 buckets
- Check bucket configurations
- Send SNS notifications

The included IAM role follows the principle of least privilege, granting only the permissions needed to perform these tasks.

### Handling of Sensitive Information

- The analyzer doesn't access the actual content of your S3 buckets
- Only configuration metadata is analyzed
- Findings are sent to a single SNS topic with a verified subscription

### Operational Security

- All infrastructure is deployed within your AWS account
- No data leaves your account except via the SNS notifications you configure
- All actions are logged in CloudTrail
- The Lambda function uses AWS-managed encryption for environment variables

## Troubleshooting

### Common Issues

1. **Missing SNS Notifications**
   - Check that you confirmed the SNS subscription
   - Verify the Lambda function has permission to publish to the SNS topic

2. **Lambda Execution Errors**
   - Check CloudWatch Logs for the Lambda function
   - Ensure the IAM role has the necessary permissions

3. **Incorrect Findings**
   - Verify the analyzer's logic for specific checks in the Lambda code
   - Adjust thresholds or conditions as needed
