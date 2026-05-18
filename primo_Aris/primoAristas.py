import os
import math
import heapq
import pygame
import numpy as np

EPS = 1e-5

# ========================================================
# 1. ESTRUCTURA DE DATOS NÚCLEO (DCEL)
# ========================================================
class Vertex:
    def __init__(self, vid, x, y):
        self.id = vid
        self.x = float(x)
        self.y = float(y)
        self.incident_edge = None

class HalfEdge:
    def __init__(self, eid):
        self.id = eid
        self.origin = None
        self.twin = None
        self.next = None
        self.prev = None
        self.face = None

class Face:
    def __init__(self, fid):
        self.id = fid
        self.outer_component = None
        self.inner_components = []
        self.area = 0.0
        self.active = False

class DCEL:
    def __init__(self):
        self.vertices = {}
        self.edges = {}
        self.faces = {}
        self.v_counter = 0
        self.e_counter = 0
        self.f_counter = 1 # C1 es la cara infinita

    def add_vertex(self, x, y):
        key = (round(x, 4), round(y, 4))
        if key in self.vertices: return self.vertices[key]
        v = Vertex(f"V{self.v_counter}", x, y)
        self.v_counter += 1
        self.vertices[key] = v
        return v

    def add_edge(self, v1, v2):
        e1 = HalfEdge(f"e{self.e_counter}")
        e2 = HalfEdge(f"e{self.e_counter+1}")
        self.e_counter += 2
        e1.origin = v1; e2.origin = v2
        e1.twin = e2; e2.twin = e1
        if v1.incident_edge is None: v1.incident_edge = e1
        if v2.incident_edge is None: v2.incident_edge = e2
        self.edges[e1.id] = e1; self.edges[e2.id] = e2
        return e1, e2

    def add_face(self, is_unbounded=False):
        f = Face(f"C{self.f_counter}")
        if is_unbounded: f.area = float('inf')
        self.faces[f.id] = f
        self.f_counter += 1
        return f

# ========================================================
# LECTURA DE ARCHIVOS
# ========================================================
def parse_layer_files(folder_path, prefix):
    dcel = DCEL(); dcel.f_counter = 1
    v_file = os.path.join(folder_path, f"{prefix}.vertices")
    v_map = {}
    with open(v_file, 'r') as f:
        for line in f:
            if line.startswith('#') or not line.strip() or "Nombre" in line or "Archivo" in line: continue
            parts = line.split()
            if len(parts) >= 4:
                vid, x, y, inc = parts[0], parts[1], parts[2], parts[3]
                v = Vertex(vid, float(x), float(y)); v_map[vid] = v; dcel.vertices[vid] = v

    e_file = os.path.join(folder_path, f"{prefix}.aristas")
    e_map = {}
    with open(e_file, 'r') as f:
        for line in f:
            if line.startswith('#') or not line.strip() or "Nombre" in line or "Archivo" in line: continue
            parts = line.split()
            if len(parts) >= 6:
                eid, orig, twin, face, nxt, prv = parts[0], parts[1], parts[2], parts[3], parts[4], parts[5]
                e = HalfEdge(eid); e_map[eid] = {'obj': e, 'orig': orig, 'twin': twin, 'face': face, 'next': nxt, 'prev': prv}
                dcel.edges[eid] = e

    for eid, data in e_map.items():
        e = data['obj']; e.origin = v_map[data['orig']]; e.twin = e_map[data['twin']]['obj']
        e.next = e_map[data['next']]['obj']; e.prev = e_map[data['prev']]['obj']
        if e.origin.incident_edge is None: e.origin.incident_edge = e

    c_file = os.path.join(folder_path, f"{prefix}.caras")
    with open(c_file, 'r') as f:
        for line in f:
            if line.startswith('#') or not line.strip() or "Nombre" in line or "Archivo" in line: continue
            parts = line.split()
            if len(parts) >= 3:
                fid, inner_str, outer_str = parts[0], parts[1], parts[2]
                f_obj = Face(fid)
                if inner_str != "None":
                    inner_ids = inner_str.replace('[','').replace(']','').split(',')
                    f_obj.inner_components = [e_map[eid]['obj'] for eid in inner_ids if eid in e_map]
                if outer_str != "None": f_obj.outer_component = e_map[outer_str]['obj']
                dcel.faces[fid] = f_obj
                if f_obj.outer_component:
                    curr = f_obj.outer_component
                    while True:
                        curr.face = f_obj; curr = curr.next
                        if curr == f_obj.outer_component: break
                for ic in f_obj.inner_components:
                    curr = ic
                    while True:
                        curr.face = f_obj; curr = curr.next
                        if curr == ic: break

    a_file = os.path.join(folder_path, f"{prefix}.activos")
    active_faces = set()
    if os.path.exists(a_file):
        with open(a_file, 'r') as f:
            for line in f:
                if line.startswith('#') or not line.strip() or "Caras" in line or "Archivo" in line: continue
                active_faces.add(line.strip())
    for fid in active_faces:
        if fid in dcel.faces: dcel.faces[fid].active = True

    for f_obj in dcel.faces.values():
        if f_obj.outer_component:
            poly = get_face_polygon(f_obj); area = 0.0; n = len(poly)
            for i in range(n):
                x1, y1 = poly[i]; x2, y2 = poly[(i+1)%n]
                area += (x1 * y2 - x2 * y1)
            f_obj.area = abs(area / 2.0)
    return dcel

# ========================================================
# ALGORITMO DE FUSIÓN (MAP OVERLAY)
# ========================================================
def extract_segments(dcel):
    segments = []; visited_edges = set()
    for e in dcel.edges.values():
        if e.id not in visited_edges:
            p1 = (e.origin.x, e.origin.y); p2 = (e.twin.origin.x, e.twin.origin.y)
            segments.append((p1, p2))
            visited_edges.add(e.id); visited_edges.add(e.twin.id)
    return segments

def cross(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

def intersect(seg1, seg2):
    p1, p2 = seg1; p3, p4 = seg2
    d1, d2 = cross(p3, p4, p1), cross(p3, p4, p2)
    d3, d4 = cross(p1, p2, p3), cross(p1, p2, p4)
    if ((d1 > 0 and d2 < 0) or (d1 < 0 and d2 > 0)) and ((d3 > 0 and d4 < 0) or (d3 < 0 and d4 > 0)):
        t = d1 / (d1 - d2)
        return (p1[0] + t*(p2[0]-p1[0]), p1[1] + t*(p2[1]-p1[1]))
    return None

def find_intersections(segments):
    # Optimización: Buscamos todas las intersecciones pareando todos los segmentos.
    # Esto es robusto y previene los errores de superposición del Sweep-Line clásico.
    points = set()
    for s in segments: points.add(s[0]); points.add(s[1])
    for i in range(len(segments)):
        for j in range(i+1, len(segments)):
            p = intersect(segments[i], segments[j])
            if p: points.add((round(p[0], 4), round(p[1], 4)))
    return list(points)

def build_overlay_dcel(segments):
    # 1. Eliminar segmentos duplicados que causan la fusión errónea de caras
    unique_segments = []
    seen = set()
    for s in segments:
        p1, p2 = s
        key = tuple(sorted([(round(p1[0],4), round(p1[1],4)), (round(p2[0],4), round(p2[1],4))]))
        if key not in seen:
            seen.add(key); unique_segments.append(s)
    
    # 2. Encontrar intersecciones y dividir segmentos
    inters = find_intersections(unique_segments)
    dcel = DCEL()
    seg_points = {i: [s[0], s[1]] for i, s in enumerate(unique_segments)}
    
    for ix, iy in inters:
        for i, seg in enumerate(unique_segments):
            p, q = seg
            d1 = math.hypot(ix-p[0], iy-p[1]); d2 = math.hypot(ix-q[0], iy-q[1])
            d3 = math.hypot(p[0]-q[0], p[1]-q[1])
            if d1 + d2 < d3 + EPS: seg_points[i].append((ix, iy))

    for i in seg_points:
        pts = seg_points[i]
        if len(pts) > 2:
            p0 = unique_segments[i][0]
            pts.sort(key=lambda p: math.hypot(p[0]-p0[0], p[1]-p0[1]))

    # 3. Construir DCEL
    edge_map = {}
    for i, pts in seg_points.items():
        for j in range(len(pts)-1):
            v1 = dcel.add_vertex(pts[j][0], pts[j][1]); v2 = dcel.add_vertex(pts[j+1][0], pts[j+1][1])
            e1, e2 = dcel.add_edge(v1, v2)
            edge_map[(v1.id, v2.id)] = e1; edge_map[(v2.id, v1.id)] = e2

    adj = {v.id: [] for v in dcel.vertices.values()}
    for e in dcel.edges.values(): adj[e.origin.id].append(e)

    # Regla de la mano izquierda (CCW)
    for v_id, edges in adj.items():
        edges.sort(key=lambda e: math.atan2(e.twin.origin.y - e.origin.y, e.twin.origin.x - e.origin.x))
        for i in range(len(edges)):
            e_curr = edges[i]; e_prev = edges[(i-1) % len(edges)].twin
            e_curr.prev = e_prev; e_prev.next = e_curr

    visited = set(); unbounded = dcel.add_face(is_unbounded=True)
    for e in dcel.edges.values():
        if e in visited: continue
        cycle_edges = []; curr = e
        while curr not in visited:
            visited.add(curr); cycle_edges.append(curr); curr = curr.next
        area = 0.0
        for ce in cycle_edges: area += (ce.origin.x * ce.twin.origin.y - ce.twin.origin.x * ce.origin.y)
        area /= 2.0
        if area < 0:
            f = dcel.add_face(); f.outer_component = cycle_edges[0]; f.area = abs(area)
            for ce in cycle_edges: ce.face = f
        else:
            for ce in cycle_edges: ce.face = unbounded
            if area > EPS: unbounded.inner_components.append(cycle_edges[0])
    for e in dcel.edges.values():
        if e.face is None: e.face = unbounded
    return dcel

# ========================================================
# PERSISTENCIA Y UTILIDADES
# ========================================================
def get_face_polygon(face):
    if not face.outer_component: return []
    poly = []; start = face.outer_component; curr = start
    while True:
        poly.append((curr.origin.x, curr.origin.y)); curr = curr.next
        if curr == start: break
    return poly

def point_in_polygon(pt, poly):
    if not poly: return False
    x, y = pt; n = len(poly); inside = False; p1x, p1y = poly[0]
    for i in range(n + 1):
        p2x, p2y = poly[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y: xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters: inside = not inside
        p1x, p1y = p2x, p2y
    return inside

def inherit_attributes(new_dcel, original_dcels):
    for f in new_dcel.faces.values():
        if f.id == "C1" or not f.outer_component: continue
        poly = get_face_polygon(f)
        cx = sum(p[0] for p in poly) / len(poly); cy = sum(p[1] for p in poly) / len(poly)
        for orig_dcel in original_dcels:
            for orig_f in orig_dcel.faces.values():
                if orig_f.active and orig_f.outer_component:
                    if point_in_polygon((cx, cy), get_face_polygon(orig_f)):
                        f.active = True; break

def save_dcel(dcel, prefix="overlay_result"):
    with open(f"{prefix}.activos", "w") as f:
        f.write("# Caras Activas\n")
        for fc in dcel.faces.values():
            if fc.active: f.write(f"{fc.id}\n")

# ========================================================
# 3. VISUALIZACIÓN E INTERACTIVIDAD (PYGAME)
# ========================================================
def pygame_interactive(dcel, img_folder="imagenes"):
    pygame.init()
    WIDTH, HEIGHT = 900, 700
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Map Overlay - Primo Primos (Pygame)")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 14)

    # Calcular límites para transformar coordenadas cartesianas a pantalla
    all_x = [v.x for v in dcel.vertices.values()]
    all_y = [v.y for v in dcel.vertices.values()]
    min_x, max_x = min(all_x) - 2, max(all_x) + 2
    min_y, max_y = min(all_y) - 2, max(all_y) + 2
    scale_x = WIDTH / (max_x - min_x)
    scale_y = HEIGHT / (max_y - min_y)
    scale = min(scale_x, scale_y) * 0.9
    offset_x = (WIDTH - (max_x - min_x) * scale) / 2
    offset_y = (HEIGHT - (max_y - min_y) * scale) / 2

    def cart_to_screen(cx, cy):
        sx = offset_x + (cx - min_x) * scale
        sy = HEIGHT - (offset_y + (cy - min_y) * scale) # Invertir Y
        return int(sx), int(sy)

    # Cargar imágenes
    images = []
    if os.path.exists(img_folder):
        for fname in sorted(os.listdir(img_folder)):
            if fname.lower().endswith(('.png', '.jpg')):
                img = pygame.image.load(os.path.join(img_folder, fname)).convert_alpha()
                images.append(img)

    running = True
    while running:
        screen.fill((240, 240, 240)) # Fondo gris claro

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                # Convertir pantalla a cartesiano
                cx = (mx - offset_x) / scale + min_x
                cy = (HEIGHT - my - offset_y) / scale + min_y
                
                best_face = None; min_area = float('inf')
                for fc in dcel.faces.values():
                    if fc.id == "C1": continue
                    poly = get_face_polygon(fc)
                    if point_in_polygon((cx, cy), poly):
                        if fc.area < min_area:
                            min_area = fc.area; best_face = fc
                
                if best_face:
                    best_face.active = not best_face.active
                    save_dcel(dcel)

        # Dibujar Caras Activas con Imagen (Clipping)
        for fc in dcel.faces.values():
            if fc.active and fc.outer_component:
                poly_cart = get_face_polygon(fc)
                poly_scr = [cart_to_screen(p[0], p[1]) for p in poly_cart]
                
                # Crear máscara de recorte
                mask_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                pygame.draw.polygon(mask_surface, (255, 255, 255, 255), poly_scr)
                
                # Cargar y escalar imagen
                if images:
                    img = images[int(fc.id[1:]) % len(images)]
                    bx = [p[0] for p in poly_scr]; by = [p[1] for p in poly_scr]
                    min_bx, max_bx = min(bx), max(bx); min_by, max_by = min(by), max(by)
                    w = max_bx - min_bx; h = max_by - min_by
                    if w > 0 and h > 0:
                        scaled_img = pygame.transform.scale(img, (w, h))
                        img_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                        img_surface.blit(scaled_img, (min_bx, min_by))
                        
                        # Aplicar máscara
                        img_surface.blit(mask_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
                        screen.blit(img_surface, (0, 0))
                else:
                    # Si no hay imágenes, rellenar de verde
                    pygame.draw.polygon(screen, (144, 238, 144, 150), poly_scr)

        # Dibujar Aristas
        for e in dcel.edges.values():
            if int(e.id[1:]) < int(e.twin.id[1:]):
                p1 = cart_to_screen(e.origin.x, e.origin.y)
                p2 = cart_to_screen(e.twin.origin.x, e.twin.origin.y)
                pygame.draw.line(screen, (0, 0, 0), p1, p2, 2)

        # Dibujar Vértices y Etiquetas
        for v in dcel.vertices.values():
            pos = cart_to_screen(v.x, v.y)
            pygame.draw.circle(screen, (200, 0, 0), pos, 4)
            label = font.render(v.id, True, (0, 0, 150))
            screen.blit(label, (pos[0] + 5, pos[1] - 10))

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()

# ========================================================
# EJECUCIÓN PRINCIPAL
# ========================================================
if __name__ == "__main__":
    folder = input("Introduce el nombre de la carpeta donde están los layers: ")
    if not os.path.exists(folder):
        print("La carpeta no existe."); exit()

    layers_prefixes = set()
    for fname in os.listdir(folder):
        if fname.endswith(".vertices"): layers_prefixes.add(fname.replace(".vertices", ""))

    if len(layers_prefixes) < 1:
        print("No se encontraron archivos .vertices en la carpeta."); exit()

    print(f"Capas encontradas: {layers_prefixes}")
    original_dcles = []; all_segments = []
    for prefix in layers_prefixes:
        print(f"Cargando capa: {prefix}...")
        dcel_orig = parse_layer_files(folder, prefix)
        original_dcles.append(dcel_orig)
        all_segments.extend(extract_segments(dcel_orig))

    print(f"Total de segmentos a fusionar: {len(all_segments)}")
    print("Ejecutando Map Overlay...")
    overlay_dcel = build_overlay_dcel(all_segments)
    inherit_attributes(overlay_dcel, original_dcles)
    save_dcel(overlay_dcel)
    print("¡Fusión completada! Archivos generados. Abriendo Pygame...")

    if not os.path.exists("imagenes"): os.makedirs("imagenes")
    pygame_interactive(overlay_dcel)