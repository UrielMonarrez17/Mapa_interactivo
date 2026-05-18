import math

class OverlaySolver:
    def __init__(self, tolerance=1e-8):
        self.TOL = tolerance
        self.vertices = {} # (x, y) -> Name
        self.vertex_objects = {} # Name -> (x, y)

    def get_key(self, x, y):
        return (round(x / self.TOL) * self.TOL, round(y / self.TOL) * self.TOL)

    def add_vertex(self, x, y, name=None):
        key = self.get_key(x, y)
        if key in self.vertices:
            return self.vertices[key]
        v_name = name if name else f"X{len(self.vertex_objects)}"
        self.vertices[key] = v_name
        self.vertex_objects[v_name] = key
        return v_name

    def find_intersection(self, p1, p2, p3, p4):
        # Algoritmo de intersección de segmentos estándar
        x1, y1 = p1; x2, y2 = p2
        x3, y3 = p3; x4, y4 = p4
        denom = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)
        if abs(denom) < 1e-12: return None
        ua = ((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)) / denom
        ub = ((x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)) / denom
        if 0 <= ua <= 1 and 0 <= ub <= 1:
            return x1 + ua * (x2 - x1), y1 + ua * (y2 - y1)
        return None

    def solve(self, edges):
        """
        PASO 1: Identificación de TODAS las intersecciones posibles.
        Se genera un pozo global de vértices.
        """
        raw_segments = []
        for e in edges:
            v1 = self.add_vertex(e['p1'][0], e['p1'][1], e['v1_name'])
            v2 = self.add_vertex(e['p2'][0], e['p2'][1], e['v2_name'])
            raw_segments.append({'v1': v1, 'v2': v2, 'layer': e['layer'], 'orig_name': e['name']})

        # Intersecciones arista vs arista
        for i in range(len(raw_segments)):
            for j in range(i + 1, len(raw_segments)):
                s1, s2 = raw_segments[i], raw_segments[j]
                p1, p2 = self.vertex_objects[s1['v1']], self.vertex_objects[s1['v2']]
                p3, p4 = self.vertex_objects[s2['v1']], self.vertex_objects[s2['v2']]
                inter = self.find_intersection(p1, p2, p3, p4)
                if inter:
                    self.add_vertex(inter[0], inter[1])

        """
        PASO 2: Subdivisión exhaustiva.
        Cada arista se rompe en cada vértice del pozo global que caiga sobre ella.
        """
        subdivided_edges = []
        all_v_names = list(self.vertex_objects.keys())
        
        for seg in raw_segments:
            p1 = self.vertex_objects[seg['v1']]
            p2 = self.vertex_objects[seg['v2']]
            dx, dy = p2[0] - p1[0], p2[1] - p1[1]
            mag_sq = dx*dx + dy*dy
            if mag_sq < 1e-12: continue

            # Encontrar vértices que viven sobre este segmento
            points_on_seg = []
            for v_name in all_v_names:
                pv = self.vertex_objects[v_name]
                # Proyección escalar u
                u = ((pv[0] - p1[0]) * dx + (pv[1] - p1[1]) * dy) / mag_sq
                if -1e-9 <= u <= 1.0 + 1e-9:
                    # Distancia perpendicular
                    dist_sq = (p1[0] + u*dx - pv[0])**2 + (p1[1] + u*dy - pv[1])**2
                    if dist_sq < 1e-12:
                        points_on_seg.append((u, v_name))
            
            points_on_seg.sort()
            for k in range(len(points_on_seg) - 1):
                u1, v_start = points_on_seg[k]
                u2, v_end = points_on_seg[k+1]
                if abs(u1 - u2) > 1e-8:
                    subdivided_edges.append({
                        'v1': v_start, 'v2': v_end, 
                        'layer': seg['layer'], 'orig_name': seg['orig_name']
                    })

        """
        PASO 3: Construcción de Arreglos Circulares (Ordenamiento Angular).
        Se generan las semi-aristas y se vinculan mediante punteros 'next'.
        """
        half_edges = {}
        adj = {}
        for i, se in enumerate(subdivided_edges):
            # Crear par de semi-aristas (Forward y Backward)
            f_name = f"{se['layer']}_{se['orig_name']}_f{i}"
            b_name = f"{se['layer']}_{se['orig_name']}_b{i}"
            
            half_edges[f_name] = {'origin': se['v1'], 'twin': b_name, 'name': f_name}
            half_edges[b_name] = {'origin': se['v2'], 'twin': f_name, 'name': b_name}
            
            adj.setdefault(se['v1'], []).append(f_name)
            adj.setdefault(se['v2'], []).append(b_name)

        for v_name, outgoing in adj.items():
            p_orig = self.vertex_objects[v_name]
            def get_angle(he_name):
                target_v = half_edges[half_edges[he_name]['twin']]['origin']
                p_target = self.vertex_objects[target_v]
                return math.atan2(p_target[1] - p_orig[1], p_target[0] - p_orig[0])
            
            outgoing.sort(key=get_angle)
            # Vincular circularmente: el gemelo de una entra al vértice y sale por la siguiente
            n = len(outgoing)
            for idx in range(n):
                curr_he = outgoing[idx]
                prev_he_twin = half_edges[outgoing[(idx - 1) % n]]['twin']
                half_edges[prev_he_twin]['next'] = curr_he

        """
        PASO 4: Recorrido de Ciclos (Caras).
        """
        visited = set()
        faces = []
        for he_name in sorted(half_edges.keys()):
            if he_name not in visited:
                cycle = []
                curr = he_name
                while curr not in visited:
                    visited.add(curr)
                    cycle.append(curr)
                    curr = half_edges[curr]['next']
                if cycle: faces.append(cycle)
        
        return self.vertex_objects, half_edges, faces

if __name__ == "__main__":
    # Ejemplo de uso rápido
    solver = OverlaySolver()
    edges_input = [
        {'p1': (0, 0), 'p2': (10, 10), 'layer': 'L1', 'name': 's1', 'v1_name': 'A', 'v2_name': 'B'},
        {'p1': (0, 10), 'p2': (10, 0), 'layer': 'L2', 'name': 's2', 'v1_name': 'C', 'v2_name': 'D'}
    ]
    v_objs, hes, faces = solver.solve(edges_input)
    print(f"Vértices encontrados: {len(v_objs)}")
    print(f"Caras detectadas: {len(faces)}")
    for i, face in enumerate(faces):
        print(f"Cara {i}: {face}")