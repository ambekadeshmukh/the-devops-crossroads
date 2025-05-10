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