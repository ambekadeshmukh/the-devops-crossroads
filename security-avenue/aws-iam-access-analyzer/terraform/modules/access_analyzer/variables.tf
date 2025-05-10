variable "analyzer_name" {
  description = "Name of the IAM Access Analyzer"
  type        = string
}

variable "analyzer_type" {
  description = "Type of analyzer (ACCOUNT or ORGANIZATION)"
  type        = string
}

variable "finding_notification_enabled" {
  description = "Enable notifications for findings"
  type        = bool
}

variable "finding_notification_frequency" {
  description = "Frequency of finding notifications"
  type        = string
}