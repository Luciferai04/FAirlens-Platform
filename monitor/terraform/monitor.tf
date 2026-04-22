# FairLens Monitor — Terraform module
# Creates Pub/Sub subscription, Dataflow job config, monitoring alert, and Slack channel.

variable "project_id" { type = string }
variable "region" { type = string default = "us-central1" }
variable "slack_webhook_url" { type = string default = "" }

# ── Custom Metric Descriptor ──────────────────────────────────────

resource "google_monitoring_metric_descriptor" "equity_score" {
  project      = var.project_id
  display_name = "FairLens Equity Score"
  type         = "custom.googleapis.com/fairlens/equity_score"
  metric_kind  = "GAUGE"
  value_type   = "DOUBLE"
  unit         = "1"
  description  = "Composite fairness equity score (0-1, higher = fairer)"

  labels {
    key         = "model_id"
    value_type  = "STRING"
    description = "Model identifier"
  }
  labels {
    key         = "sensitive_col"
    value_type  = "STRING"
    description = "Protected attribute column"
  }
  labels {
    key         = "group"
    value_type  = "STRING"
    description = "Demographic group value"
  }
}

# ── Alert Policy: equity_score < 0.8 ──────────────────────────────

resource "google_monitoring_alert_policy" "equity_alert" {
  project      = var.project_id
  display_name = "FairLens — Equity Score Below 0.80"
  combiner     = "OR"

  conditions {
    display_name = "equity_score < 0.80 for 15 min"
    condition_threshold {
      filter          = "metric.type=\"custom.googleapis.com/fairlens/equity_score\""
      comparison      = "COMPARISON_LT"
      threshold_value = 0.80
      duration        = "900s"
      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }

  notification_channels = compact([
    var.slack_webhook_url != "" ? google_monitoring_notification_channel.slack[0].name : null
  ])

  alert_strategy {
    auto_close = "1800s"
  }
}

# ── Slack Notification Channel ────────────────────────────────────

resource "google_monitoring_notification_channel" "slack" {
  count        = var.slack_webhook_url != "" ? 1 : 0
  project      = var.project_id
  display_name = "FairLens Slack Alerts"
  type         = "slack"
  labels = {
    channel_name = "#fairlens-alerts"
  }
  sensitive_labels {
    auth_token = var.slack_webhook_url
  }
}
