# Motor Insurance Portfolio Dashboard

Python + Streamlit + Plotly: 6-page interactive Motor Insurance analytics dashboard.

## Setup

```bash
pip install -r requirements.txt
streamlit run app.py
```

Place **your real dataset** at `data/motor_dashboard.csv`. If absent, the app asks for an upload. No synthetic business results are shown.

## Global UseEst filter (on all six pages)

The **UseEst** control in the global left sidebar defaults to **All**. Choose **True**, **False**, or **All**. This choice and the other global filters persist when navigating pages because their widgets are rendered in the app entrypoint (`app.py`) before `st.navigation(...).run()`.

- True: records with Boolean `True` or recognized strings `true`, `1`, `yes`, `t`.
- False: records with Boolean `False` or recognized strings `false`, `0`, `no`, `f`.
- All: **every record**, including missing/unrecognized UseEst values. Missing values are excluded by True and False, and are never recoded to False.

Original `UseEst` is preserved. `cal_UseEst_Bool` is a derived nullable Boolean.

## Mathematical conventions

- Loss Ratio = SUM(Ult Loss)/SUM(Earned Premium)
- Frequency = SUM(Ult Claim Count)/SUM(Earned Exposure) (assuming policy-year exposure)
- Severity = SUM(Ult Loss)/SUM(Ult Claim Count)
- Loss Cost = SUM(Ult Loss)/SUM(Earned Exposure)
- Renew Mix = SUM(Renew Policy Count)/(SUM(New Policy Count)+SUM(Renew Policy Count)). **Not a retention rate**.
- Financial aggregation is strict: any missing/non-numeric value in a source field makes that *specific aggregate field* unavailable (N/A), rather than treating it as zero. This is deliberately conservative. Filter or correct source records where appropriate.
- Cal_ row-level ratios, if present, are never averaged; all ratios are recomputed after filtering and grouping.
- Invalid, zero, or negative denominators yield N/A; source nulls and source columns are not overwritten.
- Risk threshold defaults (60% / 75%) are illustrative monitoring assumptions, not actuarially validated or regulatory thresholds.
- Displays the 12 quarterly positions from 2024 Q1 to 2026 Q4; periods not in data remain blank/N/A.
- New/Renew normalization recognizes New, Renew and Renewal. Any other category is excluded from the two-business mix but remains in the overall portfolio.
- Motor code is loaded as text so values like `1.10A` survive.

## Caveats

- This dataset is already aggregated. Confirm record grain, whether policies/exposures can be summed over time, premium and ultimate-loss valuation dates, and whether periods overlap before business decisions.
- Source-level partial missing data may suppress some entire-group ratios rather than silently undercount loss.
- Source values are left unaltered; normalized copies (where necessary) have a `cal_` prefix.
- All chart controls filter through common global slicers; Plotly selections are not claimed as fully synchronized clickable Power BI cross-filters. Use the sidebar slicers for consistent cross-page filtering.
- HTML/JS chart image exporting and expandable AG Grid hierarchies aren't installed. Matrix drill-down uses selectable group-by levels and sortable Streamlit tables.
- Claims component totals may differ from total ultimate loss; reconciliation displayed in the Claims page.
- Sensitive insurance data: do not publish actual customer/agent-level data on a public Streamlit host without company approval, access controls and privacy review. Public share links reveal hosted datasets to permitted viewers.

## Tests

```bash
python -m pytest -q
```
