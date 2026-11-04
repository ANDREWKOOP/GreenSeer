# SAS Viya implementation

The hackathon product was implemented as a multi-page SAS Visual Analytics report supported by prepared analytical tables and SAS Retrieval Agent Manager (RAM). The temporary hackathon tenant is no longer live, so this repository preserves screenshots, compact tables and reproducible local code rather than a dead tenant link.

## What ran in the hackathon environment

- **Discover:** sector cards opened intervention inventories and state-level maps.
- **Explore interventions:** a selected case exposed its date, outcome, observed change, time series and evidence boundary.
- **Modeling intelligence:** bar charts compared prediction error for the training-average baseline, ridge regression, gradient boosting and CatBoost on the same later period.
- **Prediction explanations:** measured and predicted series were paired with signed model contributions.
- **Methods and national coverage:** evidence inventories, source types and geographic coverage were summarized without treating every record as a measured effect.
- **SAS RAM:** curated evidence collections answered questions with citations and limitations. RAM provided retrieval and explanation, not model selection or effect estimation.

## Why SAS mattered

SAS Visual Analytics turned heterogeneous tables into one interactive decision-support surface: maps, selectors, linked tables, key-value displays and model comparisons. This made the distinction between intervention discovery, measured outcomes, model validation and cited explanation visible to a nontechnical user. The public GitHub Pages site reproduces the story and selected evidence but is not a replacement for the original interactive SAS report.
