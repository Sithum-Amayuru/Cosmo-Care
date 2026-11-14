# COSMO CARE MVP

A dataset-independent astronaut health and mission-environment monitoring prototype.

## Important
- No real astronaut dataset is included.
- The current readings are manually entered / illustrative demo inputs.
- Alert settings are configurable prototype rules, not NASA-approved operational limits.
- This is not a medical device or certified spacecraft safety system.
- The five project references provide scientific context, not live data or numeric alarm limits.

## Run locally

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

## First MVP features
- Personal-baseline comparison for heart rate
- Sleep-duration demo rule
- Configurable environmental alert limits
- Configurable radiation alert limit
- Explanations for triggered rules
- CSV export of current readings

## Next development step
Replace manual inputs with a documented input interface for future sensor readings, while keeping source labels (real / simulated / manual) attached to every record.
