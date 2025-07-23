import numpy as np
import json

def cargar_matriz_y_indices():
    matriz = np.load("data/matriz_distancias.npy")
    
    with open("data/indices_nodos.json", "r") as f:
        indice_a_nodo = json.load(f)
    with open("data/nodos_indices.json", "r") as f:
        nodo_a_indice = json.load(f)

    indice_a_nodo = {int(k): v for k, v in indice_a_nodo.items()}
    nodo_a_indice = {int(k): v for k, v in nodo_a_indice.items()}

    return matriz, nodo_a_indice, indice_a_nodo
