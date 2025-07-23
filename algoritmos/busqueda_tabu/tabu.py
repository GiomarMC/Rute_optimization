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

    def ruta_pasa_por_gasolinera(self, ruta):
        """
        Verifica si la ruta pasa por una gasolinera entre el vertedero y el centro (regreso).
        Supone que la ruta tiene esta forma:
        [centro, ..., vertedero, ..., gasolinera, ..., centro]
        """
        try:
            idx_vertedero = ruta.index(self.vertedero)
            idx_centro_final = len(ruta) - 1  # Último nodo debe ser centro
            subtramo = ruta[idx_vertedero + 1 : idx_centro_final]
            for nodo in subtramo:
                if nodo in self.gasolineras:
                    return True
            return False
        except ValueError:
            # No se encontró vertedero o ruta mal formada
            return False

    def evaluar_costo(self, rutas):
        costo_total = 0
        penalidad = 0

        for ruta in rutas:
            carga = 0
            distancia = 0
            combustible_restante = self.max_km  # o tanque lleno

            for i in range(len(ruta) - 1):
                a = ruta[i]
                b = ruta[i+1]
                distancia += self.matriz[a][b]
                combustible_restante -= self.matriz[a][b]

                # Si el nodo b es un tacho, acumular carga
                if b in self.demandas:
                    carga += self.demandas[b]

            # Penalización por sobrecarga
            if carga > self.capacidad_kg:
                penalidad += 1000 * (carga - self.capacidad_kg)

            # Penalización si no recarga antes de que se acabe la gasolina
            if combustible_restante < 0:
                penalidad += 2000  # o proporcional al exceso

            # Penalización si no pasa por gasolinera antes de llegar al centro
            if not self.ruta_pasa_por_gasolinera(ruta, desde='vertedero', hasta='centro'):
                penalidad += 1500

            # Penalización si excede max_km sin recarga
            if distancia > self.max_km:
                penalidad += 1000 * ((distancia - self.max_km) / 10)

            costo_total += distancia

        return costo_total + penalidad


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



def mostrar_rutas(ts, rutas):
    print("=" * 60)
    print("📦 Evaluación de Solución de Rutas:")
    costo_total = 0
    penalizacion_total = 0

    for idx_ruta, ruta in enumerate(rutas):
        print(f"\n🛻 Ruta del Camión {idx_ruta + 1}:")
        #nodos_nombre = [ts.indice_a_nodo.get(n, f"?{n}") for n in ruta]
        print(" -> ".join(map(str, ruta)))  # Solo muestra los índices

        carga_kg = 0
        distancia_km = 0
        paso_por_gasolinera = False
        penalizaciones = []

        for i in range(len(ruta) - 1):
            origen = ruta[i]
            destino = ruta[i + 1]
            distancia = ts.matriz[origen][destino]
            distancia_km += distancia

            if destino in ts.demandas:
                carga_kg += ts.demandas[destino]

            if destino in ts.gasolineras:
                paso_por_gasolinera = True

        # Penalización por sobrecarga
        if carga_kg > ts.capacidad_kg:
            exceso = carga_kg - ts.capacidad_kg
            penal = exceso * 10  # penalización por exceso de kg
            penalizaciones.append((f"⚠️ Exceso de carga ({exceso:.2f} kg)", penal))

        # Penalización por no pasar por gasolinera si supera max_km
        if distancia_km > ts.max_km and not paso_por_gasolinera:
            exceso = distancia_km - ts.max_km
            penal = exceso * 5  # penalización por km sin gasolina
            penalizaciones.append((f"⛽ No pasó por gasolinera con exceso de {exceso:.2f} km", penal))

        # Mostrar resumen de la ruta
        print(f"🔁 Carga total: {carga_kg/1000:.2f} toneladas")
        print(f"📏 Distancia total: {distancia_km:.2f} km")

        penal_total = sum(p[1] for p in penalizaciones)
        for desc, val in penalizaciones:
            print(f"{desc}: +{val:.2f} penal")

        print(f"💰 Costo ruta sin penalización: {distancia_km:.2f}")
        print(f"💥 Penalización total: {penal_total:.2f}")
        print(f"💵 Costo total ruta: {distancia_km + penal_total:.2f}")

        # Acumular totales
        costo_total += distancia_km
        penalizacion_total += penal_total

    print("\n🔚 Resumen General:")
    print(f"✅ Costo total (sin penalizaciones): {costo_total:.2f}")
    print(f"🚫 Penalización total: {penalizacion_total:.2f}")
    print(f"💵 Costo final con penalización: {costo_total + penalizacion_total:.2f}")
    print("=" * 60)

