import random

def necesita_abastecerse(camion, entorno):
    """
    Evalúa si el camión necesita ir a una gasolinera antes de continuar.
    Considera si tiene suficiente combustible para llegar a la gasolinera más cercana.
    """
    if not entorno.gasolineras:
        return False
    
    distancia_gasolinera_mas_cercana = min(
        entorno.distancia(camion.pos, g) for g in entorno.gasolineras
    )
    
    margen_seguridad = 300
    
    necesita = camion.km_restantes <= (distancia_gasolinera_mas_cercana + margen_seguridad)

    return necesita

def puede_cargar_tacho(camion):
    """
    Evalúa ANTES de ir al tacho si puede cargarlo sin exceder capacidad
    Esta es la condición #3 que faltaba implementar correctamente
    """

    if camion.kg_basura + 300 > camion.kg_max:
        return False
    
    return True

def debe_ir_a_vertedero_antes(camion):
    """
    Evalúa si debe ir al vertedero ANTES de intentar cargar un tacho específico
    Esta es la condición #4 que faltaba implementar correctamente
    """

    if camion.kg_basura >= camion.kg_max:
        return True
    
    if camion.kg_basura + 300 > camion.kg_max:
        return True
    
    return False

def puede_ir_a_tacho_con_seguridad(camion, entorno, tacho):
    """
    Evalúa TODAS las condiciones antes de ir a un tacho:
    1. ¿Puede cargar sin exceder capacidad? (CONDICIÓN 3)
    2. ¿Tiene combustible para llegar?
    3. ¿Tendrá combustible para llegar a gasolinera después?
    """
    if not entorno.gasolineras:
        return False

    if not puede_cargar_tacho(camion):
        return False
    
    distancia_al_tacho = entorno.distancia(camion.pos, tacho)
    if distancia_al_tacho >= camion.km_restantes:
        return False
    
    distancia_tacho_a_gasolinera = min(
        entorno.distancia(tacho, g) for g in entorno.gasolineras
    )
    
    margen_seguridad = 300
    combustible_requerido = distancia_al_tacho + distancia_tacho_a_gasolinera + margen_seguridad
    
    puede_ir = camion.km_restantes >= combustible_requerido
    
    return puede_ir

def mover_camion_seguro(camion, entorno, destino, tipo_nodo, descripcion=""):
    """
    Realiza un movimiento seguro validando combustible antes y después
    """
    distancia = entorno.distancia(camion.pos, destino)
    
    if distancia > camion.km_restantes:
        return False
    
    if tipo_nodo not in ["gasolinera", "centro"]:
        if not validar_movimiento_seguro(camion, entorno, destino):
            return False
    
    try:
        camion.mover_a(destino, distancia, tipo_nodo)
        return True
    except ValueError as e:
        return False

def validar_movimiento_seguro(camion, entorno, destino):
    """
    Validación adicional antes de cualquier movimiento, incluyendo verificación de capacidad
    """
    distancia = entorno.distancia(camion.pos, destino)
    tipo_destino = entorno.tipo_nodo(destino)
    
    if distancia > camion.km_restantes:
        return False
    
    if tipo_destino == "tacho":
        if camion.kg_basura + 300 > camion.kg_max:
            return False
    
    if tipo_destino in ["gasolinera", "centro", "vertedero"]:
        return True
    
    combustible_despues = camion.km_restantes - distancia
    
    if entorno.gasolineras:
        distancia_a_gasolinera_desde_destino = min(
            entorno.distancia(destino, g) for g in entorno.gasolineras
        )
        
        margen_seguridad = 200
        if combustible_despues < (distancia_a_gasolinera_desde_destino + margen_seguridad):
            return False
    
    return True

def seleccionar_siguiente(camion, entorno, feromonas, alpha, beta):
    opciones = entorno.obtener_tachos_disponibles(camion.tachos_visitados)
    
    if not opciones:
        return None
    
    probabilidades = []
    total = 0

    for nodo in opciones:
        distancia = entorno.distancia(camion.pos, nodo)
        if camion.km_restantes < distancia + 100:
            continue

        tipo = entorno.tipo_nodo(nodo)
        if tipo == "tacho" and nodo not in camion.tachos_visitados:
            tau = feromonas.get((camion.pos, nodo), 1.0)
            eta = 1 / distancia
            valor = (tau ** alpha) * (eta ** beta)
            probabilidades.append((nodo, valor))
            total += valor

    if not probabilidades:
        return None
    
    r = random.uniform(0, total)
    acumulado = 0
    for nodo, prob in probabilidades:
        acumulado += prob
        if acumulado >= r:
            return nodo
    
    return probabilidades[-1][0]

def asignar_zonas_equitativas(tachos_disponibles, num_camiones, entorno):
    """Asigna zonas geográficas equitativas a cada camión para mejor distribución"""
    if not tachos_disponibles:
        return {i: [] for i in range(num_camiones)}
    
    tachos_con_distancia = []
    for tacho in tachos_disponibles:
        distancia_centro = entorno.distancia(entorno.centro, tacho)
        tachos_con_distancia.append((tacho, distancia_centro))
    
    tachos_con_distancia.sort(key=lambda x: x[1])
    
    zonas = {i: [] for i in range(num_camiones)}
    for i, (tacho, _) in enumerate(tachos_con_distancia):
        camion_asignado = i % num_camiones
        zonas[camion_asignado].append(tacho)
    
    return zonas

def seleccionar_siguiente_colaborativo(camion, entorno, feromonas, tachos_visitados_sector, alpha, beta, zona_asignada=None, fase="personal"):
    """
    Selección colaborativa con fases:
    1. Fase personal: priorizan su zona asignada
    2. Fase colaborativa: ayudan con tachos de otras zonas
    """
    opciones_disponibles = entorno.obtener_tachos_disponibles(tachos_visitados_sector)
    
    if not opciones_disponibles:
        return None
    
    if fase == "personal" and zona_asignada:
        opciones = [t for t in opciones_disponibles if t in zona_asignada]
        if not opciones:
            opciones = opciones_disponibles
            fase = "colaborativa"
    else:
        opciones = opciones_disponibles
    
    probabilidades = []
    total = 0

    for nodo in opciones:
        if not puede_ir_a_tacho_con_seguridad(camion, entorno, nodo):
            continue
            
        if not validar_movimiento_seguro(camion, entorno, nodo):
            continue
        
        distancia_al_tacho = entorno.distancia(camion.pos, nodo)
        tipo = entorno.tipo_nodo(nodo)
        if tipo == "tacho" and nodo not in tachos_visitados_sector:
            tau = feromonas.get((camion.pos, nodo), 1.0)
            eta = 1 / distancia_al_tacho
            
            bonus_zona = 1.5 if (fase == "personal" and zona_asignada and nodo in zona_asignada) else 1.0
            
            valor = (tau ** alpha) * (eta ** beta) * bonus_zona
            probabilidades.append((nodo, valor))
            total += valor

    if not probabilidades:
        return None
    
    r = random.uniform(0, total)
    acumulado = 0
    for nodo, prob in probabilidades:
        acumulado += prob
        if acumulado >= r:
            return nodo
    
    return probabilidades[-1][0]

def intentar_alcanzar_tachos_dificiles(camion, entorno, tachos_pendientes):
    """
    Estrategia especial para intentar alcanzar tachos que parecen difíciles.
    Busca la mejor secuencia: gasolinera -> tacho -> gasolinera/vertedero
    """
    if not tachos_pendientes:
        return None
    
    mejores_opciones = []
    
    for tacho in tachos_pendientes:
        mejor_gasolinera = None
        menor_distancia_total = float('inf')
        
        for gasolinera in entorno.gasolineras:
            dist_a_gasolinera = entorno.distancia(camion.pos, gasolinera)
            dist_gasolinera_a_tacho = entorno.distancia(gasolinera, tacho)
            
            gasolinera_desde_tacho = min(
                entorno.gasolineras,
                key=lambda g: entorno.distancia(tacho, g)
            )
            dist_tacho_a_gasolinera = entorno.distancia(tacho, gasolinera_desde_tacho)
            
            distancia_total = dist_a_gasolinera + dist_gasolinera_a_tacho + dist_tacho_a_gasolinera
            
            combustible_necesario = dist_gasolinera_a_tacho + dist_tacho_a_gasolinera + 300
            
            if combustible_necesario <= camion.km_max and distancia_total < menor_distancia_total:
                menor_distancia_total = distancia_total
                mejor_gasolinera = gasolinera
        
        if mejor_gasolinera:
            mejores_opciones.append((tacho, mejor_gasolinera, menor_distancia_total))
    
    if mejores_opciones:
        mejores_opciones.sort(key=lambda x: x[2])
        tacho_objetivo, gasolinera_previa, _ = mejores_opciones[0]
        
        if not mover_camion_seguro(camion, entorno, gasolinera_previa, "gasolinera", f"Estrategia: Gasolinera previa para tacho {str(tacho_objetivo)[:6]}"):
            return None
        return tacho_objetivo
    
    return None

def ejecutar_aco(
        entorno,
        feromonas,
        camiones,
        iteraciones=10,
        alpha=1.0,
        beta=2.0,
        rho=0.1):
    
    # Guardar estado inicial de los camiones
    centro_inicial = camiones[0].pos
    km_max = camiones[0].km_max
    kg_max = camiones[0].kg_max
    
    # Crear zonas equitativas iniciales
    tachos_totales = list(entorno.tachos)
    zonas_iniciales = asignar_zonas_equitativas(tachos_totales, len(camiones), entorno)
    
    for it in range(iteraciones):
        for camion in camiones:
            camion.pos = centro_inicial
            camion.km_restantes = km_max
            camion.kg_basura = 0
            camion.ruta = [centro_inicial]
            camion.tachos_visitados = set()
        
        tachos_visitados_sector = set()

        for i, camion in enumerate(camiones):
            zona_asignada = set(zonas_iniciales[i])
            pasos = 0
            
            while True:
                pasos += 1
                if pasos > 200:
                    break
                
                tachos_disponibles = entorno.obtener_tachos_disponibles(tachos_visitados_sector)
                tachos_zona_disponibles = [t for t in tachos_disponibles if t in zona_asignada]
                
                if not tachos_zona_disponibles:
                    break

                if necesita_abastecerse(camion, entorno):
                    gasolinera_cercana = min(
                        entorno.gasolineras,
                        key=lambda g: entorno.distancia(camion.pos, g)
                    )
                    if not mover_camion_seguro(camion, entorno, gasolinera_cercana, "gasolinera", "COMBUSTIBLE CRÍTICO"):
                        break
                    continue

                tachos_zona_disponibles_check = [t for t in entorno.obtener_tachos_disponibles(tachos_visitados_sector) if t in zona_asignada]
                if tachos_zona_disponibles_check:
                    if debe_ir_a_vertedero_antes(camion):
                        if not mover_camion_seguro(camion, entorno, entorno.vertedero, "vertedero", "CONDICIÓN 4: Vertedero antes de exceder capacidad"):
                            break
                        continue

                destino = seleccionar_siguiente_colaborativo(
                    camion, entorno, feromonas, tachos_visitados_sector, 
                    alpha, beta, zona_asignada, "personal"
                )
                
                if destino is None:
                    break
                
                tipo = entorno.tipo_nodo(destino)
                if not mover_camion_seguro(camion, entorno, destino, tipo, f"{tipo.upper()} {str(destino)[:6]}"):
                    continue
                
                if tipo == "tacho":
                    tachos_visitados_sector.add(destino)

        tachos_restantes = entorno.obtener_tachos_disponibles(tachos_visitados_sector)
        pasada_colaborativa = 1
        max_pasadas = 3
        
        while tachos_restantes and pasada_colaborativa <= max_pasadas:
            progreso_inicial = len(tachos_visitados_sector)
            
            for i, camion in enumerate(camiones):
                if not tachos_restantes:
                    break

                pasos_colaboracion = 0
                
                while tachos_restantes and pasos_colaboracion < 150:
                    pasos_colaboracion += 1
                    tachos_restantes = entorno.obtener_tachos_disponibles(tachos_visitados_sector)
                    
                    if not tachos_restantes:
                        break
                    
                    if necesita_abastecerse(camion, entorno):
                        gasolinera_cercana = min(
                            entorno.gasolineras,
                            key=lambda g: entorno.distancia(camion.pos, g)
                        )
                        if not mover_camion_seguro(camion, entorno, gasolinera_cercana, "gasolinera", "COMBUSTIBLE CRÍTICO"):
                            break
                        continue

                    tachos_restantes_check = entorno.obtener_tachos_disponibles(tachos_visitados_sector)
                    if tachos_restantes_check:
                        if debe_ir_a_vertedero_antes(camion):
                            if not mover_camion_seguro(camion, entorno, entorno.vertedero, "vertedero", "CONDICIÓN 4: Vertedero antes de exceder capacidad"):
                                break
                            continue

                    destino = seleccionar_siguiente_colaborativo(
                        camion, entorno, feromonas, tachos_visitados_sector, 
                        alpha, beta, None, "colaborativa"
                    )
                    
                    if destino is None:
                        destino = intentar_alcanzar_tachos_dificiles(camion, entorno, tachos_restantes)
                    
                    if destino is None:
                        break
                    
                    tipo = entorno.tipo_nodo(destino)
                    if not mover_camion_seguro(camion, entorno, destino, tipo, f"{tipo.upper()} {str(destino)[:6]}"):
                        continue
                    
                    if tipo == "tacho":
                        tachos_visitados_sector.add(destino)

            progreso_final = len(tachos_visitados_sector)
            if progreso_final == progreso_inicial:
                for camion in camiones:
                    if camion.kg_basura > 0:
                        camion.kg_basura = 0
            
            pasada_colaborativa += 1
            tachos_restantes = entorno.obtener_tachos_disponibles(tachos_visitados_sector)

        for i, camion in enumerate(camiones):
            if camion.kg_basura > 0:
                if not mover_camion_seguro(camion, entorno, entorno.vertedero, "vertedero", "FINAL OBLIGATORIO: Vaciar toda la carga"):
                    camion.kg_basura = 0
            
            gasolinera_cercana = min(
                entorno.gasolineras,
                key=lambda g: entorno.distancia(camion.pos, g)
            )

        total_tachos_recolectados = len(tachos_visitados_sector)
        eficiencia = (total_tachos_recolectados / len(entorno.tachos)) * 100
        
        if eficiencia >= 100:
            break

        for camion in camiones:
            for j in range(len(camion.ruta) - 1):
                origen, destino = camion.ruta[j], camion.ruta[j + 1]
                if (origen, destino) not in feromonas:
                    feromonas[(origen, destino)] = 1.0
                feromonas[(origen, destino)] *= (1 - rho)
                if entorno.tipo_nodo(destino) == "tacho":
                    feromonas[(origen, destino)] += 1.0

    return camiones