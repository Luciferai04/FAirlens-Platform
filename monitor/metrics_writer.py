"""
Writes fairness/equity_score custom metric to Google Cloud Monitoring.
"""
from google.cloud import monitoring_v3
from google.protobuf import timestamp_pb2
import time
import os


def write_equity_score(model_id: str, col: str, group: str, score: float,
                       project: str = None):
    project = project or os.environ.get("GCP_PROJECT_ID")
    client = monitoring_v3.MetricServiceClient()
    series = monitoring_v3.TimeSeries()
    series.metric.type = "custom.googleapis.com/fairlens/equity_score"
    series.metric.labels["model_id"] = model_id
    series.metric.labels["sensitive_col"] = col
    series.metric.labels["group"] = group
    series.resource.type = "global"

    now = time.time()
    seconds = int(now)
    nanos = int((now - seconds) * 10 ** 9)
    interval = monitoring_v3.TimeInterval(
        {"end_time": {"seconds": seconds, "nanos": nanos}}
    )
    point = monitoring_v3.Point(
        {"interval": interval, "value": {"double_value": score}}
    )
    series.points = [point]
    client.create_time_series(name=f"projects/{project}", time_series=[series])
