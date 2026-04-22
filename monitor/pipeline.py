"""
Streaming fairness monitor — Dataflow pipeline.
Subscribes to Pub/Sub prediction logs, bins by group, detects drift.
"""
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.transforms.window import FixedWindows
import json
import argparse
from .drift.page_hinkley import PageHinkleyDetector
from .metrics_writer import write_equity_score


class BinPredictionsByGroup(beam.DoFn):
    def __init__(self, sensitive_cols):
        self.sensitive_cols = sensitive_cols

    def process(self, element):
        prediction = element.get("prediction")
        for col in self.sensitive_cols:
            group_val = element.get(col, element.get("group_value"))
            if group_val is not None:
                yield {
                    "attribute": col,
                    "group_value": str(group_val),
                    "prediction": prediction,
                    "timestamp": element.get("timestamp"),
                }


class DriftDetectionFn(beam.DoFn):
    """Page-Hinkley drift detection per group stream."""

    def __init__(self, equity_threshold):
        self.equity_threshold = equity_threshold
        self._detectors = {}

    def process(self, element):
        key = f"{element['attribute']}::{element['group_value']}"
        if key not in self._detectors:
            self._detectors[key] = PageHinkleyDetector()
        detector = self._detectors[key]
        drift_detected = detector.update(float(element["prediction"]))

        yield {
            "window_start": element["timestamp"],
            "attribute": element["attribute"],
            "group_value": element["group_value"],
            "positive_rate": float(element["prediction"]),
            "sample_count": 1,
            "drift_detected": drift_detected,
        }


def run(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--subscription", required=True)
    parser.add_argument("--sensitive-cols", required=True)
    parser.add_argument("--equity-threshold", type=float, default=0.85)
    parser.add_argument("--bq-output", required=True)
    known_args, pipeline_args = parser.parse_known_args(argv)

    sensitive_cols = known_args.sensitive_cols.split(",")
    options = PipelineOptions(pipeline_args, streaming=True, save_main_session=True)

    with beam.Pipeline(options=options) as p:
        messages = (
            p
            | "ReadPubSub" >> beam.io.ReadFromPubSub(subscription=known_args.subscription)
            | "ParseJSON" >> beam.Map(lambda m: json.loads(m.decode("utf-8")))
            | "Window" >> beam.WindowInto(FixedWindows(60))
        )
        (
            messages
            | "BinByGroup" >> beam.ParDo(BinPredictionsByGroup(sensitive_cols))
            | "DetectDrift" >> beam.ParDo(DriftDetectionFn(known_args.equity_threshold))
            | "WriteBQ" >> beam.io.WriteToBigQuery(
                known_args.bq_output,
                write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
            )
        )


if __name__ == "__main__":
    run()
