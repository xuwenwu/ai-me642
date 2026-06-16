from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


thermo = pd.read_csv("thermo.csv")
ax = thermo.plot(x="Step", y=["Temp", "TotEng"])
ax.set_xlabel("Step")
ax.set_ylabel("Value")
Path("figures").mkdir(exist_ok=True)
plt.savefig("figures/thermo_summary.png", dpi=150)
