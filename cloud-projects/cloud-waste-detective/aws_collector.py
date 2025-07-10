import boto3
import pandas as pd
from datetime import datetime, timedelta
import json
import logging
from typing import Dict, List, Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AWSCostCollector:
    """
    AWS Cost and Resource Collector for Cloud Waste Detection
    """
    
    def __init__(self, region_name: str = 'us-east-1'):
        """Initialize AWS clients"""
        try:
            self.region = region_name
            self.ec2 = boto3.client('ec2', region_name=region_name)
            self.cloudwatch = boto3.client('cloudwatch', region_name=region_name)
            self.pricing = boto3.client('pricing', region_name='us-east-1')  # Pricing API only available in us-east-1
            self.rds = boto3.client('rds', region_name=region_name)
            self.elbv2 = boto3.client('elbv2', region_name=region_name)
            self.s3 = boto3.client('s3')
            
            logger.info(f"Successfully initialized AWS clients for region: {region_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize AWS clients: {e}")
            raise

    def get_ec2_instances(self) -> pd.DataFrame:
        """
        Retrieve all EC2 instances with their metadata
        """
        try:
            response = self.ec2.describe_instances()
            instances = []
            
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    if instance['State']['Name'] != 'terminated':
                        # Extract tags
                        tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
                        
                        instances.append({
                            'resource_id': instance['InstanceId'],
                            'resource_type': 'EC2',
                            'instance_type': instance['InstanceType'],
                            'state': instance['State']['Name'],
                            'launch_time': instance['LaunchTime'],
                            'vpc_id': instance.get('VpcId', ''),
                            'subnet_id': instance.get('SubnetId', ''),
                            'name': tags.get('Name', 'Unnamed'),
                            'environment': tags.get('Environment', 'Unknown'),
                            'owner': tags.get('Owner', 'Unknown'),
                            'tags': json.dumps(tags)
                        })
            
            logger.info(f"Retrieved {len(instances)} EC2 instances")
            return pd.DataFrame(instances)
            
        except Exception as e:
            logger.error(f"Error retrieving EC2 instances: {e}")
            return pd.DataFrame()

    def get_rds_instances(self) -> pd.DataFrame:
        """
        Retrieve all RDS instances
        """
        try:
            response = self.rds.describe_db_instances()
            instances = []
            
            for db in response['DBInstances']:
                instances.append({
                    'resource_id': db['DBInstanceIdentifier'],
                    'resource_type': 'RDS',
                    'instance_type': db['DBInstanceClass'],
                    'state': db['DBInstanceStatus'],
                    'engine': db['Engine'],
                    'engine_version': db['EngineVersion'],
                    'storage_gb': db['AllocatedStorage'],
                    'multi_az': db['MultiAZ'],
                    'name': db['DBInstanceIdentifier'],
                    'environment': 'Unknown',
                    'owner': 'Unknown'
                })
            
            logger.info(f"Retrieved {len(instances)} RDS instances")
            return pd.DataFrame(instances)
            
        except Exception as e:
            logger.error(f"Error retrieving RDS instances: {e}")
            return pd.DataFrame()

    def get_load_balancers(self) -> pd.DataFrame:
        """
        Retrieve all Application Load Balancers
        """
        try:
            response = self.elbv2.describe_load_balancers()
            load_balancers = []
            
            for lb in response['LoadBalancers']:
                load_balancers.append({
                    'resource_id': lb['LoadBalancerArn'].split('/')[-1],
                    'resource_type': 'ALB',
                    'name': lb['LoadBalancerName'],
                    'state': lb['State']['Code'],
                    'scheme': lb['Scheme'],
                    'type': lb['Type'],
                    'vpc_id': lb['VpcId'],
                    'created_time': lb['CreatedTime']
                })
            
            logger.info(f"Retrieved {len(load_balancers)} load balancers")
            return pd.DataFrame(load_balancers)
            
        except Exception as e:
            logger.error(f"Error retrieving load balancers: {e}")
            return pd.DataFrame()

    def get_cpu_utilization(self, instance_id: str, days: int = 7) -> float:
        """
        Get average CPU utilization for an EC2 instance
        """
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=days)
            
            response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName='CPUUtilization',
                Dimensions=[
                    {'Name': 'InstanceId', 'Value': instance_id}
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,  # 1 hour
                Statistics=['Average']
            )
            
            if response['Datapoints']:
                datapoints = response['Datapoints']
                avg_cpu = sum(point['Average'] for point in datapoints) / len(datapoints)
                return round(avg_cpu, 2)
            
            return 0.0
            
        except Exception as e:
            logger.warning(f"Could not get CPU utilization for {instance_id}: {e}")
            return 0.0

    def estimate_monthly_cost(self, instance_type: str, resource_type: str = 'EC2') -> float:
        """
        Estimate monthly cost for a resource (simplified pricing)
        """
        # Simplified pricing estimates (actual pricing varies by region and usage)
        ec2_pricing = {
            't2.nano': 4.18,
            't2.micro': 8.35,
            't2.small': 16.70,
            't2.medium': 33.41,
            't2.large': 66.82,
            't3.nano': 3.80,
            't3.micro': 7.59,
            't3.small': 15.18,
            't3.medium': 30.37,
            't3.large': 60.74,
            't3.xlarge': 121.47,
            'm5.large': 69.12,
            'm5.xlarge': 138.24,
            'c5.large': 61.56,
            'c5.xlarge': 123.12
        }
        
        rds_pricing = {
            'db.t3.micro': 14.60,
            'db.t3.small': 29.20,
            'db.t3.medium': 58.40,
            'db.t3.large': 116.80,
            'db.m5.large': 138.24,
            'db.m5.xlarge': 276.48
        }
        
        if resource_type == 'EC2':
            return ec2_pricing.get(instance_type, 50.0)  # Default estimate
        elif resource_type == 'RDS':
            return rds_pricing.get(instance_type, 100.0)  # Default estimate
        elif resource_type == 'ALB':
            return 22.50  # Standard ALB pricing
        else:
            return 25.0  # Default estimate

    def analyze_waste(self) -> pd.DataFrame:
        """
        Comprehensive waste analysis across all AWS resources
        """
        all_resources = []
        
        # Analyze EC2 instances
        ec2_instances = self.get_ec2_instances()
        if not ec2_instances.empty:
            for _, instance in ec2_instances.iterrows():
                cpu_util = self.get_cpu_utilization(instance['resource_id'])
                monthly_cost = self.estimate_monthly_cost(instance['instance_type'], 'EC2')
                
                # Determine waste category
                waste_category = self._classify_ec2_waste(instance, cpu_util)
                savings = self._calculate_savings(instance, waste_category, monthly_cost)
                
                all_resources.append({
                    'resource_name': instance['name'],
                    'resource_id': instance['resource_id'],
                    'resource_type': instance['resource_type'],
                    'instance_type': instance['instance_type'],
                    'monthly_cost': monthly_cost,
                    'cpu_utilization': cpu_util,
                    'state': instance['state'],
                    'waste_category': waste_category,
                    'potential_savings': savings,
                    'recommendation': self._get_recommendation(waste_category, instance['instance_type']),
                    'environment': instance['environment'],
                    'owner': instance['owner'],
                    'last_updated': datetime.now()
                })
        
        # Analyze RDS instances
        rds_instances = self.get_rds_instances()
        if not rds_instances.empty:
            for _, instance in rds_instances.iterrows():
                monthly_cost = self.estimate_monthly_cost(instance['instance_type'], 'RDS')
                waste_category = self._classify_rds_waste(instance)
                savings = self._calculate_savings(instance, waste_category, monthly_cost)
                
                all_resources.append({
                    'resource_name': instance['name'],
                    'resource_id': instance['resource_id'],
                    'resource_type': instance['resource_type'],
                    'instance_type': instance['instance_type'],
                    'monthly_cost': monthly_cost,
                    'cpu_utilization': 0,  # RDS metrics require separate API calls
                    'state': instance['state'],
                    'waste_category': waste_category,
                    'potential_savings': savings,
                    'recommendation': self._get_recommendation(waste_category, instance['instance_type']),
                    'environment': instance['environment'],
                    'owner': instance['owner'],
                    'last_updated': datetime.now()
                })
        
        # Analyze Load Balancers
        load_balancers = self.get_load_balancers()
        if not load_balancers.empty:
            for _, lb in load_balancers.iterrows():
                monthly_cost = self.estimate_monthly_cost('', 'ALB')
                waste_category = self._classify_lb_waste(lb)
                savings = monthly_cost if waste_category == 'zombie' else 0
                
                all_resources.append({
                    'resource_name': lb['name'],
                    'resource_id': lb['resource_id'],
                    'resource_type': lb['resource_type'],
                    'instance_type': lb['type'],
                    'monthly_cost': monthly_cost,
                    'cpu_utilization': 0,
                    'state': lb['state'],
                    'waste_category': waste_category,
                    'potential_savings': savings,
                    'recommendation': self._get_recommendation(waste_category, 'ALB'),
                    'environment': 'Unknown',
                    'owner': 'Unknown',
                    'last_updated': datetime.now()
                })
        
        logger.info(f"Analyzed {len(all_resources)} total resources")
        return pd.DataFrame(all_resources)

    def _classify_ec2_waste(self, instance: dict, cpu_util: float) -> str:
        """Classify EC2 instance waste category"""
        if instance['state'] in ['stopped', 'stopping']:
            return 'zombie'
        elif cpu_util < 5:
            return 'severely-underutilized'
        elif cpu_util < 20:
            return 'underutilized'
        elif 'dev' in instance['name'].lower() or 'test' in instance['name'].lower():
            return 'schedule-candidate'
        else:
            return 'optimized'

    def _classify_rds_waste(self, instance: dict) -> str:
        """Classify RDS instance waste category"""
        if instance['state'] not in ['available']:
            return 'zombie'
        elif 'test' in instance['name'].lower() or 'dev' in instance['name'].lower():
            return 'schedule-candidate'
        else:
            return 'optimized'

    def _classify_lb_waste(self, lb: dict) -> str:
        """Classify Load Balancer waste category"""
        if lb['state'] != 'active':
            return 'zombie'
        # In real implementation, check target groups and traffic
        return 'optimized'

    def _calculate_savings(self, instance: dict, waste_category: str, monthly_cost: float) -> float:
        """Calculate potential savings based on waste category"""
        if waste_category == 'zombie':
            return monthly_cost  # Full savings by terminating
        elif waste_category == 'severely-underutilized':
            return monthly_cost * 0.5  # 50% savings by right-sizing
        elif waste_category == 'underutilized':
            return monthly_cost * 0.3  # 30% savings by right-sizing
        elif waste_category == 'schedule-candidate':
            return monthly_cost * 0.6  # 60% savings by scheduling
        else:
            return 0.0

    def _get_recommendation(self, waste_category: str, instance_type: str) -> str:
        """Get human-readable recommendation"""
        if waste_category == 'zombie':
            return f"Terminate unused resource"
        elif waste_category == 'severely-underutilized':
            return f"Right-size to smaller instance type"
        elif waste_category == 'underutilized':
            return f"Consider downsizing {instance_type}"
        elif waste_category == 'schedule-candidate':
            return "Implement auto-scheduling for dev/test environments"
        else:
            return "No optimization needed"

# Example usage
if __name__ == "__main__":
    # Example of how to use the collector
    try:
        collector = AWSCostCollector()
        waste_analysis = collector.analyze_waste()
        
        if not waste_analysis.empty:
            print(f"Found {len(waste_analysis)} resources")
            print(f"Total potential monthly savings: ${waste_analysis['potential_savings'].sum():.2f}")
            print("\nTop waste opportunities:")
            top_waste = waste_analysis.nlargest(5, 'potential_savings')[['resource_name', 'waste_category', 'potential_savings']]
            print(top_waste.to_string(index=False))
        else:
            print("No resources found or unable to connect to AWS")
            
    except Exception as e:
        print(f"Error running waste analysis: {e}")
        print("Make sure AWS credentials are configured properly")