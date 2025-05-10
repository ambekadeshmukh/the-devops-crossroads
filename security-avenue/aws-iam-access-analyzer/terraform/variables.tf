variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "analyzer_name" {
  description = "Name of the IAM Access Analyzer"
  type        = string
  default     = "account-analyzer"
}

variable "analyzer_type" {
  description = "Type of analyzer (ACCOUNT or ORGANIZATION)"
  type        = string
  default     = "ACCOUNT"
}

variable "finding_notification_enabled" {
  description = "Enable notifications for findings"
  type        = bool
  default     = true
}

variable "finding_notification_frequency" {
  description = "Frequency of finding notifications (FIFTEEN_MINUTES, ONE_HOUR, SIX_HOURS, DAILY)"
  type        = string
  default     = "DAILY"
}