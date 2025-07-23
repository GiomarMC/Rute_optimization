class Camion:
    def __init__(self, inicio, km_max=5000, kg_max=5000):
        self.pos = inicio
        self.km_restantes = km_max
        self.kg_basura = 0
        self.ruta = [inicio]
        self.kg_max = kg_max
        self.km_max = km_max
        self.tachos_visitados = set()

    def mover_a(self, destino, distancia, tipo_nodo):
        if self.km_restantes < distancia:
            raise ValueError(f"Movimiento imposible: requiere {distancia:.1f}m, disponible {self.km_restantes:.1f}m")
        
        self.pos = destino
        self.ruta.append(destino)
        self.km_restantes -= distancia
        
        if self.km_restantes < 0:
            raise ValueError(f"Combustible negativo detectado: {self.km_restantes:.1f}m")
        
        if tipo_nodo == 'tacho':
            if self.kg_basura + 300 > self.kg_max:
                raise ValueError(f"Capacidad excedida: {self.kg_basura + 300}kg > {self.kg_max}kg")
            
            self.kg_basura += 300
            self.tachos_visitados.add(destino)
        elif tipo_nodo == 'gasolinera':
            self.km_restantes = self.km_max
        elif tipo_nodo == 'vertedero':
            self.kg_basura = 0
        elif tipo_nodo == 'centro':
            pass
