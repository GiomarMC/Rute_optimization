import networkx as nx
import osmnx as ox
import numpy as np
import json
import os
import matplotlib.pyplot as plt

G = ox.load_graphml("data/grafo_paucarpata.graphml")
with open ("data/datos_extra.json", "r") as f:
    datos = json.load(f)

nodos_relevantes = (
    [datos["nodo_centro"]] +
    [datos["nodo_vertedero"]] +
    datos["tachos_este"] +
    datos["tachos_oeste"]+
    datos["puntos_gasolineras"]
)

indice_a_nodo = {}
for i in range(len(nodos_relevantes)):
    nodo = nodos_relevantes[i]
    indice_a_nodo[i] = nodo

nodo_a_indice = {}
for i, nodo in indice_a_nodo.items():
    nodo_a_indice[nodo] = i

with open("data/nodos_indices.json", "w") as f:
    json.dump(nodo_a_indice, f, indent=4)

matriz_path = "data/matriz_distancias.npy"
indices_path = "data/indices_nodos.json"

#if not os.path.exists(matriz_path) or not os.path.exists(indices_path):
n = len(nodos_relevantes)
matriz = np.zeros((n, n))

for i in range(n):
    for j in range(n):
        if i == j:
            matriz[i][j] = 0
        else:
            try:
                distancia = nx.shortest_path_length(G, 
                                                    source = indice_a_nodo[i], 
                                                    target = indice_a_nodo[j], 
                                                    weight = "length")
                matriz[i][j] = distancia

            except nx.NetworkXNoPath:
                matriz[i][j] = np.inf

np.save(matriz_path, matriz)
with open(indices_path, "w") as f:
    json.dump(indice_a_nodo, f, indent=4)
#else:
 #   print("Los archivos ya existen, no se generarán de nuevo.")

