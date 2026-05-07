# Stripe MRR Dashboard

Steps below should be ran sequentially.

## How to Run the Data Generator (Step 1)

0. Create a `.env` file with your Stripe API key. Refer to `.env.example` for the required format.

### Windows CMD/PowerShell

```bash
cd scripts
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python populate_stripe.py
```

### macOS/Linux Bash/Zsh

```bash
cd scripts
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 populate_stripe.py
```

To see the logic used to generate Stripe test data, see [SCRIPT_PLAN](./plans/SCRIPT_PLAN.md)

## How to Migrate Stripe Data to GCP BigQuery (Step 2)

0. Create a GCP account, enable the BigQuery API, and fill .env with `GCP_PROJECT_ID` and `BQ_DATASET`. Refer to .env.example for the required format.
1. Activate the Python virtual environment from the previous section.

### mac/OS

```bash
brew install --cask google-cloud-sdk
gcloud init
gcloud config set project YOUR_PROJECT_ID
gcloud auth application-default login
python3 export_stripe_to_big_query.py
```

### Linux

```bash
sudo snap install google-cloud-cli --classic
gcloud init
gcloud config set project YOUR_PROJECT_ID
gcloud auth application-default login
python3 export_stripe_to_big_query.py
```

### Windows

```bash
gcloud init
gcloud config set project YOUR_PROJECT_ID
gcloud auth application-default login
python export_stripe_to_big_query.py
```

To see the logic used to export stripe data into bigquery tables , see [EXPORT_TO_BIGQUERY_PLAN](./plans/SCRIPT_PLAN.md)

## How to run BigQuery SQL to find monthly MRR (Step 3)

copy sql from [bq_calculate_mrr.sql](./sql/bq_calculate_mrr.sql) and run it in the BigQuery console.

it should return a table with columns `month`, `mrr`,

other sql files in [sql](./sql/) can be run similarly and they exist for validation purposes.

## How to run the React Frontend (Step 4)

1. create a .env file in the frontend directory using the .env.example as a template.
2. retrieve the values from GCP and fill in the .env file.
3. run

```bash
npm install
npm run dev
```

4. open [http://localhost:3000](http://localhost:3000) in your browser.
