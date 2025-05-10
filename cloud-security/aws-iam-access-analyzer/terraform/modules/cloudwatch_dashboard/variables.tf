variable "dashboard_name" {
  description = "Name of the CloudWatch dashboard"
  type        = string
  default     = "IAMAccessAnalyzerDashboard"
}

variable "analyzer_name" {
  description = "Name of the IAM Access Analyzer"
  type        = string
}