# Source: Marketing Funnel by Olist (real data)

- **Dataset:** Marketing Funnel by Olist
- **Publisher:** Olist (Brazilian e-commerce marketplace)
- **Link:** https://www.kaggle.com/datasets/olistbr/marketing-funnel-olist
- **License:** CC BY-NC-SA 4.0 (attribution, non-commercial, share-alike). Redistributed here unchanged, for non-commercial portfolio use, with attribution.

## Files

| File | Rows | Description |
|---|---|---|
| `olist_marketing_qualified_leads_dataset.csv` | 8,000 | Sellers who filled in a sign-up form on a landing page (Jun 2017 – May 2018): `mql_id`, `first_contact_date`, `landing_page_id`, `origin` (marketing channel) |
| `olist_closed_deals_dataset.csv` | 842 | Leads the sales team closed (won Dec 2017 – Nov 2018): sales development rep (`sdr_id`), sales rep (`sr_id`), `won_date`, `business_segment`, `lead_type`, `lead_behaviour_profile`, and more |

Join key: `mql_id`. Ids are anonymised hashes in the original data.

## How to re-download

The files are included so the project runs without a Kaggle account. To fetch them yourself:

```bash
pip install kaggle      # needs a Kaggle API token in ~/.kaggle/kaggle.json
kaggle datasets download -d olistbr/marketing-funnel-olist -p data/real_olist --unzip
```
