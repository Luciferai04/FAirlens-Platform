terraform {
  required_version = ">= 1.5"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# ─── BigQuery Dataset ──────────────────────────────────────────────

resource "google_bigquery_dataset" "fairlens" {
  dataset_id                 = "fairlens"
  project                    = var.project_id
  location                   = "US"
  description                = "FairLens bias audit and governance data"
  delete_contents_on_destroy = false

  labels = {
    environment = "production"
    managed_by  = "terraform"
  }
}

# ─── BigQuery Tables ───────────────────────────────────────────────

resource "google_bigquery_table" "audit_reports" {
  dataset_id          = google_bigquery_dataset.fairlens.dataset_id
  table_id            = "audit_reports"
  project             = var.project_id
  deletion_protection = false

  time_partitioning {
    type  = "DAY"
    field = "created_at"
  }

  clustering = ["model_id"]

  schema = jsonencode([
    { name = "report_id",        type = "STRING",          mode = "REQUIRED" },
    { name = "model_id",         type = "STRING",          mode = "REQUIRED" },
    { name = "created_at",       type = "TIMESTAMP",       mode = "REQUIRED" },
    { name = "protected_cols",   type = "STRING",          mode = "REPEATED" },
    { name = "metrics",          type = "JSON",            mode = "NULLABLE" },
    { name = "threshold_policy", type = "STRING",          mode = "NULLABLE" },
    { name = "passed",           type = "BOOL",            mode = "NULLABLE" },
    { name = "triggered_by",     type = "STRING",          mode = "NULLABLE" },
    { name = "provider",         type = "STRING",          mode = "NULLABLE" },
    { name = "intended_purpose", type = "STRING",          mode = "NULLABLE" },
    { name = "open_incidents",   type = "INT64",           mode = "NULLABLE" },
    { name = "last_remediation", type = "TIMESTAMP",       mode = "NULLABLE" },
  ])
}

resource "google_bigquery_table" "bias_incidents" {
  dataset_id          = google_bigquery_dataset.fairlens.dataset_id
  table_id            = "bias_incidents"
  project             = var.project_id
  deletion_protection = false

  time_partitioning {
    type  = "DAY"
    field = "detected_at"
  }

  clustering = ["model_id", "status"]

  schema = jsonencode([
    { name = "incident_id",   type = "STRING",    mode = "REQUIRED" },
    { name = "model_id",      type = "STRING",    mode = "REQUIRED" },
    { name = "detected_at",   type = "TIMESTAMP", mode = "REQUIRED" },
    { name = "metric_name",   type = "STRING",    mode = "NULLABLE" },
    { name = "current_value", type = "FLOAT64",   mode = "NULLABLE" },
    { name = "threshold",     type = "FLOAT64",   mode = "NULLABLE" },
    { name = "severity",      type = "STRING",    mode = "NULLABLE" },
    { name = "status",        type = "STRING",    mode = "NULLABLE" },
    { name = "sensitive_col", type = "STRING",    mode = "NULLABLE" },
    { name = "playbook_id",   type = "STRING",    mode = "NULLABLE" },
    { name = "resolved_at",   type = "TIMESTAMP", mode = "NULLABLE" },
  ])
}

resource "google_bigquery_table" "bias_profiles" {
  dataset_id          = google_bigquery_dataset.fairlens.dataset_id
  table_id            = "bias_profiles"
  project             = var.project_id
  deletion_protection = false

  time_partitioning {
    type  = "DAY"
    field = "scanned_at"
  }

  schema = jsonencode([
    { name = "profile_id",         type = "STRING",    mode = "REQUIRED" },
    { name = "dataset_gcs_path",   type = "STRING",    mode = "NULLABLE" },
    { name = "scanned_at",         type = "TIMESTAMP", mode = "REQUIRED" },
    { name = "sensitive_cols",     type = "STRING",    mode = "REPEATED" },
    { name = "class_imbalance",    type = "JSON",      mode = "NULLABLE" },
    { name = "proxy_leakage",      type = "JSON",      mode = "NULLABLE" },
    { name = "label_bias",         type = "JSON",      mode = "NULLABLE" },
    { name = "representation_gap", type = "JSON",      mode = "NULLABLE" },
    { name = "overall_risk_score", type = "FLOAT64",   mode = "NULLABLE" },
  ])
}

resource "google_bigquery_table" "shap_attributions" {
  dataset_id          = google_bigquery_dataset.fairlens.dataset_id
  table_id            = "shap_attributions"
  project             = var.project_id
  deletion_protection = false

  time_partitioning {
    type  = "DAY"
    field = "computed_at"
  }

  clustering = ["model_id", "sensitive_col"]

  schema = jsonencode([
    { name = "attribution_id", type = "STRING",    mode = "REQUIRED" },
    { name = "model_id",       type = "STRING",    mode = "REQUIRED" },
    { name = "sensitive_col",  type = "STRING",    mode = "NULLABLE" },
    { name = "group_value",    type = "STRING",    mode = "NULLABLE" },
    { name = "feature_name",   type = "STRING",    mode = "NULLABLE" },
    { name = "mean_abs_shap",  type = "FLOAT64",   mode = "NULLABLE" },
    { name = "computed_at",    type = "TIMESTAMP", mode = "REQUIRED" },
  ])
}

# ─── Pub/Sub Topics ────────────────────────────────────────────────

resource "google_pubsub_topic" "predictions" {
  name                       = "fairlens-predictions"
  project                    = var.project_id
  message_retention_duration = "86600s"
}

resource "google_pubsub_topic" "scan_requests" {
  name    = "fairlens-scan-requests"
  project = var.project_id
}

resource "google_pubsub_topic" "bias_incidents" {
  name    = "fairlens-bias-incidents"
  project = var.project_id
}

resource "google_pubsub_topic" "playbooks_ready" {
  name    = "fairlens-playbooks-ready"
  project = var.project_id
}

# ─── Pub/Sub Subscriptions ─────────────────────────────────────────

resource "google_pubsub_subscription" "monitor_sub" {
  name                       = "fairlens-monitor-sub"
  topic                      = google_pubsub_topic.predictions.name
  project                    = var.project_id
  ack_deadline_seconds       = 60
  message_retention_duration = "3600s"

  expiration_policy {
    ttl = ""
  }
}

resource "google_pubsub_subscription" "remediation_sub" {
  name                 = "fairlens-remediation-sub"
  topic                = google_pubsub_topic.bias_incidents.name
  project              = var.project_id
  ack_deadline_seconds = 120
}

# ─── Cloud Storage ─────────────────────────────────────────────────

resource "google_storage_bucket" "artifacts" {
  name          = "${var.project_id}-fairlens-artifacts"
  project       = var.project_id
  location      = var.region
  force_destroy = false

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 365
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }
}

# ─── Artifact Registry ────────────────────────────────────────────

resource "google_artifact_registry_repository" "fairlens" {
  location      = var.region
  project       = var.project_id
  repository_id = "fairlens"
  format        = "DOCKER"
  description   = "FairLens platform container images"
}

# ─── Cloud KMS ─────────────────────────────────────────────────────

resource "google_kms_key_ring" "fairlens_keys" {
  name     = "fairlens-keys"
  location = "global"
  project  = var.project_id
}

resource "google_kms_crypto_key" "compliance_signer" {
  name     = "compliance-signer"
  key_ring = google_kms_key_ring.fairlens_keys.id
  purpose  = "ASYMMETRIC_SIGN"

  version_template {
    algorithm        = "RSA_SIGN_PKCS1_4096_SHA512"
    protection_level = "SOFTWARE"
  }

  lifecycle {
    prevent_destroy = true
  }
}
