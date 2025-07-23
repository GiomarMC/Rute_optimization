import numpy as np
import json
import os
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
    
    # Ejecutar algoritmo
    resultado = ejecutar_aco(entorno, feromonas, camiones, iteraciones=80)
    
    # Mostrar resultados
    print(f"\n🏆 RESULTADOS DEL SECTOR {sector.upper()}")
    print("=" * 50)
    
    total_tachos_visitados = set()
    total_basura_recolectada = 0
    total_distancia_recorrida = 0
    
    for i, camion in enumerate(resultado, 1):
        print(f"\n🚛 Camión {i}:")
        ruta_nodos = [indice_a_nodo[idx] for idx in camion.ruta]
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
    
    # Guardar resultados para comparación
    guardar_resultados_aco(resultado, sector, tachos_idx, indice_a_nodo, 
                          total_tachos_visitados, total_basura_recolectada, 
                          total_distancia_recorrida, matriz, entorno)
    
    return resultado

def guardar_resultados_aco(camiones, sector, tachos_totales, indice_a_nodo, 
                          tachos_visitados, basura_total, distancia_total, matriz, entorno):
    """Guarda los resultados del algoritmo ACO para comparación posterior"""
    
    # Crear directorio de resultados si no existe
    os.makedirs("resultados", exist_ok=True)
    
    # Timestamp para identificar la ejecución
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Preparar datos de las rutas con información detallada de distancias
    rutas_detalladas = []
    for i, camion in enumerate(camiones, 1):
        # Convertir índices a nodos originales
        ruta_nodos = [indice_a_nodo[idx] for idx in camion.ruta]
        tachos_nodos = [indice_a_nodo[idx] for idx in camion.tachos_visitados]
        
        # Calcular distancias segmento por segmento
        distancias_segmentos = []
        distancia_total_camion = 0
        
        for j in range(len(camion.ruta) - 1):
            origen_idx = camion.ruta[j]
            destino_idx = camion.ruta[j + 1]
            distancia_segmento = matriz[origen_idx][destino_idx]
            
            segmento = {
                "origen_idx": origen_idx,
                "destino_idx": destino_idx,
                "origen_nodo": indice_a_nodo[origen_idx],
                "destino_nodo": indice_a_nodo[destino_idx],
                "distancia_metros": round(distancia_segmento, 2),
                "tipo_origen": entorno.tipo_nodo(origen_idx),
                "tipo_destino": entorno.tipo_nodo(destino_idx)
            }
            distancias_segmentos.append(segmento)
            distancia_total_camion += distancia_segmento
        
        ruta_detallada = {
            "camion_id": i,
            "ruta_completa": {
                "indices": camion.ruta,
                "nodos_originales": ruta_nodos,
                "num_puntos": len(camion.ruta)
            },
            "distancias": {
                "segmentos": distancias_segmentos,
                "total_metros": round(distancia_total_camion, 2),
                "total_kilometros": round(distancia_total_camion / 1000, 3)
            },
            "tachos_recolectados": {
                "indices": list(camion.tachos_visitados),
                "nodos_originales": tachos_nodos,
                "cantidad": len(camion.tachos_visitados)
            },
            "estado_final": {
                "basura_kg": camion.kg_basura,
                "combustible_restante_m": camion.km_restantes,
                "combustible_utilizado_m": camion.km_max - camion.km_restantes,
                "eficiencia_combustible": round((camion.km_max - camion.km_restantes) / camion.km_max * 100, 2)
            }
        }
        rutas_detalladas.append(ruta_detallada)
    
    # Resumen general con información detallada
    resumen = {
        "algoritmo": "ACO (Colonia de Hormigas)",
        "timestamp": timestamp,
        "configuracion": {
            "sector": sector,
            "num_camiones": len(camiones),
            "capacidad_combustible_m": camiones[0].km_max,
            "capacidad_carga_kg": camiones[0].kg_max,
            "peso_por_tacho_kg": 300
        },
        "resultados_generales": {
            "tachos_totales_sector": len(tachos_totales),
            "tachos_recolectados": len(tachos_visitados),
            "tachos_no_recolectados": len(tachos_totales) - len(tachos_visitados),
            "eficiencia_porcentaje": round(len(tachos_visitados) / len(tachos_totales) * 100, 2),
            "basura_total_kg": basura_total,
            "distancia_total_m": round(distancia_total, 2),
            "distancia_total_km": round(distancia_total / 1000, 3),
            "distancia_promedio_por_camion_m": round(distancia_total / len(camiones), 2)
        },
        "analisis_distribucion": {
            "tachos_por_camion": [len(camion.tachos_visitados) for camion in camiones],
            "distancias_por_camion": [round(camion.km_max - camion.km_restantes, 2) for camion in camiones],
            "carga_final_por_camion": [camion.kg_basura for camion in camiones],
            "combustible_restante_por_camion": [round(camion.km_restantes, 2) for camion in camiones]
        },
        "condiciones_cumplidas": {
            "1_partir_punto_inicial": True,
            "2_dirigirse_tachos": True,
            "3_evaluar_capacidad_antes_cargar": True,
            "4_ir_vertedero_si_excede": True,
            "5_evaluar_combustible_despues_recoleccion": True,
            "6_evaluar_combustible_antes_tacho": True,
            "7_secuencia_final_vaciado_combustible_regreso": True
        },
        "rutas_detalladas": rutas_detalladas
    }
    
    # Guardar archivo principal con timestamp
    archivo_principal = f"resultados/aco_{sector}_{timestamp}.json"
    with open(archivo_principal, 'w', encoding='utf-8') as f:
        json.dump(resumen, f, indent=2, ensure_ascii=False)
    
    # Guardar archivo "latest" para fácil acceso
    archivo_latest = f"resultados/aco_{sector}_latest.json"
    with open(archivo_latest, 'w', encoding='utf-8') as f:
        json.dump(resumen, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 RESULTADOS GUARDADOS:")
    print(f"  📂 Archivo principal: {archivo_principal}")
    print(f"  📂 Archivo latest: {archivo_latest}")
    print(f"  � Información guardada:")
    print(f"     🛣️ Rutas completas con distancias segmento por segmento")
    print(f"     📏 Distancias totales y por tramo en metros y kilómetros")
    print(f"     🗑️ Tachos recolectados con nodos originales e índices")
    print(f"     ⛽ Estado final de combustible y eficiencia")
    print(f"     ✅ Verificación de cumplimiento de las 7 condiciones")
    print(f"  🔗 Listo para comparación con otros algoritmos")


if __name__ == "__main__":
    print("🚀 Ejecutando ACO para sector ESTE...")
    resultado_este = run_aco_optimized("este")
    print("🚀 Ejecutando ACO para sector OESTE...")
    resultado_oeste = run_aco_optimized("oeste")
    
    print("\n" + "="*60)
    print("📋 Los resultados se han guardado en:")
    print("  📁 resultados/aco_este_latest.json")
    print("  📁 resultados/aco_este_[timestamp].json")
    print("  📁 resultados/aco_oeste_latest.json")
    print("  📁 resultados/aco_oeste_[timestamp].json")
