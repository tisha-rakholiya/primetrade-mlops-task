import argparse
import json
import logging
import time
import sys
import os

import numpy as np
import pandas as pd
import yaml


def setup_logging(log_file):
    """Setup logging to both file and console."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )


def load_config(config_path):
    """Load and validate config from YAML file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    # Validate required fields
    required_fields = ["seed", "window", "version"]
    for field in required_fields:
        if field not in config:
            raise ValueError(f"Missing required config field: {field}")

    return config


def load_dataset(input_path):
    """Load and validate CSV dataset."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    df = pd.read_csv(input_path)

    if df.empty:
        raise ValueError("Input CSV file is empty")

    if "close" not in df.columns:
        raise ValueError("Required column 'close' not found in dataset")

    return df


def compute_rolling_mean(df, window):
    """Compute rolling mean on close column."""
    # First window-1 rows will be NaN — we keep them and exclude from signal
    df["rolling_mean"] = df["close"].rolling(window=window).mean()
    return df


def generate_signal(df):
    """
    Generate binary signal:
    signal = 1 if close > rolling_mean
    signal = 0 otherwise
    NaN rows (first window-1 rows) are excluded
    """
    df["signal"] = np.where(
        df["rolling_mean"].isna(),
        np.nan,
        np.where(df["close"] > df["rolling_mean"], 1, 0)
    )
    return df


def write_metrics(output_path, metrics):
    """Write metrics to JSON file."""
    with open(output_path, "w") as f:
        json.dump(metrics, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description="MLOps Batch Job")
    parser.add_argument("--input",   required=True, help="Path to input CSV")
    parser.add_argument("--config",  required=True, help="Path to config YAML")
    parser.add_argument("--output",  required=True, help="Path to output metrics JSON")
    parser.add_argument("--log-file", required=True, help="Path to log file")
    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_file)
    logger = logging.getLogger(__name__)

    # Track start time
    start_time = time.time()
    logger.info("Job started")

    version = "v1"  # default fallback

    try:
        # Step 1: Load and validate config
        logger.info(f"Loading config from: {args.config}")
        config = load_config(args.config)
        seed    = config["seed"]
        window  = config["window"]
        version = config["version"]
        logger.info(f"Config loaded — seed={seed}, window={window}, version={version}")

        # Set seed for reproducibility
        np.random.seed(seed)
        logger.info(f"Random seed set to {seed}")

        # Step 2: Load and validate dataset
        logger.info(f"Loading dataset from: {args.input}")
        df = load_dataset(args.input)
        rows_loaded = len(df)
        logger.info(f"Dataset loaded — {rows_loaded} rows, columns: {list(df.columns)}")

        # Step 3: Compute rolling mean
        logger.info(f"Computing rolling mean with window={window}")
        df = compute_rolling_mean(df, window)
        logger.info("Rolling mean computed successfully")

        # Step 4: Generate signal
        logger.info("Generating binary signal (close > rolling_mean = 1, else 0)")
        df = generate_signal(df)

        # Exclude NaN rows (first window-1 rows) from signal rate calculation
        valid_signals = df["signal"].dropna()
        rows_processed = len(valid_signals)
        signal_rate = round(float(valid_signals.mean()), 4)
        logger.info(f"Signal generated — rows processed: {rows_processed}, signal_rate: {signal_rate}")

        # Step 5: Compute latency
        latency_ms = round((time.time() - start_time) * 1000)
        logger.info(f"Processing complete — latency: {latency_ms}ms")

        # Build success metrics
        metrics = {
            "version": version,
            "rows_processed": rows_processed,
            "metric": "signal_rate",
            "value": signal_rate,
            "latency_ms": latency_ms,
            "seed": seed,
            "status": "success"
        }

        # Write metrics
        write_metrics(args.output, metrics)
        logger.info(f"Metrics written to: {args.output}")
        logger.info(f"Job completed successfully — status: success")

        # Print final metrics to stdout
        print(json.dumps(metrics, indent=2))

        sys.exit(0)

    except Exception as e:
        latency_ms = round((time.time() - start_time) * 1000)
        logger.error(f"Job failed — {type(e).__name__}: {str(e)}")

        error_metrics = {
            "version": version,
            "status": "error",
            "error_message": str(e)
        }

        # Always write metrics even on error
        try:
            write_metrics(args.output, error_metrics)
            logger.info(f"Error metrics written to: {args.output}")
        except Exception as write_err:
            logger.error(f"Failed to write error metrics: {write_err}")

        print(json.dumps(error_metrics, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
