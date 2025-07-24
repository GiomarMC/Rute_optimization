import json
import networkx as nx
import osmnx as ox
import numpy as np

def cargar_matriz(path="data/matriz_distancias.npy"):
    return np.load(path)

def cargar_grafo(path):
    return ox.load_graphml(path)

def cargar_datos_extra(path="data/datos_extra.json"):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def cargar_indices(path="data/indices_nodos.json"):
    with open(path, "r", encoding="utf-8") as f:
        nodos = json.load(f)
    
    nodo_a_indice = {}
    indice_a_nodo = {}
    for idx_str, nodo in nodos.items():
        idx = int(idx_str)
        nodo = int(nodo)
        nodo_a_indice[nodo] = idx
        indice_a_nodo[idx] = nodo

    return nodo_a_indice, indice_a_nodo

def construir_matriz_distancias(G, nodos_interes, archivo_salida="data/matriz_distancias.json"):
    matriz = {}
    for origen in nodos_interes:
        matriz[origen] = {}
        for destino in nodos_interes:
            if origen == destino:
                matriz[origen][destino] = 0
            else:
                try:
                    distancia = nx.shortest_path_length(
                        G, 
                        source=origen, 
                        target=destino, 
                        weight='length')
                    matriz[origen][destino] = distancia
                except:
                    matriz[origen][destino] = float('inf')
    with open(archivo_salida, 'w', encoding='utf-8') as f:
        json.dump(matriz, f)
    return matriz

def cargar_matriz_distancias(path="data/matriz_distancias.json"):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def obtener_distancia(matriz, origen, destino):
    return matriz.get(origen, {}).get(destino, float('inf'))

def convertir_matriz_para_acceso_rapido(matriz_anidada):
    matriz = {}
    for origen, destinos in matriz_anidada.items():
        for destino, distancia in destinos.items():
            matriz[(origen, destino)] = distancia
    return matriz
