import json
import networkx as nx
import osmnx as ox


def cargar_grafo(path):
    return ox.load_graphml(path)

def cargar_datos_extra(path):
    with open(path, 'r', encoding='utf-8') as f:
        nodos = json.load(f)
    return nodos

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
