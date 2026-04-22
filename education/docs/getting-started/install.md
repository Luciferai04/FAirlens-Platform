# Installation

## Quick Install (SDK only)

```bash
pip install fairlens
```

## Full Development Setup

```bash
# Clone the repository
git clone https://github.com/your-org/fairlens.git
cd fairlens

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install SDK in development mode with all extras
pip install -e "sdk/[dev]"

# Install additional dependencies
pip install scikit-learn reportlab pypdf scipy

# Verify installation
python -c "import fairlens; print(fairlens.__version__)"
```

## Requirements

- Python ≥ 3.9
- scikit-learn ≥ 1.0
- numpy, pandas

### Optional Dependencies

| Package | Purpose | Install |
|---------|---------|---------|
| `reportlab` | PDF compliance reports | `pip install reportlab` |
| `shap` | SHAP explainability | `pip install shap` |
| `ctgan` | Synthetic data debiaser | `pip install ctgan` |
| `rich` | Pretty terminal output | `pip install rich` |
| `google-cloud-bigquery` | BigQuery integration | `pip install google-cloud-bigquery` |

## GCP Setup (Optional)

For cloud features (monitoring, remediation, compliance signing), see [GCP Setup](gcp-setup.md).
