# Stripe MRR Dashboard

## How to run data generator

0. create a .env file with Stripe API Key. Refer to .env.example for format

| Action                            | Windows (CMD/PowerShell)          | macOS / Linux (Bash/Zsh)          |
| :-------------------------------- | :-------------------------------- | :-------------------------------- |
| **1. Go to /scripts**             | `cd scripts`                      | `cd scripts`                      |
| **2. Create Virtual Environment** | `python -m venv .venv`            | `python3 -m venv .venv`           |
| **3. Activate Environment**       | `.venv\Scripts\activate`          | `source .venv/bin/activate`       |
| **4. Install Requirements**       | `pip install -r requirements.txt` | `pip install -r requirements.txt` |
| **5. Run populate_stripe.py**     | `python populate_stripe.py`       | `python3 populate_stripe.py`      |

To see the logic I used to generate test data for stripe [See Logic](plans/SCRIPT_PLAN.md)
