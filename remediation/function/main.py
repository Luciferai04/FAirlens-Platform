"""
Cloud Function: triggered by Pub/Sub bias incident topic.
Calls Gemini 1.5 Pro to generate remediation playbook.
Stores result in Firestore with pending_approval gate.
"""
import functions_framework
import base64
import json
import os
import uuid
import time
from datetime import datetime, timezone

from google.cloud import firestore, pubsub_v1
import google.generativeai as genai
from jinja2 import Environment, FileSystemLoader


# Pre-cached fallback template
FALLBACK_PLAYBOOK = {
    "strategies": [
        {
            "name": "Reweighting Training Data",
            "description": "Apply sample weights inversely proportional to group representation to balance model learning.",
            "technique": "reweighting",
            "code_snippet": "from fairlearn.reductions import ExponentiatedGradient, DemographicParity\nmitigator = ExponentiatedGradient(estimator, DemographicParity())\nmitigator.fit(X_train, y_train, sensitive_features=sensitive)",
            "estimated_effort": "medium",
        },
        {
            "name": "Threshold Adjustment",
            "description": "Apply group-specific decision thresholds to equalize positive prediction rates.",
            "technique": "threshold_adjustment",
            "code_snippet": "from fairlearn.postprocessing import ThresholdOptimizer\nto = ThresholdOptimizer(estimator=model, constraints='demographic_parity')\nto.fit(X_train, y_train, sensitive_features=sensitive)",
            "estimated_effort": "low",
        },
        {
            "name": "Feature Audit and Removal",
            "description": "Identify and remove proxy features that correlate with protected attributes.",
            "technique": "feature_removal",
            "code_snippet": "from sklearn.feature_selection import mutual_info_classif\nmi = mutual_info_classif(X, sensitive)\nproxy_features = [f for f, s in zip(X.columns, mi) if s > 0.1]",
            "estimated_effort": "low",
        },
    ],
    "root_cause_analysis": "Bias likely stems from historical data imbalances and proxy features correlated with protected attributes.",
    "priority_order": ["Threshold Adjustment", "Reweighting Training Data", "Feature Audit and Removal"],
}


@functions_framework.cloud_event
def generate_playbook(cloud_event):
    """Entry point: receives BiasIncident from Pub/Sub."""
    data = base64.b64decode(cloud_event.data["message"]["data"]).decode()
    incident = json.loads(data)

    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
    db = firestore.Client()

    start = time.time()
    playbook = _generate_with_gemini(incident, db)
    elapsed = time.time() - start

    playbook_id = str(uuid.uuid4())

    doc = {
        "playbook_id": playbook_id,
        "incident_id": incident.get("incident_id", "unknown"),
        "model_id": incident.get("model_id", "unknown"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "pending_approval": True,
        "status": "pending_approval",
        "strategies": playbook.get("strategies", []),
        "root_cause_analysis": playbook.get("root_cause_analysis", ""),
        "priority_order": playbook.get("priority_order", []),
        "generation_time_seconds": round(elapsed, 2),
        "version": 1,
    }

    db.collection("playbooks").document(playbook_id).set(doc)

    # Notify that playbook is ready
    try:
        publisher = pubsub_v1.PublisherClient()
        topic = f"projects/{os.environ.get('GCP_PROJECT_ID')}/topics/fairlens-playbooks-ready"
        publisher.publish(topic, json.dumps({
            "playbook_id": playbook_id,
            "incident_id": incident.get("incident_id"),
        }).encode())
    except Exception as e:
        print(f"[Remediation] Warning: could not publish notification: {e}")

    print(f"Playbook {playbook_id} generated in {elapsed:.1f}s for incident {incident.get('incident_id')}")


def _generate_with_gemini(incident: dict, db: firestore.Client) -> dict:
    """Generate playbook via Gemini, with fallback to cached template."""
    try:
        # Load and render prompt template
        prompts_dir = os.path.join(os.path.dirname(__file__), "..", "prompts")
        if not os.path.exists(prompts_dir):
            prompts_dir = "/workspace/prompts"

        env = Environment(loader=FileSystemLoader(prompts_dir))
        tmpl = env.get_template("playbook.jinja2")
        prompt = tmpl.render(incident=incident)

        model = genai.GenerativeModel(
            model_name=os.environ.get("GEMINI_MODEL", "gemini-1.5-pro"),
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.2,
            ),
        )
        response = model.generate_content(prompt)
        result = json.loads(response.text)

        # Validate structure
        if "strategies" not in result or len(result["strategies"]) == 0:
            raise ValueError("Gemini response missing strategies")

        return result

    except (json.JSONDecodeError, ValueError) as e:
        print(f"[Remediation] Gemini returned invalid JSON, using fallback: {e}")
        return _get_fallback_template(db)

    except Exception as e:
        print(f"[Remediation] Gemini API error, using fallback: {e}")
        return _get_fallback_template(db)


def _get_fallback_template(db: firestore.Client) -> dict:
    """Retrieve fallback template from Firestore, or use hardcoded default."""
    try:
        doc = db.collection("playbook_templates").document("default").get()
        if doc.exists:
            return doc.to_dict()
    except Exception:
        pass
    return FALLBACK_PLAYBOOK
