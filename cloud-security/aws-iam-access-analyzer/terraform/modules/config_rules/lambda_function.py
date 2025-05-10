import boto3
import json

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    
    # Parse the invocation event
    invocation_event = json.loads(event['invokingEvent'])
    configuration_item = invocation_event['configurationItem']
    
    # Get the S3 bucket name
    bucket_name = configuration_item['resourceName']
    
    try:
        # Block public access for the bucket
        s3.put_public_access_block(
            Bucket=bucket_name,
            PublicAccessBlockConfiguration={
                'BlockPublicAcls': True,
                'IgnorePublicAcls': True,
                'BlockPublicPolicy': True,
                'RestrictPublicBuckets': True
            }
        )
        
        return {
            'statusCode': 200,
            'message': f'Successfully blocked public access for bucket {bucket_name}'
        }
    except Exception as e:
        print(f'Error blocking public access for bucket {bucket_name}: {str(e)}')
        raise
