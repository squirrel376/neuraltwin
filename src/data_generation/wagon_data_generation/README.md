# **README — Railroad Wagon Fleet Simulator**

## **Overview**

This project simulates a **fleet of railroad wagons** by:

* Generating **wagon specification PDFs**
* Simulating **IIoT sensor data** (speed, brake pressure, axle temperature, vibration, battery levels, etc.)
* Modeling **failures** and **repairs** based on realistic **probabilistic reliability functions**
* Producing **failure reports** per wagon
* Validating observed failures against expected theoretical values

This is useful for:

* Predictive maintenance testing
* IIoT cloud ingestion pipelines
* Failure modeling & anomaly detection
* Synthetic dataset generation

---

## **1. Mathematical Model**

The simulation is built on **probabilistic reliability theory** combined with **stochastic time-series modeling**.

### **1.1 Failure Probability**

Each wagon type has a **base failure rate** `λ_base` (failures per timestep).
For wagon $i$ of type $T$, we define the **effective failure rate**:

$$
\lambda_i = \lambda_{\text{base}}(T) \cdot \left(1 + \frac{\text{age}_i}{20}\right)
$$

Where:

* $\lambda_{\text{base}}(T)$ = type-specific constant
* $\text{age}_i$ = wagon age in years
* Older wagons are more failure-prone.

The **probability of failure** in one timestep:

$$
P_{\text{fail}} = 1 - e^{-\lambda_i} \approx \lambda_i
$$

(small-$\lambda$ approximation used here).

---

### **1.2 Time Series Generation**

For each wagon, we simulate **N timesteps**:

$$
N = \frac{\text{hours} \cdot 60}{\text{freq\_minutes}}
$$

At each timestep, we generate sensor readings:

| Sensor                | Healthy State (µ ± σ)   | Failure State Behavior  |
| --------------------- | ----------------------- | ----------------------- |
| Speed \[km/h]         | $\mathcal{N}(60, 5^2)$  | Drops to ≈ 0            |
| Brake Pressure \[bar] | $\mathcal{N}(5, 0.5^2)$ | Spikes                  |
| Axle Temp \[°C]       | $\mathcal{N}(40, 5^2)$  | $\mathcal{N}(80, 10^2)$ |
| Vibration \[g]        | $\mathcal{N}(2, 0.5^2)$ | $\mathcal{N}(10, 5^2)$  |
| Battery \[%]          | Slowly decreases        | Drops faster            |

Each sensor has **Gaussian noise** $\epsilon \sim \mathcal{N}(0, \sigma^2)$ added to mimic IIoT imperfections.

---

### **1.3 Failure & Repair Modeling**

If a failure occurs at timestep $t_f$:

1. Sensors shift into **failure mode**.
2. The wagon is down for **R timesteps**:

   $$
   R \sim \mathcal{U}(3, 20)
   $$
3. After repair, sensors return to normal distribution.

The failure events are logged:

* Start time
* Repair time
* Downtime (minutes)
* Cause of failure

---

### **1.4 Validation of Failure Rates**

After simulation, we check:

$$
E[F_T] = N_T \cdot N \cdot \lambda_{\text{base}}(T)
$$

Where:

* $E[F_T]$ = expected failures for type $T$
* $N_T$ = number of wagons of type $T$
* $N$ = timesteps per wagon

Then we compare to **observed failures** and report deviations.

Example validation output:

```
=== FAILURE VALIDATION REPORT ===
Boxcar              | Wagons:  2 | Expected Failures ≈ 1.0 | Observed: 1
Tank Car            | Wagons:  3 | Expected Failures ≈ 3.6 | Observed: 4
Refrigerator Car    | Wagons:  1 | Expected Failures ≈ 0.9 | Observed: 1
```

---

## **2. Implementation**

### **2.1 Project Structure**

```
railroad-simulator/
│── wagon_outputs/              # Generated PDFs + CSVs
│── simulator.py                # Main simulation code
│── README.md                  # Documentation
```

### **2.2 Main Classes**

#### **A. `Wagon`**

* Stores static metadata: ID, dimensions, type, manufacture date.
* Generates **wagon info PDF**.

#### **B. `WagonSimulator`**

* Builds **probabilistic model**.
* Simulates:

  * Sensor data time series
  * Failures & repairs
* Exports:

  * **Sensor CSV**
  * **Failure report PDF**

#### **C. `FleetManager`**

* Generates entire fleet.
* Runs all simulations.
* Performs **failure validation**.
* Aggregates statistics for the whole fleet.

---

## **3. Outputs**

### **3.1 PDFs**

For each wagon:

* **Info PDF:** Static specifications.
* **Failure PDF:** Table of failure & repair events.

Example snippet:

| Failure ID | Start Time | Repair Time | Downtime (min) | Cause         |
| ---------- | ---------- | ----------- | -------------- | ------------- |
| 1          | 2025-08-21 | 2025-08-21  | 120            | Brake Failure |

---

### **3.2 Sensor CSVs**

For each wagon, CSV file contains:

| timestamp        | speed\_kmh | brake\_bar | axle\_temp\_C | vibration\_g | battery\_% |
| ---------------- | ---------- | ---------- | ------------- | ------------ | ---------- |
| 2025-08-21 12:00 | 58.3       | 5.2        | 41.2          | 2.1          | 99.7       |
| 2025-08-21 12:30 | 60.7       | 5.1        | 40.5          | 2.0          | 99.6       |
| ...              | ...        | ...        | ...           | ...          | ...        |

---

## **4. How to Run**

### **4.1 Install Dependencies**

```bash
pip install faker numpy reportlab
```

### **4.2 Run Simulation**

```bash
python simulator.py
```

### **4.3 Configure Simulation**

Inside `simulator.py`, adjust:

```python
manager = FleetManager(num_wagons=10)
```

Also configurable:

* **Simulation hours**
* **Sensor sample frequency**
* **Base failure rates per type**

---

## **5. Extensions & Future Work**

* Generate a **fleet-level PDF dashboard** with:

  * Total failures per type
  * Mean Time Between Failures (MTBF)
  * Average downtime & cause distribution
* Integrate **streaming APIs** for real-time simulation.
* Add **predictive maintenance models**.
* Export directly to **SQL/InfluxDB/Kafka** for IIoT testing.

---

## **6. Summary**

This simulator:

* Generates **synthetic IIoT sensor datasets**
* Includes **failures, repairs, and noise**
* Validates against expected theoretical reliability
* Produces PDFs & CSVs for each wagon

It's a **self-contained framework** for **data-driven maintenance modeling** in the railroad domain.
