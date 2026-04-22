output "bigquery_dataset_id" {
  value       = google_bigquery_dataset.fairlens.dataset_id
  description = "BigQuery dataset ID"
}

output "pubsub_predictions_topic" {
  value       = google_pubsub_topic.predictions.name
  description = "Pub/Sub topic for prediction logs"
}

output "pubsub_incidents_topic" {
  value       = google_pubsub_topic.bias_incidents.name
  description = "Pub/Sub topic for bias incidents"
}

output "artifacts_bucket" {
  value       = google_storage_bucket.artifacts.name
  description = "GCS bucket for FairLens artifacts"
}

output "artifact_registry_url" {
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.fairlens.repository_id}"
  description = "Artifact Registry Docker repository URL"
}

output "kms_key_ring" {
  value       = google_kms_key_ring.fairlens_keys.name
  description = "KMS key ring name"
}

output "kms_signing_key" {
  value       = google_kms_crypto_key.compliance_signer.name
  description = "KMS asymmetric signing key name"
}
