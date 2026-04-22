variable "project_id" {
  type        = string
  description = "GCP project ID for FairLens deployment"
}

variable "region" {
  type        = string
  default     = "us-central1"
  description = "GCP region for regional resources"
}

variable "bq_dataset" {
  type        = string
  default     = "fairlens"
  description = "BigQuery dataset name"
}

variable "alert_email" {
  type        = string
  default     = ""
  description = "Email address for monitoring alert notifications"
}

variable "console_image" {
  type        = string
  default     = ""
  description = "Container image for the frontend console (gcr.io/PROJECT/fairlens-console:latest)"
}

variable "api_image" {
  type        = string
  default     = ""
  description = "Container image for the backend API (gcr.io/PROJECT/fairlens-api:latest)"
}
