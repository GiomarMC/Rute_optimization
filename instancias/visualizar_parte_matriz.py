import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Cargar matriz
matriz = np.load("data/matriz_distancias.npy")

# Cargar primeros 20x20
fragmento = matriz[:20, :20]

plt.figure(figsize=(12, 10))
sns.heatmap(fragmento, annot=True, fmt=".0f", cmap="YlGnBu")
plt.title("Fragmento 20x20 de la matriz de distancias (en metros)")
plt.xlabel("Nodo destino")
plt.ylabel("Nodo origen")
plt.tight_layout()
plt.show()
