import time
import numpy as np
import json
from utils import cargar_datos_extra, cargar_matriz, cargar_indices
from clarke_wright import construir_rutas, optimizar_rutas_distribuidas

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Uso: python clarke_runner.py [este|oeste]")
        exit(1)

    sector = sys.argv[1].lower()
    if sector not in ["este", "oeste"]:
        print("Sector inválido. Usa 'este' o 'oeste'.")
        exit(1)

    # Cargar datos y matriz
    datos = cargar_datos_extra()
    matriz = cargar_matriz()
    nodo_a_indice, indice_a_nodo = cargar_indices()

    # Obtener nodos centro y vertedero con fallback
    centro_nodo = int(datos.get("centro", datos.get("nodo_centro")))
    vertedero_nodo = int(datos.get("vertedero", datos.get("nodo_vertedero")))

    if centro_nodo not in nodo_a_indice or vertedero_nodo not in nodo_a_indice:
        print("Error: centro o vertedero no están en el índice de nodos.")
        exit(1)

    centro_idx = nodo_a_indice[centro_nodo]
    vertedero_idx = nodo_a_indice[vertedero_nodo]
    gas_raw = datos.get("puntos_gasolineras", [])
    gasolineras_idx = [nodo_a_indice[g] for g in gas_raw if g in nodo_a_indice]


    # Filtrar tachos conectados al centro
    tachos_crudos = [nodo_a_indice[t] for t in datos[f"tachos_{sector}"]]
    tachos_idx = [t for t in tachos_crudos if np.isfinite(matriz[centro_idx][t])]
    total_tachos_originales = len(tachos_crudos)

    print(f"\n📍 CONFIGURACIÓN DEL SECTOR {sector.upper()}:")
    print(f"  🏠 Centro: {centro_idx}")
    print(f"  🗑️ Vertedero: {vertedero_idx}")
    print(f"  📦 Tachos totales (originales): {total_tachos_originales}")
    print(f"  📦 Tachos con conexión válida al centro: {len(tachos_idx)}")
    print(f"  ⛽ Gasolineras: {len(gasolineras_idx)}")
    print(f"  🚛 Camiones: 3")
    print("============================================================")

    # Ejecutar algoritmo
    start = time.time()
    rutas_brutas = construir_rutas(tachos_idx, centro_idx, matriz)
    rutas_finales = optimizar_rutas_distribuidas(
        rutas_brutas, matriz, indice_a_nodo,
        centro_idx, vertedero_idx, gasolineras_idx
    )
    end = time.time()

    print(f"\n🏁 RESULTADOS SECTOR {sector.upper()}")
    print("==================================================\n")

    distancia_total = 0
    tachos_recolectados_global = set()
    rutas_output = []

    for ruta in rutas_finales:
        print(f"  🚛 Camión {ruta['camion']}:")
        print(f"  📍 Ruta (nodos originales): {ruta['ruta']}")
        print(f"  🛣️ Distancia recorrida: {ruta['distancia_total_m']} km\n")
        distancia_total += ruta['distancia_total_m']
        tachos_recolectados_global.update(ruta["tachos_recolectados"])
        rutas_output.append([int(n) for n in ruta['ruta']])

    # Mostrar resumen
    print("📊 RESUMEN DEL SECTOR:")
    print(f"  ✅ Tachos recolectados: {len(tachos_recolectados_global)} / {total_tachos_originales}")
    print(f"  ⚠️ (De los {total_tachos_originales}, solo {len(tachos_idx)} eran accesibles desde el centro)")
    print(f"  📈 Cobertura real: {len(tachos_recolectados_global)/total_tachos_originales*100:.2f}%")
    print(f"  🛣️ Distancia total: {round(distancia_total, 2)} m")
    print(f"  📏 Promedio por camión: {round(distancia_total / 3, 2)} m")

    # Guardar JSON de resultados
    resultado_json = {
        "total_distance": round(distancia_total, 2),
        "routes": rutas_output,
        "execution_time": round(end - start, 2),
        "algorithm": "Clarke & Wright"
    }

    with open(f"algoritmos/clarke_wright/resultados_{sector}.json", "w", encoding="utf-8") as f:
        json.dump(resultado_json, f, indent=2)

    print(f"\n💾 Resultados guardados en 'resultados_{sector}.json'")
