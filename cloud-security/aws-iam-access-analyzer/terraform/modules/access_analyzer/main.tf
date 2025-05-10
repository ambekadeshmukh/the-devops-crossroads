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