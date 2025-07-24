import numpy as np
import json
import os
import time
from datetime import datetime
from utils import cargar_datos_extra
from ant import Camion
from aco import ejecutar_aco


class EntornoACOOptimized:
    def __init__(self, matriz, centro, vertedero, tachos, gasolineras, nodo_a_indice, indice_a_nodo):
        self.matriz = matriz
        self.centro = centro
        self.vertedero = vertedero
        self.tachos = set(tachos)
        self.gasolineras = set(gasolineras)
        self.nodo_a_indice = nodo_a_indice
        self.indice_a_nodo = indice_a_nodo

    def tipo_nodo(self, nodo_idx):
        if nodo_idx in self.tachos:
            return "tacho"
        elif nodo_idx == self.vertedero:
            return "vertedero"
        elif nodo_idx in self.gasolineras:
            return "gasolinera"
        return "otro"
    
    def obtener_tachos_disponibles(self, tachos_visitados_sector):
        return list(self.tachos - tachos_visitados_sector)
    
    def distancia(self, origen, destino):
        try:
            if origen >= len(self.matriz) or destino >= len(self.matriz[0]):
                return float('inf')
            distancia = self.matriz[origen][destino]
            return distancia if distancia != 0 or origen == destino else float('inf')
        except:
            return float('inf')


def cargar_matriz_y_indices():
    matriz = np.load("../../data/matriz_distancias.npy")
    
    with open("../../data/indices_nodos.json", "r") as f:
        indice_a_nodo = json.load(f)
    with open("../../data/nodos_indices.json", "r") as f:
        nodo_a_indice = json.load(f)

    # Convertir claves a enteros
    indice_a_nodo = {int(k): v for k, v in indice_a_nodo.items()}
    nodo_a_indice = {int(k): v for k, v in nodo_a_indice.items()}

    return matriz, nodo_a_indice, indice_a_nodo

def run_aco_optimized(sector="este"):
    
    # Cargar datos
    datos = cargar_datos_extra("../../data/datos_extra.json")
    matriz, nodo_a_indice, indice_a_nodo = cargar_matriz_y_indices()
    
    # Convertir nodos a índices
    centro_idx = nodo_a_indice[datos["nodo_centro"]]
    vertedero_idx = nodo_a_indice[datos["nodo_vertedero"]]
    tachos_ids = datos[f"tachos_{sector}"]
    tachos_idx = [nodo_a_indice[t] for t in tachos_ids if t in nodo_a_indice]
    gasolineras_ids = datos["puntos_gasolineras"]
    gasolineras_idx = [nodo_a_indice[g] for g in gasolineras_ids if g in nodo_a_indice]
    
    print(f"📍 CONFIGURACIÓN DEL SECTOR {sector.upper()}:")
    print(f"  🏠 Centro: nodo {centro_idx} (original: {datos['nodo_centro']})")
    print(f"  🗑️ Vertedero: nodo {vertedero_idx} (original: {datos['nodo_vertedero']})")
    print(f"  📦 Tachos: {len(tachos_idx)} disponibles en el sector")
    print(f"  ⛽ Gasolineras: {len(gasolineras_idx)} disponibles")
    print(f"  🚛 Camiones: 3 (capacidad: 5000m combustible, 5000kg carga)")
    print("=" * 60)
    
    
    # Crear entorno con matriz optimizada
    entorno = EntornoACOOptimized(
        matriz, centro_idx, vertedero_idx, 
        tachos_idx, gasolineras_idx, 
        nodo_a_indice, indice_a_nodo
    )
    
    # Crear camiones con combustible estándar de 5km
    camiones = [Camion(centro_idx, km_max=5000, kg_max=5000) for _ in range(3)]
    feromonas = {}
    
    # Medir tiempo de ejecución
    start_time = time.time()
    
    # Ejecutar algoritmo
    resultado = ejecutar_aco(entorno, feromonas, camiones, iteraciones=80)
    
    # Calcular tiempo de ejecución
    execution_time = time.time() - start_time
    
    # Mostrar resultados
    print(f"\n🏆 RESULTADOS DEL SECTOR {sector.upper()}")
    print("=" * 50)
    
    total_tachos_visitados = set()
    total_basura_recolectada = 0
    total_distancia_recorrida = 0
    
    for i, camion in enumerate(resultado, 1):
        print(f"\n🚛 Camión {i}:")
        print(f"  📍 Puntos visitados: {len(camion.ruta)}")
        print(f"  🗑️ Tachos recolectados: {len(camion.tachos_visitados)}")
        print(f"  ⚖️ Basura final: {camion.kg_basura} kg")
        print(f"  ⛽ Combustible restante: {camion.km_restantes:.1f} m")
        
        # Calcular distancia total recorrida
        distancia_camion = camion.km_max - camion.km_restantes
        print(f"  🛣️ Distancia recorrida: {distancia_camion:.1f} m")
        
        total_tachos_visitados.update(camion.tachos_visitados)
        total_basura_recolectada += camion.kg_basura
        total_distancia_recorrida += distancia_camion
    
    print(f"\n📊 RESUMEN DEL SECTOR:")
    print(f"  🎯 Tachos totales del sector: {len(tachos_idx)}")
    print(f"  ✅ Tachos recolectados: {len(total_tachos_visitados)}")
    print(f"  📈 Eficiencia: {len(total_tachos_visitados)/len(tachos_idx)*100:.1f}%")
    print(f"  🗑️ Basura total recolectada: {total_basura_recolectada} kg")
    print(f"  🛣️ Distancia total recorrida: {total_distancia_recorrida:.1f} m")
    print(f"  📏 Distancia promedio por camión: {total_distancia_recorrida/3:.1f} m")
    print(f"  ⏱️ Tiempo de ejecución: {execution_time:.2f} segundos")
    
    # Guardar resultados para comparación
    archivo_guardado = guardar_resultados_aco(resultado, sector, indice_a_nodo,  
                          total_distancia_recorrida, execution_time)
    
    return resultado, archivo_guardado

def guardar_resultados_aco(camiones, sector, indice_a_nodo, 
                          distancia_total, execution_time):
    """Guarda los resultados del algoritmo ACO en formato simplificado para comparación"""
    
    # Crear directorio de resultados si no existe
    os.makedirs("resultados", exist_ok=True)
    
    # Timestamp para identificar la ejecución
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Convertir rutas de índices a nodos originales
    routes = []
    for camion in camiones:
        ruta_nodos = [indice_a_nodo[idx] for idx in camion.ruta]
        routes.append(ruta_nodos)
    
    # Crear el JSON en formato simplificado
    resultado_simplificado = {
        "total_distance": round(distancia_total, 2),
        "routes": routes,
        "execution_time": round(execution_time, 2),
        "algorithm": "ACO (Ant Colony Optimization)"
    }
    
    # Guardar archivo con timestamp
    archivo_timestamp = f"resultados/aco_{sector}_{timestamp}.json"
    with open(archivo_timestamp, 'w', encoding='utf-8') as f:
        json.dump(resultado_simplificado, f, indent=2, ensure_ascii=False)
    
    # Guardar archivo "latest" para fácil acceso
    archivo_latest = f"resultados/aco_{sector}_latest.json"
    with open(archivo_latest, 'w', encoding='utf-8') as f:
        json.dump(resultado_simplificado, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 RESULTADOS GUARDADOS:")
    print(f"  📂 Archivo principal: {archivo_timestamp}")
    print(f"  📂 Archivo latest: {archivo_latest}")
    print(f"  📊 Formato: Simplificado para comparación")
    print(f"  ⏱️ Tiempo de ejecución: {execution_time:.2f} segundos")
    print(f"  🛣️ Distancia total: {distancia_total:.2f} metros")
    print(f"  🚛 Número de rutas: {len(routes)}")
    
    return archivo_latest


if __name__ == "__main__":
    print("🚀 Ejecutando ACO para sector ESTE...")
    resultado_este, archivo_este = run_aco_optimized("este")
    
    print("\n🚀 Ejecutando ACO para sector OESTE...")
    resultado_oeste, archivo_oeste = run_aco_optimized("oeste")
    
    print("\n" + "="*60)
    print("📋 ARCHIVOS GENERADOS:")
    print(f"  📁 {archivo_este}")
    print(f"  📁 {archivo_oeste}")
    print("\n💡 Para generar mapas visuales, ejecuta:")
    print("  python visualizar_rutas.py")
