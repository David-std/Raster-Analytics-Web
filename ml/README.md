# ML

Model work is intentionally staged:

1. **Mock** — synthetic deterministic provider used only to exercise integration.
2. **Baseline** — first real, reproducible reference model built after profiling real data.
3. **CNN-RNN candidates** — alternative spatial-temporal configurations evaluated under the same data split and metrics.
4. **Selected model** — provider chosen from benchmarking evidence.

The current scaffold does not assume ConvLSTM, LSTM, GRU, a particular target representation, or a future forecasting horizon.
