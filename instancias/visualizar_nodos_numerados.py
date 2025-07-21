import json
import osmnx as ox
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

G = ox.load_graphml("data/grafo_paucarpata.graphml")
with open("data/datos_extra.json") as f:
    datos = json.load(f)
with open("data/indices_nodos.json") as f:
    indice_a_nodo = {int(k): int(v) for k, v in json.load(f).items()}

nodo_a_indice = {nodo: idx for idx, nodo in indice_a_nodo.items()}

nodo_centro = datos["nodo_centro"]
nodo_vertedero = datos["nodo_vertedero"]
tachos_oeste = set(datos["tachos_oeste"])
tachos_este = set(datos["tachos_este"])
gasolineras = set(datos["puntos_gasolineras"])

posiciones = {nodo: (G.nodes[nodo]['x'], G.nodes[nodo]['y']) for nodo in indice_a_nodo.values()}

fig, ax = ox.plot_graph(G, node_size=0, edge_color='gray', show=False, close=False)
ax.set_facecolor('white')

def obtener_color(nodo):
    if nodo == nodo_centro:
        return 'red'
    elif nodo == nodo_vertedero:
        return 'blue'
    elif nodo in tachos_oeste:
        return 'green'
    elif nodo in tachos_este:
        return 'orange'
    elif nodo in gasolineras:
        return 'purple'
    else:
        return 'black'  # por si acaso

for idx, nodo in indice_a_nodo.items():
    x, y = posiciones[nodo]
    color = obtener_color(nodo)
    ax.scatter(x, y, s=30, color=color, zorder=5)
    ax.text(x, y, str(idx), fontsize=6, color='black', zorder=10)

leyenda = [
    mpatches.Patch(color='red', label='Centro'),
    mpatches.Patch(color='blue', label='Relleno sanitario'),
    mpatches.Patch(color='green', label='Tacho Oeste'),
    mpatches.Patch(color='orange', label='Tacho Este'),
    mpatches.Patch(color='purple', label='Gasolinera')
]
ax.legend(handles=leyenda, loc='lower right')

plt.savefig("instancias/grafo_numerado.png", dpi=500, bbox_inches="tight")
#plt.show()
