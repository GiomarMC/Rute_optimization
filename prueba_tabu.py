from algoritmos.busqueda_tabu.tabu import TabuSearch, mostrar_rutas
from instancias.cargar_datos import cargar_matriz_y_indices
import json
import random

# === Cargar la matriz de distancias y los índices ===
matriz, nodo_a_indice, indice_a_nodo = cargar_matriz_y_indices()

# === Cargar datos extra ===
with open("data/datos_extra.json", "r") as f:
    datos = json.load(f)

# === Zona de trabajo: 'este' o 'oeste' ===
zona = "este"

# === Obtener nodos clave ===
centro = nodo_a_indice[datos["nodo_centro"]]
vertedero = nodo_a_indice[datos["nodo_vertedero"]]
gasolineras = [nodo_a_indice[n] for n in datos["puntos_gasolineras"]]
tachos_zona = datos["tachos_este"] if zona == "este" else datos["tachos_oeste"]
tachos_actuales_idx = [nodo_a_indice[n] for n in tachos_zona]
# === Simular demandas en kg ===
random.seed(42)
demandas = {nodo_a_indice[n]: random.randint(300, 800) for n in tachos_zona}

# === Crear instancia de TabuSearch ===
ts = TabuSearch(
    matriz=matriz,
    nodo_a_indice=nodo_a_indice,
    indice_a_nodo=indice_a_nodo,
    demandas=demandas,
    centro_idx=centro,
    vertedero_idx=vertedero,
    gasolineras_idx=gasolineras,
    tachos_actuales_idx=tachos_actuales_idx,
    capacidad_camion=5.0,   # toneladas
    max_km=100.0,
    num_camiones=3,
    tam_tabu=7,
    zona=zona
)

# === Generar solución inicial válida ===
solucion_inicial = ts.generar_solucion_inicial()

# === Guardar la solución inicial en un archivo JSON ===
with open("data/soluciones/solucion_0.json", "w") as f:
    json.dump(solucion_inicial, f, indent=2)


# === Mostrar la solución con detalle ===
mostrar_rutas(ts, solucion_inicial)
