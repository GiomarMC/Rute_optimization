import numpy as np

PESO_TACO = 300
CAPACIDAD_CAMION = 5000
AUTONOMIA_KM = 5
CANT_CAMIONES = 3

def calcular_ahorros(tachos, centro_idx, matriz):
    ahorros = []
    for i in range(len(tachos)):
        for j in range(i + 1, len(tachos)):
            ni, nj = tachos[i], tachos[j]
            ahorro = matriz[centro_idx][ni] + matriz[centro_idx][nj] - matriz[ni][nj]
            ahorros.append((ahorro, ni, nj))
    return sorted(ahorros, reverse=True)

def construir_rutas(tachos, centro_idx, matriz):
    rutas = []
    tachos_usados = set()
    ahorros = calcular_ahorros(tachos, centro_idx, matriz)

    for ahorro, ni, nj in ahorros:
        if ni in tachos_usados or nj in tachos_usados:
            continue
        rutas.append([centro_idx, ni, nj, centro_idx])
        tachos_usados.update([ni, nj])

    for t in tachos:
        if t not in tachos_usados:
            rutas.append([centro_idx, t, centro_idx])

    return rutas

def distancia_km(metros):
    return metros / 1000

def buscar_gasolinera(origen, gasolineras, matriz):
    return min(gasolineras, key=lambda g: matriz[origen][g])

def optimizar_rutas_distribuidas(rutas_brutas, matriz, indice_a_nodo, centro_idx, vertedero_idx, gasolineras_idx):
    rutas_finales = []
    camiones = [[] for _ in range(CANT_CAMIONES)]
    tachos_recolectados_global = set()

    # Distribuir rutas en round robin
    for i, ruta in enumerate(rutas_brutas):
        camiones[i % CANT_CAMIONES].append(ruta)

    for i, rutas_camion in enumerate(camiones):
        carga = 0
        combustible = AUTONOMIA_KM
        distancia_total = 0
        ruta_real = []
        origen = centro_idx

        for subruta in rutas_camion:
            for j in range(1, len(subruta) - 1):
                destino = subruta[j]

                if not np.isfinite(matriz[origen][destino]):
                    print(f"⚠️ Camión {i+1} omitió salto inválido: {origen} → {destino} (distancia = inf)")
                    continue

                dist_km = matriz[origen][destino]

                if dist_km > combustible:
                    gas = buscar_gasolinera(origen, gasolineras_idx, matriz)
                    distancia_total += (matriz[origen][gas])
                    ruta_real.append(gas)
                    combustible = AUTONOMIA_KM
                    origen = gas
                    dist_km = (matriz[origen][destino])

                if carga + PESO_TACO > CAPACIDAD_CAMION:
                    distancia_total += (matriz[origen][vertedero_idx])
                    ruta_real.append(vertedero_idx)
                    combustible -= (matriz[origen][vertedero_idx])
                    carga = 0
                    origen = vertedero_idx

                combustible -= dist_km
                distancia_total += dist_km
                ruta_real.append(destino)
                carga += PESO_TACO
                origen = destino
                tachos_recolectados_global.add(destino)

        if ruta_real and ruta_real[-1] != vertedero_idx:
            if np.isfinite(matriz[origen][vertedero_idx]):
                distancia_total += (matriz[origen][vertedero_idx])
                ruta_real.append(vertedero_idx)
                origen = vertedero_idx
            else:
                print(f"⚠️ Camión {i+1} no pudo ir al vertedero desde {origen} (sin conexión)")

        if np.isfinite(matriz[origen][centro_idx]):
            distancia_total += (matriz[origen][centro_idx])
            ruta_real.append(centro_idx)
        else:
            print(f"⚠️ Camión {i+1} no pudo regresar al centro desde {origen} (sin conexión)")

        rutas_finales.append({
            "camion": i + 1,
            "ruta": [indice_a_nodo[idx] for idx in [centro_idx] + ruta_real],
            "distancia_total_m": round(distancia_total, 2),
            "tachos_recolectados": list(tachos_recolectados_global)
        })

    return rutas_finales
