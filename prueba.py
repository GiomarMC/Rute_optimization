import osmnx as ox
import matplotlib.pyplot as plt
import networkx as nx
import random
import json

# Funcion para definir un nodo en el grafo y graficarlo
def definir_nodo(G, nodo, ax, color, size, name=None):
    x = G.nodes[nodo]['x']
    y = G.nodes[nodo]['y']
    if name:
        ax.scatter(x, y, s=size, zorder=10, color=color, label=name)
    else:
        ax.scatter(x, y, s=size, zorder=10, color=color)

# Definir el lugar
lugar = "Paucarpata, Arequipa, Peru"

# Descargar el grafo vial (tipo 'drive' = calles para autos)
G = ox.graph_from_place(lugar, network_type="drive")

lat_centro = -16.429520243651115
lon_centro = -71.50308204976639

# Obtener los nodos cercanos al centro
nodo_centro = ox.distance.nearest_nodes(G, lon_centro, lat_centro)

# Encontrar nodo más alejado (vertedero)
longest_node = max(
    nx.single_source_dijkstra_path_length(
        G,
        nodo_centro,  # type: ignore
        weight="length"
        ),
    key=lambda k: nx.single_source_dijkstra_path_length(
        G,
        nodo_centro,  # type: ignore
        weight="length"
        )[k]
)
nodo_vertedero = longest_node

# Graficar el grafo base
fig, ax = ox.plot_graph(
    G,
    bgcolor='white',
    node_size=0,
    edge_color='gray',
    show=False,
    close=False
)

# Coordenadas de centro y vertedero
definir_nodo(G, nodo_centro, ax, 'red', 50, 'Centro')
definir_nodo(G, nodo_vertedero, ax, 'blue', 50, 'Relleno sanitario')

nodos = list(G.nodes(data=True))

# Calcular la mediana para dividir en este/oeste
longitudes = [data['x'] for _, data in nodos]
x_medio = sorted(longitudes)[len(longitudes) // 2]

nodos_oeste = [n for n, data in nodos if data['x'] <= x_medio]
nodos_este = [n for n, data in nodos if data['x'] > x_medio]

# Cantidad de tachos
total_tachos = 120
proporcion_oeste = len(nodos_oeste) / len(nodos)
num_tachos_oeste = round(total_tachos * proporcion_oeste)
num_tachos_este = total_tachos - num_tachos_oeste

# Selección aleatoria
tachos_oeste = random.sample(
    nodos_oeste,
    min(num_tachos_oeste, len(nodos_oeste))
    )
tachos_este = random.sample(
    nodos_este,
    min(num_tachos_este, len(nodos_este))
    )

# Dibujar tachos por sección con distinto color
definir_nodo(G, tachos_oeste[0], ax, 'green', 5, 'Tacho Oeste', )
for nodo in tachos_oeste[1:]:
    definir_nodo(G, nodo, ax, 'green', 5, None)

definir_nodo(G, tachos_este[0], ax, 'orange', 5, 'Tacho Este')
for nodo in tachos_este[1:]:
    definir_nodo(G, nodo, ax, 'orange', 5, None)

ax.legend()
plt.savefig('grafo_paucarpata.png', dpi=500, bbox_inches='tight')
plt.show()

# Guardar el grafo y los datos extra en archivos
ox.save_graphml(G, filepath='grafo_paucarpata.graphml')
datos_extra = {
    "nodo_centro": nodo_centro,
    "nodo_vertedero": nodo_vertedero,
    "tachos_oeste": tachos_oeste,
    "tachos_este": tachos_este,
}

with open('datos_extra.json', 'w') as f:
    json.dump(datos_extra, f, indent=4)
