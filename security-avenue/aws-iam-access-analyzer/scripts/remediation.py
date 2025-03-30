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