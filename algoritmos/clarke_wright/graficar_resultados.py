import osmnx as ox
import matplotlib.pyplot as plt
import networkx as nx
import json
import time

# Cargar grafo y datos
G = ox.load_graphml("data/grafo_paucarpata.graphml")
with open("data/datos_extra.json", "r") as f:
    datos = json.load(f)

# Función para dibujar puntos
def dibujar_nodo(G, nodo, ax, color, size, label=None, marker='o'):
    x, y = G.nodes[nodo]['x'], G.nodes[nodo]['y']
    ax.scatter(x, y, s=size, c=color, zorder=10, label=label, marker=marker)

# Función para trazar ruta entre nodos
def trazar_ruta(G, ruta, ax, color):
    for i in range(len(ruta) - 1):
        try:
            path = nx.shortest_path(G, source=ruta[i], target=ruta[i+1], weight='length')
            ox.plot_graph_route(G, path, route_color=color, route_linewidth=1.5, ax=ax, show=False, close=False, orig_dest_node_size=0)
        except:
            print(f"⚠️ Ruta no trazable: {ruta[i]} → {ruta[i+1]}")

# Colores para camiones
colores = ['red', 'blue', 'green', 'orange', 'purple', 'brown']

def graficar_sector(nombre_archivo_resultado, nombre_salida_img, sector_nombre):
    with open(nombre_archivo_resultado, "r") as f:
        resultado = json.load(f)

    fig, ax = ox.plot_graph(
    G,
    node_size=0,
    edge_color='lightgray',
    bgcolor='white',   # <-- esta línea fuerza fondo blanco
    show=False,
    close=False
)


    # Dibuja centro como cuadrado negro
    centro = datos["nodo_centro"]
    dibujar_nodo(G, centro, ax, "black", 60, "Punto de inicio", marker='s')

    total_tachos = 0

    for i, ruta in enumerate(resultado["routes"]):
        color = colores[i % len(colores)]
        trazar_ruta(G, ruta, ax, color)
        dibujar_nodo(G, ruta[0], ax, color, 10)  # primer nodo
        dibujar_nodo(G, ruta[-1], ax, color, 10)  # último nodo
        ax.plot([], [], color=color, label=f"Camión {i+1} ({len(ruta)} nodos)")
        total_tachos += len(ruta)

    titulo = f"Rutas de Recolección - Clarke & Wright\nSector: {sector_nombre.upper()} | Distancia Total: {resultado['total_distance'] * 1000:.1f}m | Tiempo: {resultado['execution_time']}s"
    ax.set_title(titulo, fontsize=10)
    ax.legend()
    plt.savefig(nombre_salida_img, dpi=400, bbox_inches='tight')
    plt.show()

# Ejecutar para ESTE y OESTE
graficar_sector("algoritmos/clarke_wright/resultados_este.json", "rutas_este.png", "ESTE")
graficar_sector("algoritmos/clarke_wright/resultados_oeste.json", "rutas_oeste.png", "OESTE")
