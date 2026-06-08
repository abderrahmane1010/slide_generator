---

# Exemple de Code Python

```python
import numpy as np
import matplotlib.pyplot as plt

def plot_sine_wave(frequency=1.0, duration=2.0):
    t = np.linspace(0, duration, 1000)
    y = np.sin(2 * np.pi * frequency * t)

    plt.figure(figsize=(10, 4))
    plt.plot(t, y, color="#006400", linewidth=2)
    plt.title("Onde sinusoïdale")
    plt.xlabel("Temps (s)")
    plt.ylabel("Amplitude")
    plt.grid(True, alpha=0.3)
    plt.show()

plot_sine_wave(frequency=3.0)
```

---
