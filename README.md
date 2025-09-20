# neuraltwin

```
py -3.12 -m venv .venv
.venv/Scripts/activate
pip install faker ipykernel matplotlib pandas reportlab pycaret
```

## Wagon simulator parameters: `parts`, `baselines`, and `degradation rates`

The data-generation simulator (`src/data_generation/wagon_data_generation/wagon_simulator.py`) models component wear and sensor drift using three main concepts:

- `parts`: a dict of components modeled with simple Weibull-like failure dynamics. Each part entry is a mapping with keys:
  - `lambda0`: base hazard rate (per day) used as the starting failure intensity
  - `lifetime`: a scaling constant (days) that controls how quickly the hazard increases with age
  - `beta`: a shape factor that controls how the hazard grows with time (Weibull-like exponent)
  - runtime fields added by the simulator: `failed` (bool), `last_replacement` (datetime), and `failures` (list)

  Example snippet from the simulator:

  ```python
  parts = {
      "brakes": {"lambda0": 0.0003, "lifetime": 800, "beta": 2.0},
      "axle": {"lambda0": 0.0002, "lifetime": 1200, "beta": 1.8},
      "battery": {"lambda0": 0.0001, "lifetime": 600, "beta": 2.2},
      "cooling": {"lambda0": 0.0004, "lifetime": 500, "beta": 2.5},
  }
  ```

  How failures are sampled (simplified):
  - For each part the code computes an instantaneous hazard `lam = lambda0 * (1 + age / lifetime) ** beta` where `age` is days since `last_replacement`.
  - The failure probability for that day is `p_fail = min(1.0, lam)` and a uniform random sample (`np.random.rand()`) determines if a failure occurs.

- `baselines`: a set of nominal, healthy sensor values used as a starting point for simulated readings. Current baseline keys and units:
  - `speed`: km/h
  - `brake`: bar
  - `temp`: °C
  - `vibration`: mm/s
  - `battery`: percent (%)

  Example:

  ```python
  BASELINES = {
      "speed": 60,
      "brake": 5,
      "temp": 40,
      "vibration": 2,
      "battery": 100,
  }
  ```

- `degradation rates`: small per-day additive changes applied to baselines to simulate drift and wear. They are applied as `value = baseline + rate * age + noise` for non-failure days.

  Example:

  ```python
  DEGRADATION_RATES = {
      "speed": -0.02,      # km/h per day (slower over time)
      "brake": +0.005,     # bar per day (braking worsens)
      "temp": +0.02,       # °C per day (heating)
      "vibration": +0.005, # mm/s per day (more vibrations)
      "battery": -0.05,    # percent per day (capacity loss)
  }
  ```

  Notes:
  - `age` used in the formula is typically days since the relevant part's `last_replacement`.
  - Small floating-point rates accumulate over many days/months, producing realistic drift.
  - During a failure the simulator forces different, more extreme sensor values (e.g., `speed=0`, large temperature and vibration spikes) until the part's `repair_time`.

Tuning guidance
- To make failures rarer, reduce `lambda0` and/or increase `lifetime`.
- To simulate infant-failure (early-life) modes, increase `lambda0` or use a `beta < 1` to have early high hazard.
- To model gradual wear, increase `degradation rates` (absolute value) to amplify drift over time.
- Remember that `degradation rates` are applied per day; multiply by expected lifespan (days) to reason about long-term effects.

How to change behavior
- Edit the `parts`, `BASELINES`, or `DEGRADATION_RATES` dicts in `wagon_simulator.py` directly.
- For more advanced scenarios, you can refactor these dicts to be parameters of `WagonSimulator.__init__` and pass them in from a config or test harness.

Example: make brakes wear faster and battery drain slower

```python
parts["brakes"]["lambda0"] = 0.0006
DEGRADATION_RATES["battery"] = -0.01
```

If you want, I can also extract these tables into a YAML/JSON config file and load them at runtime so you can tweak parameters without editing code.