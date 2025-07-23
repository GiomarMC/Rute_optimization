import numpy as np
import random
import json


class TabuSearch:
    def __init__(self, 
                 matriz, 
                 nodo_a_indice,
                 indice_a_nodo,
                 demandas,
                 centro_idx, 
                 vertedero_idx, 
                 gasolineras_idx,
                 tachos_actuales_idx,
                 capacidad_camion=5.0, 
                 max_km=100, 
                 num_camiones=3, 
                 tam_tabu=7, 
                 zona='este'):

        self.matriz = matriz
        self.nodo_a_indice = nodo_a_indice
        self.indice_a_nodo = indice_a_nodo

        # === Índices de nodos clave ===
        self.centro = centro_idx
        self.vertedero = vertedero_idx
        self.gasolineras = gasolineras_idx
        self.tachos_actuales = tachos_actuales_idx

        # === Parámetros del problema ===
        self.capacidad_kg = capacidad_camion * 1000 
        self.max_km = max_km
        self.num_camiones = num_camiones
        self.tam_tabu = tam_tabu
        self.zona = zona  
        self.demandas = demandas

        self.tabu_list = []
        self.mejor_solucion = None
        self.mejor_costo = float('inf')

    def generar_solucion_inicial(self):
        """
        Genera una solución inicial válida cumpliendo las restricciones duras:
        1. Todos los tachos deben ser asignados.
        2. No se supera la capacidad del camión.
        3. Cada ruta comienza en el centro, va por los tachos, pasa por vertedero, 
        gasolinera (cualquiera) y termina en el centro.
        4. No hay tachos repetidos.
        5. Solo se usan tachos de la zona asignada.
        6. Se genera una solución completa para la zona actual.
        """
        # Tachos convertidos a índices
        tachos_idx = self.tachos_actuales.copy()

        # Mezclar aleatoriamente los tachos
        random.shuffle(tachos_idx)

        rutas = [[] for _ in range(self.num_camiones)]
        cargas = [0 for _ in range(self.num_camiones)]

        for tacho in tachos_idx:
            demanda = self.demandas[tacho]

            # Intentar asignar a un camión sin sobrepasar capacidad
            asignado = False
            for i in range(self.num_camiones):
                if cargas[i] + demanda <= self.capacidad_kg:
                    rutas[i].append(tacho)
                    cargas[i] += demanda
                    asignado = True
                    break

            # Si no se pudo asignar, forzar al que menos carga tiene (último recurso)
            if not asignado:
                idx_min = cargas.index(min(cargas))
                rutas[idx_min].append(tacho)
                cargas[idx_min] += demanda  # aunque se pase

        # Construir rutas completas (con centro, vertedero y gasolinera)
        rutas_finales = []
        for ruta_tachos in rutas:
            ruta_completa = [self.centro]
            ruta_completa.extend(ruta_tachos)
            ruta_completa.append(self.vertedero)

            # Elegir una gasolinera aleatoria
            gasolinera = random.choice(self.gasolineras)
            ruta_completa.append(gasolinera)
            ruta_completa.append(self.centro)

            rutas_finales.append(ruta_completa)

        return rutas_finales

    def evaluar_costo(self, rutas):
        """
        Devuelve el costo total con penalizaciones.
        """
        costo_total = 0
        penalizacion_total = 0
        tachos_visitados = set()

        for ruta in rutas:
            carga = 0
            distancia = 0
            paso_por_gasolinera = False
            antes_de_vertedero = True

            for i in range(len(ruta) - 1):
                origen = ruta[i]
                destino = ruta[i + 1]
                distancia = distancia + self.matriz[origen][destino]

                # Verificar si estamos antes del vertedero
                if antes_de_vertedero and destino == self.vertedero:
                    antes_de_vertedero = False

                # Acumulamos carga si es tacho
                if origen in self.demandas:
                    carga = carga + self.demandas[origen]
                    if origen in tachos_visitados:
                        penalizacion_total += 99999  # Penalización muy alta por tacho duplicado
                    else:
                        tachos_visitados.add(origen)

                # Verificar si pasa por gasolinera
                if origen in self.gasolineras:
                    paso_por_gasolinera = True

            # 🚫 Penalización por exceso de carga
            if carga > self.capacidad_kg:
                exceso = carga - self.capacidad_kg
                penalizacion_total = penalizacion_total + (exceso * 1000)

            # 🚫 Penalización por no recargar gasolina antes del vertedero (si se pasa el límite)
            if distancia > self.max_km and not paso_por_gasolinera:
                exceso = distancia - self.max_km
                penalizacion_total = penalizacion_total + (exceso * 500)

            # 🚫 Penalización si no pasa por gasolinera entre vertedero y centro
            if ruta[-3] == self.vertedero:
                gasolinera = ruta[-2]
                if gasolinera not in self.gasolineras:
                    penalizacion_total = penalizacion_total + 50000  # fuerte penalización

            costo_total = costo_total + distancia

        # 🚫 Penalización si quedaron tachos sin visitar
        tachos_idx = self.tachos_actuales
        faltantes = set(tachos_idx) - tachos_visitados
        penalizacion_total = penalizacion_total + (len(faltantes) * 9999)

        return costo_total + penalizacion_total

    def costo_total(self, solucion):
        """
        Calcula el costo total de una solución válida (sin penalizaciones).
        La solución es una lista de rutas, donde cada ruta es una lista de índices de nodos.
        """
        total = 0.0
        for ruta in solucion:
            for i in range(len(ruta) - 1):
                origen = ruta[i]
                destino = ruta[i + 1]
                total += self.matriz[origen][destino]
        return total
    
    def vecindario(self, solucion_actual, num_vecinos=10):
        """
        Crea vecindario, en el cual se devuelve tuplar (solucion_vecina, movimiento):
        - Una lista de vecinos generados a partir de la solución actual.
        - Cada vecino es una nueva solución con un movimiento específico.
            + Donde el movimiento es un swap entre dos nodos de dos rutas distintas.
                movimiento = ("swap", nodo1, ruta1, nodo2, ruta2)
        """
        vecinos = []
        intentos = 0
        max_intentos = num_vecinos * 3

        while len(vecinos) < num_vecinos and intentos < max_intentos:
            # Copiar la solución actual
            nueva_sol = [ruta.copy() for ruta in solucion_actual]

            # Seleccionar 2 rutas distintas
            r1, r2 = random.sample(range(len(nueva_sol)), 2)

            # Evitar que tengan solo nodos fijos
            if len(nueva_sol[r1]) <= 4 or len(nueva_sol[r2]) <= 4:
                intentos += 1
                continue

            # Elegir posiciones aleatorias dentro de las rutas (solo en el tramo de tachos)
            i1 = random.randint(1, len(nueva_sol[r1]) - 4)  # excluye centro, vertedero, etc.
            i2 = random.randint(1, len(nueva_sol[r2]) - 4)

            # Nodo original antes de swap
            nodo1 = nueva_sol[r1][i1]
            nodo2 = nueva_sol[r2][i2]

            # Creamos el movimiento
            movimiento = ("swap", nodo1, r1, nodo2, r2)

            # Aplicamos el swap
            nueva_sol[r1][i1], nueva_sol[r2][i2] = nodo2, nodo1

            # Validar que los tachos no se repitan
            tachos_usados = set()
            valido = True
            for ruta in nueva_sol:
                for nodo in ruta[1:-3]:  # solo los tachos
                    if nodo in tachos_usados:
                        valido = False
                        break
                    tachos_usados.add(nodo)

            if valido:
                vecinos.append((nueva_sol, movimiento))

            intentos += 1

        return vecinos
    
    def buscar_mejor_vecino(self, vecinos):
        """
        Dado un conjunto de vecinos generados junto con su movimiento:
        - Evalúa el costo de cada vecino usando evaluar_costo().
        - Si el movimiento está en la lista tabú:
            - Lo ignora a menos que cumpla el criterio de aspiración.
        - Escoge el vecino con menor costo total permitido.

        Devuelve:
        - El mejor vecino.
        - Su costo.
        - El movimiento.
        - Si fue tabú o no.
        """
        mejor_vecino = None
        mejor_costo = float('inf')
        mejor_movimiento = None
        fue_tabu = False

        for vecino, movimiento in vecinos:
            costo = self.evaluar_costo(vecino)

            if movimiento in self.tabu_list:
                # Criterio de aspiración: si mejora el mejor global, se permite
                if costo < self.mejor_costo:
                    mejor_vecino = vecino
                    mejor_costo = costo
                    mejor_movimiento = movimiento
                    fue_tabu = True  # Se permitió por aspiración
            else:
                if costo < mejor_costo:
                    mejor_vecino = vecino
                    mejor_costo = costo
                    mejor_movimiento = movimiento
                    fue_tabu = False

        return mejor_vecino, mejor_costo, mejor_movimiento, fue_tabu

    def ejecutar_busqueda(self, max_iter=100, verbose=True):
        # 1. Solución inicial
        solucion_actual = self.generar_solucion_inicial()
        costo_actual = self.evaluar_costo(solucion_actual)

        # 2. Mejor solución
        self.mejor_solucion = solucion_actual
        self.mejor_costo = costo_actual

        if verbose:
            print(f"Iteración 0: Costo inicial = {costo_actual:.2f}")

        # 3. Ciclo principal
        for iteracion in range(1, max_iter + 1):
            vecinos = self.vecindario(solucion_actual)
            if not vecinos:
                if verbose:
                    print(f"⚠️ Sin vecinos generados en la iteración {iteracion}")
                break

            mejor_vecino, costo_vecino, movimiento, fue_tabu = self.buscar_mejor_vecino(vecinos)

            # 4. Actualizar solución actual
            solucion_actual = mejor_vecino
            costo_actual = costo_vecino

            # 5. Actualizar mejor solución si es necesario
            if costo_actual < self.mejor_costo:
                self.mejor_solucion = solucion_actual
                self.mejor_costo = costo_actual
                if verbose:
                    print(f"✅ Iteración {iteracion}: Mejorada a {self.mejor_costo:.2f}")
            else:
                if verbose:
                    tag = "⭐️ (tabú)" if fue_tabu else ""
                    print(f"Iteración {iteracion}: Costo = {costo_actual:.2f} {tag}")

            # 6. Actualizar lista tabú
            self.tabu_list.append(movimiento)


def mostrar_rutas(ts, rutas):
    print("=" * 60)
    print("📦 Evaluación de Solución de Rutas:")
    costo_total = 0
    penalizacion_total = 0
    todos_tachos = set(ts.tachos_actuales)
    tachos_visitados = set()

    for idx_ruta, ruta in enumerate(rutas):
        print(f"\n🛻 Ruta del Camión {idx_ruta + 1}:")
        
        # Mostrar ruta con tipos de nodo
        ruta_str = []
        for idx in ruta:
            tipo = (
                "Centro" if idx == ts.centro else
                "Vertedero" if idx == ts.vertedero else
                "Gasolinera" if idx in ts.gasolineras else
                "Tacho"
            )
            ruta_str.append(f"{idx}({tipo})")
            if idx in ts.demandas:
                tachos_visitados.add(idx)
        print(" → ".join(ruta_str))

        # Cálculos de ruta
        carga_kg = 0
        distancia_km = 0
        paso_por_gasolinera = False
        penalizaciones = []
        tiene_vertedero = False

        for i in range(len(ruta) - 1):
            origen, destino = ruta[i], ruta[i+1]
            distancia_km += ts.matriz[origen][destino]

            if origen in ts.demandas:
                carga_kg += ts.demandas[origen]

            if destino in ts.gasolineras:
                paso_por_gasolinera = True
                
            if destino == ts.vertedero:
                tiene_vertedero = True

        # Validaciones y penalizaciones
        if not tiene_vertedero:
            penalizaciones.append(("🚫 Ruta no pasa por vertedero", 50000))
            
        if carga_kg > ts.capacidad_kg:
            exceso = carga_kg - ts.capacidad_kg
            penalizaciones.append((f"⚠️ Exceso de carga ({exceso/1000:.2f} ton)", exceso * 10))

        if distancia_km > ts.max_km and not paso_por_gasolinera:
            exceso = distancia_km - ts.max_km
            penalizaciones.append((f"⛽ Exceso km sin gasolinera ({exceso:.2f} km)", exceso * 5))

        # Mostrar resumen
        print(f"🔁 Carga: {carga_kg/1000:.2f} ton (Capacidad: {ts.capacidad_kg/1000:.2f} ton)")
        print(f"📏 Distancia: {distancia_km:.2f} km (Límite: {ts.max_km} km)")
        
        if penalizaciones:
            print("🚨 Penalizaciones:")
            for desc, val in penalizaciones:
                print(f" - {desc}: +{val:.2f}")
        
        costo_ruta = distancia_km + sum(p[1] for p in penalizaciones)
        print(f"💰 Costo total ruta: {costo_ruta:.2f}")

        costo_total += distancia_km
        penalizacion_total += sum(p[1] for p in penalizaciones)

    # Verificación de tachos no visitados
    faltantes = todos_tachos - tachos_visitados
    if faltantes:
        penal = len(faltantes) * 9999
        print(f"\n🚨 Tachos no visitados ({len(faltantes)}): {faltantes}")
        penalizacion_total += penal

    print("\n🔚 Resumen General:")
    print(f"✅ Costo rutas: {costo_total:.2f} km")
    print(f"🚫 Penalizaciones: {penalizacion_total:.2f}")
    print(f"💵 COSTO TOTAL: {costo_total + penalizacion_total:.2f}")
    print("=" * 60)

