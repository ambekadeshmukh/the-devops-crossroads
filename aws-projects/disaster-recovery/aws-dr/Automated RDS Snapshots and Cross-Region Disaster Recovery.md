# Automated RDS Snapshots and Cross-Region Disaster Recovery

This repository contains the code and documentation for implementing an automated RDS snapshot and cross-region disaster recovery (DR) solution using AWS services.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Components](#components)
3. [Implementation Steps](#implementation-steps)
   - [Automated Snapshot Creation](#automated-snapshot-creation)
   - [Cross-Region Snapshot Copy](#cross-region-snapshot-copy)
   - [Automated Snapshot Deletion](#automated-snapshot-deletion)
4. [Disaster Recovery Process](#disaster-recovery-process)
5. [Setup Instructions](#setup-instructions)
6. [Testing](#testing)
7. [Monitoring and Alerting](#monitoring-and-alerting)
8. [Security Considerations](#security-considerations)
9. [Conclusion](#conclusion)


## Architecture Overview

![Untitled-2024-10-18-1300](https://github.com/user-attachments/assets/58e4338c-8393-42e4-8b54-a09073f93b7d)


This architecture leverages AWS Lambda functions triggered by EventBridge rules to create regular snapshots of our RDS instance in the US East (N. Virginia) region. These snapshots are then automatically copied to the US West (Oregon) region for disaster recovery purposes. The system also includes a mechanism to clean up old snapshots, ensuring efficient resource management.

## Components

- Amazon RDS: Hosts our database instance
- AWS Lambda: Executes the core logic for snapshot creation, copying, and deletion
- Amazon EventBridge: Triggers Lambda functions on a schedule
- AWS Identity and Access Management (IAM): Manages permissions for Lambda functions
- AWS Key Management Service (KMS): Ensures encryption of snapshots in the destination region
- Amazon Simple Notification Service (SNS): Sends notifications about the snapshot processes
- Amazon Route 53: Used for DNS failover in case of disaster recovery

## Implementation Steps

### Automated Snapshot Creation

1. Create a Lambda function named `RDS_Snapshot_Automation` with the following code:

```python
import boto3
from datetime import datetime

rds_client = boto3.client('rds')
sns_client = boto3.client('sns')

# Update this ARN to match your actual SNS topic ARN
SNS_TOPIC_ARN = 'arn:aws:sns:us-east-1:YOUR_ACCOUNT_ID:RDS-Snapshot-Notifications'

def lambda_handler(event, context):
    db_instance_identifier = 'database-1'
    current_time = datetime.now().strftime("%Y-%m-%d-%H-%M")
    snapshot_identifier = f"{db_instance_identifier}-snapshot-{
current_time}"
    
    try:
        # Take a snapshot
        response = rds_client.create_db_snapshot(
            DBInstanceIdentifier=db_instance_identifier,
            DBSnapshotIdentifier=snapshot_identifier
        )
        message = f"Snapshot {snapshot_identifier} created successfully."
        print(message)
        
        # Publish success message to SNS
        sns_response = sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=message,
            Subject='RDS Snapshot Creation Success'
        )
        print(f"SNS publish response: {sns_response}")
        
    except Exception as e:
        error_message = f"Error: {str(e)}"
        print(error_message)
        
        # Publish failure message to SNS
        try:
            sns_response = sns_client.publish(
                TopicArn=SNS_TOPIC_ARN,
                Message=error_message,
                Subject='RDS Snapshot Creation Failed'
            )
            print(f"SNS publish response for error: {sns_response}")
        except Exception as sns_error:
            print(f"Failed to publish to SNS: {str(sns_error)}")
    
    return {
        'statusCode': 200,
        'body': 'Lambda function executed successfully'
    }
```

2. Create an EventBridge rule named `RDS_Snapshot_6Hr_Trigger` to run this function every 6 hours using the cron expression `cron(0 */6 * * ? *)`.

### Cross-Region Snapshot Copy

1. Create a Lambda function named `RDS_Snapshot_Copy` with the following code:

```python
import boto3
from botocore.exceptions import ClientError

# Set up clients
rds_client = boto3.client('rds', region_name='us-east-1')
destination_region_client = boto3.client('rds', region_name='us-west-2')
sns_client = boto3.client('sns', region_name='us-east-1')

# Constants
SOURCE_REGION = 'us-east-1'
DESTINATION_REGION = 'us-west-2'
DB_INSTANCE_IDENTIFIER = 'database-1'
SNS_TOPIC_ARN = 'arn:aws:sns:us-east-1:YOUR_ACCOUNT_ID:RDS-Snapshot-Notifications'
ACCOUNT_ID = 'YOUR_ACCOUNT_ID'
DESTINATION_KMS_KEY_ID = 'YOUR_KMS_KEY_ID'  # Replace with your KMS key ID in us-west-2

def lambda_handler(event, context):
    try:
        # Get the latest snapshot
        snapshots = rds_client.describe_db_snapshots(DBInstanceIdentifier=DB_INSTANCE_IDENTIFIER)['DBSnapshots']
        if not snapshots:
            raise ValueError(f"No snapshots found for {DB_INSTANCE_IDENTIFIER}")
        
        latest_snapshot = max(snapshots, key=lambda x: x['SnapshotCreateTime'])
        snapshot_identifier = latest_snapshot['DBSnapshotIdentifier']
        copy_identifier = f"{snapshot_identifier}-copy-{DESTINATION_REGION}"

        # Construct the source ARN
        source_arn = f'arn:aws:rds:{SOURCE_REGION}:{ACCOUNT_ID}:snapshot:{snapshot_identifier}'

        # Copy snapshot to another region
        response = destination_region_client.copy_db_snapshot(
            SourceDBSnapshotIdentifier=source_arn,
            TargetDBSnapshotIdentifier=copy_identifier,
            SourceRegion=SOURCE_REGION,
            KmsKeyId=DESTINATION_KMS_KEY_ID,
            CopyTags=True
        )
        
        message = f"Snapshot {snapshot_identifier} copy initiated to {DESTINATION_REGION} as {copy_identifier}."
        print(message)
        
        # Publish success message to SNS
        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=message,
            Subject=f'RDS Snapshot Copy Initiated to {DESTINATION_REGION}'
        )
        
        return {
            'statusCode': 200,
            'body': message
        }
    except ClientError as e:
        error_message = f"AWS Error copying snapshot: {e.response['Error']['Message']}"
        print(error_message)
        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=error_message,
            Subject=f'RDS Snapshot Copy Failed to {DESTINATION_REGION}'
        )
        return {
            'statusCode': 500,
            'body': error_message
        }
    except Exception as e:
        error_message = f"Unexpected error: {str(e)}"
        print(error_message)
        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=error_message,
            Subject=f'RDS Snapshot Copy Failed to {DESTINATION_REGION}'
        )
        return {
            'statusCode': 500,
            'body': error_message
        }
```

2. Create an EventBridge rule named `RDS_Snapshot_Copy_6Hr_Trigger` to run this function every 6 hours.

### Automated Snapshot Deletion

1. Create a Lambda function named `RDS_Delete_Old_Snapshots` with the following code:

```python
import boto3
from datetime import datetime, timedelta

rds_client = boto3.client('rds')
sns_client = boto3.client('sns')

SNS_TOPIC_ARN = 'arn:aws:sns:us-east-1:YOUR_ACCOUNT_ID:RDS-Snapshot-Notifications'

def lambda_handler(event, context):
    retention_days = 10
    db_instance_identifier = 'database-1'
    snapshots = rds_client.describe_db_snapshots(DBInstanceIdentifier=db_instance_identifier)['DBSnapshots']
    deletion_time = datetime.now() - timedelta(days=retention_days)

    for snapshot in snapshots:
        snapshot_creation_time = snapshot['SnapshotCreateTime']
        snapshot_identifier = snapshot['DBSnapshotIdentifier']
        
        if snapshot_creation_time < deletion_time:
            try:
                # Delete old snapshot
                rds_client.delete_db_snapshot(DBSnapshotIdentifier=snapshot_identifier)
                message = f"Deleted snapshot: {snapshot_identifier}"
                print(message)
                
                # Publish success message to SNS
                sns_client.publish(
                    TopicArn=SNS_TOPIC_ARN,
                    Message=message,
                    Subject='RDS Snapshot Deletion Success'
                )
            except Exception as e:
                error_message = f"Error deleting snapshot {snapshot_identifier}: {e}"
                print(error_message)
                
                # Publish failure message to SNS
                sns_client.publish(
                    TopicArn=SNS_TOPIC_ARN,
                    Message=error_message,
                    Subject='RDS Snapshot Deletion Failed'
                )
```

2. Create an EventBridge rule to run this function daily using the cron expression `cron(0 0 * * ? *)`.

## Disaster Recovery Process

In the event of a failure in the primary region (US East N. Virginia), follow these steps to recover in the US West Oregon region:

1. Trigger the Recovery Lambda function in US West Oregon.
2. The Recovery Lambda will:
   a. Identify the latest copied snapshot in US West Oregon.
   b. Initiate the restore process from this snapshot to create a new RDS instance.
   c. Update Route 53 DNS records to point to the new RDS instance.

Here's the code for the Recovery Lambda function:

```python
import boto3
import time

rds_client = boto3.client('rds', region_name='us-west-2')
route53_client = boto3.client('route53')

def lambda_handler(event, context):
    # Find the latest snapshot
    snapshots = rds_client.describe_db_snapshots(
        SnapshotType='manual',
        IncludeShared=False,
        IncludePublic=False
    )['DBSnapshots']
    
    latest_snapshot = max(snapshots, key=lambda x: x['SnapshotCreateTime'])
    
    # Restore the RDS instance from the snapshot
    new_instance_identifier = f"restored-{latest_snapshot['DBSnapshotIdentifier']}"
    response = rds_client.restore_db_instance_from_db_snapshot(
        DBInstanceIdentifier=new_instance_identifier,
        DBSnapshotIdentifier=latest_snapshot['DBSnapshotIdentifier'],
        PubliclyAccessible=False
    )
    
    # Wait for the instance to be available
    waiter = rds_client.get_waiter('db_instance_available')
    waiter.wait(DBInstanceIdentifier=new_instance_identifier)
    
    # Get the new endpoint
    instance_info = rds_client.describe_db_instances(DBInstanceIdentifier=new_instance_identifier)
    new_endpoint = instance_info['DBInstances'][0]['Endpoint']['Address']
    
    # Update Route 53
    route53_client.change_resource_record_sets(
        HostedZoneId='YOUR_HOSTED_ZONE_ID',
        ChangeBatch={
            'Changes': [
                {
                    'Action': 'UPSERT',
                    'ResourceRecordSet': {
                        'Name': 'your-db-domain.com',
                        'Type': 'CNAME',
                        'TTL': 300,
                        'ResourceRecords': [{'Value': new_endpoint}]
                    }
                }
            ]
        }
    )
    
    return {
        'statusCode': 200,
        'body': f'Recovery completed. New instance: {new_instance_identifier}, Endpoint: {new_endpoint}'
    }
```

## Setup Instructions

1. Set up an RDS instance in the US East (N. Virginia) region.
2. Create an SNS topic for notifications.
3. Create the necessary IAM roles with appropriate permissions for the Lambda functions.
4. Create a KMS key in the US West (Oregon) region for snapshot encryption.
5. Implement the Lambda functions as described above.
6. Set up the EventBridge rules to trigger the Lambda functions.
7. Configure Route 53 for your database domain.

## Testing

1. Manually trigger the snapshot creation Lambda function and verify that a snapshot is created.
2. Wait for the cross-region copy function to run and check that the snapshot is copied to the US West (Oregon) region.
3. Manually trigger the snapshot deletion function and verify that old snapshots are removed.
4. Simulate a disaster recovery scenario by manually triggering the recovery Lambda function and verifying that a new RDS instance is created and Route 53 is updated.

## Monitoring and Alerting

- Use CloudWatch Logs to monitor the execution of Lambda functions.
- Set up CloudWatch Alarms to alert on any failures in the snapshot creation, copying, or deletion processes.
- Use the SNS notifications to stay informed about the status of each operation.

## Security Considerations

- Ensure that all IAM roles follow the principle of least privilege.
- Use KMS encryption for snapshots in both regions.
- Regularly rotate the KMS keys used for snapshot encryption.
- Implement network security controls to restrict access to the RDS instances.

## Conclusion

By implementing this automated RDS snapshot and cross-region DR solution, you've significantly enhanced your database's resilience and recovery capabilities. Regular testing of the recovery process is crucial to ensure its effectiveness in real-world scenarios.
Remember to adjust the IAM roles, KMS keys, and other AWS resource identifiers to match your specific setup. 
