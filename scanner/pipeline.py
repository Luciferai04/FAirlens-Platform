"""
FairLens Bias Scanner — Apache Beam / Dataflow pipeline.
Reads CSV from GCS, runs all three detectors, produces BiasProfile, writes to BigQuery.

Usage:
    python pipeline.py --runner=DataflowRunner --project=PROJECT --region=REGION \
        --input_gcs=gs://bucket/data.csv --sensitive_cols=gender,race \
        --bq_output=PROJECT:fairlens.bias_profiles
"""
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
import argparse
import json
import pandas as pd
import io

from .detectors import detect_class_imbalance, detect_proxy_leakage, detect_label_bias
from .schema import BiasProfile


class RunBiasScanner(beam.DoFn):
    """DoFn that reads a CSV, runs all detectors, and produces a BiasProfile."""

    def __init__(self, sensitive_cols, label_col="label"):
        self.sensitive_cols = sensitive_cols
        self.label_col = label_col

    def process(self, csv_content):
        df = pd.read_csv(io.StringIO(csv_content))

        profile = BiasProfile(
            dataset_id="gcs_input",
            n_rows=len(df),
            n_cols=len(df.columns),
            protected_cols=self.sensitive_cols,
        )

        profile.imbalance_results = detect_class_imbalance(
            df, self.sensitive_cols, self.label_col
        )
        profile.proxy_leakage_results = detect_proxy_leakage(
            df, self.sensitive_cols
        )
        profile.label_bias_results = detect_label_bias(
            df, self.sensitive_cols, self.label_col
        )

        profile.compute_severity()
        profile.compute_health_score()

        yield profile.to_dict()


def run(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_gcs", required=True, help="gs://bucket/path/to/data.csv")
    parser.add_argument("--sensitive_cols", required=True, help="Comma-separated sensitive cols")
    parser.add_argument("--bq_output", required=True, help="project:dataset.table")
    parser.add_argument("--label_col", default="label")
    known_args, pipeline_args = parser.parse_known_args(argv)

    sensitive_cols = known_args.sensitive_cols.split(",")

    options = PipelineOptions(
        pipeline_args, save_main_session=True, job_name="fairlens-bias-scanner"
    )

    with beam.Pipeline(options=options) as p:
        (
            p
            | "ReadCSV" >> beam.io.ReadFromText(known_args.input_gcs)
            | "CombineLines" >> beam.CombineGlobally(lambda lines: "\n".join(lines))
            | "ScanBias" >> beam.ParDo(
                RunBiasScanner(sensitive_cols, known_args.label_col)
            )
            | "WriteBQ" >> beam.io.WriteToBigQuery(
                known_args.bq_output,
                write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
            )
        )


if __name__ == "__main__":
    run()
