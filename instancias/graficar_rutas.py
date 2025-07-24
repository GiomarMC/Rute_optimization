import networkx as nx
import matplotlib.pyplot as plt
import json

# Cargar grafo
G = nx.read_graphml("data/grafo_paucarpata.graphml")
# Convertir los pesos 'length' a float
for u, v, d in G.edges(data=True):
    if "length" in d:
        d["length"] = float(d["length"])


# Cargar índices
with open("data/indices_nodos.json", "r") as f:
    indice_a_nodo = json.load(f)
indice_a_nodo = {int(k): int(v) for k, v in indice_a_nodo.items()}

# Cargar rutas
with open("data/soluciones/solucion_0.json", "r") as f:
    rutas = json.load(f)
rutas = [[int(n) for n in ruta] for ruta in rutas]

# Posiciones de nodos
pos = {
    n: (float(G.nodes[n]["x"]), float(G.nodes[n]["y"]))
    for n in G.nodes
    if "x" in G.nodes[n] and "y" in G.nodes[n]
}

# Dibujar grafo base
fig, ax = plt.subplots(figsize=(10, 10))
nx.draw(G, pos, node_size=5, edge_color='lightgray', ax=ax)

# Dibujar rutas
colores = ["red", "blue", "green", "purple", "orange", "cyan"]

def dibujar_ruta(ruta, color, label):
    coords = []
    for idx in ruta:
        if idx not in indice_a_nodo:
            print(f"⚠️ Índice {idx} no está en indice_a_nodo")
            continue

        nodo_real = str(indice_a_nodo[idx])  # convertimos a string porque G usa nodos string
        if nodo_real not in G.nodes:
            print(f"⚠️ Nodo {nodo_real} no está en el grafo")
            continue

        x = float(G.nodes[nodo_real]["x"])
        y = float(G.nodes[nodo_real]["y"])
        coords.append((x, y))

    if len(coords) >= 2:
        xs, ys = zip(*coords)
        ax.plot(xs, ys, linewidth=2, color=color, label=label)

def dibujar_ruta_por_calles(G, indice_a_nodo, ruta, color, label):
    for i in range(len(ruta) - 1):
        idx_origen = ruta[i]
        idx_destino = ruta[i + 1]

        try:
            nodo_origen = str(indice_a_nodo[idx_origen])
            nodo_destino = str(indice_a_nodo[idx_destino])
            path = nx.shortest_path(G, source=nodo_origen, target=nodo_destino, weight='length')
            path_coords = [(float(G.nodes[n]['x']), float(G.nodes[n]['y'])) for n in path if n in G.nodes]

            if len(path_coords) >= 2:
                xs, ys = zip(*path_coords)
                ax.plot(xs, ys, linewidth=2, color=color, alpha=0.8, label=label if i == 0 else "")  # Solo 1 vez el label

        except nx.NetworkXNoPath:
            print(f"❌ Sin camino entre {nodo_origen} y {nodo_destino}")


for i, ruta in enumerate(rutas):
    #dibujar_ruta(ruta, colores[i % len(colores)], f"Camión {i+1}")
    dibujar_ruta_por_calles(G, indice_a_nodo, ruta, colores[i % len(colores)], f"Camión {i+1}")

ax.legend()
plt.title("Rutas de Solución Inicial")
plt.savefig("instancias/rutas_graficadas/rutas_solucion_inicial.png", dpi=300)
plt.show()
