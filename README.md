# MLOps Batch Job — Primetrade.ai T0 Task

A minimal MLOps-style batch job that loads OHLCV data, computes a rolling mean on `close`, generates a binary trading signal, and writes structured metrics and logs.

---

## What This Does

1. Loads config from `config.yaml` (seed, window, version)
2. Reads `data.csv` — validates it has a `close` column
3. Computes rolling mean on `close` using the configured window
4. Generates signal: `1` if `close > rolling_mean`, else `0`
5. Writes metrics to `metrics.json` and logs to `run.log`
6. Runs locally and inside Docker

---

## Local Run

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the job
```bash
python run.py --input data.csv --config config.yaml --output metrics.json --log-file run.log
```

---

## Docker Build & Run

### 1. Build the Docker image
```bash
docker build -t mlops-task .
```

### 2. Run the container
```bash
docker run --rm mlops-task
```

The container includes `data.csv` and `config.yaml`, produces `metrics.json` and `run.log`, prints final metrics JSON to stdout, and exits with code `0` on success.

---

## Config (config.yaml)

```yaml
seed: 42
window: 5
version: "v1"
```

| Field   | Description                          |
|---------|--------------------------------------|
| seed    | Random seed for reproducibility      |
| window  | Rolling mean window size             |
| version | Pipeline version tag                 |

---

## Example Output (metrics.json)

```json
{
  "version": "v1",
  "rows_processed": 9996,
  "metric": "signal_rate",
  "value": 0.499,
  "latency_ms": 127,
  "seed": 42,
  "status": "success"
}
```

> Note: `rows_processed` excludes the first `window-1` rows where rolling mean is NaN.

---

## Error Output

```json
{
  "version": "v1",
  "status": "error",
  "error_message": "Description of what went wrong"
}
```

Metrics file is always written — even on failure.

---

## Project Structure

```
primetrade-mlops-task/
├── run.py           # Main pipeline script
├── config.yaml      # Configuration file
├── data.csv         # Input OHLCV dataset
├── requirements.txt # Python dependencies
├── Dockerfile       # Docker setup
├── README.md        # This file
├── metrics.json     # Sample success output
└── run.log          # Sample log output
```

---

## Author

Tisha Rakholiya — BTech CSE (AI & Data Science)  
github.com/tisha-rakholiya
