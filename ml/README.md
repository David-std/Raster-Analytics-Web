# Machine learning

The analytical implementation is staged around evidence rather than around a preselected neural-network architecture.

The current sequence is:

1. source qualification and reproducible snapshots;
2. spatial/temporal representation experiments;
3. feature and target contract with explicit leakage and missingness rules;
4. transparent statistical and tabular benchmarks;
5. CNN + recurrent candidates evaluated on the same frozen split and metrics;
6. selected model integrated behind the stable application provider contract.

The repository does not assume ConvLSTM, LSTM, GRU, a probability target, or a future-forecasting horizon before the data and benchmark evidence justify those decisions.

`ml/datasets` owns model-independent analytical contracts and dataset assembly guards. Source acquisition and feature derivation remain in `pipelines`; model-specific imputation, scaling, sampling and tensorization belong to the later training pipeline and must be fitted on development partitions only.
