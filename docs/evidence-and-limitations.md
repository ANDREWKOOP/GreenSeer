# Evidence types and limitations

GreenSeer keeps the following labels separate:

- **Observed source change:** a measured change in emissions, emissions intensity or operating activity at a regulated source.
- **Observed ambient change:** a measured change at an outdoor-air monitoring channel. It describes that monitor and period; weather, transport and concurrent changes may also matter.
- **Adjusted association:** a model-based relationship after selected variables are included. Prediction accuracy and SHAP explanations do not make it causal.
- **Causal estimate:** reserved for a design with a defensible comparison, timing, assumptions, diagnostics and uncertainty. The compact public examples do not claim this status.
- **Hypothetical scenario:** a modeled “what if” result, not an observed policy effect.

For the Sammis example, the outcome is source sulfur-dioxide mass divided by fuel-energy input. The before period is 2007–2009, the reported equipment-start year 2010 is omitted, and the after period is 2011–2013. The observed intensity changed from 1.264 to 0.167 lb SO2/MMBtu. Other controls, changes in fuel, unit operations, displacement and broader regulation could contribute. The result is not a direct measurement of nearby ambient SO2 or fine-particle exposure.

The held-out 2013 model comparison answers a prediction question: which approved method was closest to later measured source intensity? The test block contains 12 months. Lower root mean squared error is better. SHAP values show how inputs moved CatBoost predictions relative to its baseline; they do not isolate the scrubber’s causal effect.

Cross-sector cards preserve place, period, outcome, unit, evidence type and a case-specific boundary. They should not be averaged into one effectiveness score because a source rate, an ambient concentration and a bus operating cost describe different things.
