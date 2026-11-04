# GreenSeer architecture

GreenSeer separates five responsibilities so that an attractive explanation cannot silently change the study design.

1. **Evidence intake** retains an intervention description, source citation, place, dates and available outcomes.
2. **Interpretation** converts narrative records into a controlled schema: sector, mechanism, targeted emissions, plausible ambient pollutants, geography, timing and missing information. A language model can propose this structure, but proposals remain reviewable.
3. **Validated routing** uses deterministic rules and the evidence inventory to select an approved template. The public `route_intervention` function demonstrates this boundary. It never chooses a method because that method yields the largest result.
4. **Estimation and validation** execute the selected calculation or model and preserve the evaluation period, units, prediction error and evidence status.
5. **Explanation** combines the measured result with its provenance and claim boundary. SAS Retrieval Agent Manager supplied cited context in the hackathon implementation; it did not generate effect sizes.

The public example routes a power-plant scrubber record with monthly emissions and heat-input data to `source_intensity_existing_v1`. That template divides total sulfur-dioxide pounds by total heat input within each period. An industrial closure with only a compatible ambient monitor routes to `ambient_period_summary_v1`. A case without a verified operational date routes to review.

The architecture is **auto-ML inspired**, not unrestricted AutoML. Its flexibility comes from reusable templates and governed routing: many intervention records can share a small number of scientifically interpretable workflows. New templates should add explicit eligibility criteria, diagnostics, versioning and tests before the router can use them.
