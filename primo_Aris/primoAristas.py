import os
import math
import heapq
import pygame
import matplotlib.pyplot as plt

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
        self.physical_id = None  # ID único visual y de archivo (Ej. e1)
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
        self.f_counter = 1 

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

    return dcel

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

# ========================================================
# GUARDADO DE ARCHIVOS DCEL RESULTANTE
# ========================================================
def save_dcel_full(dcel, prefix="overlay_result"):
    with open(f"{prefix}.vertices", "w") as f:
        f.write("#################################\n")
        f.write(f"{'Nombre':<8}{'x':<8}{'y':<8}{'Incidente'}\n")
        f.write("#################################\n")
        for v in dcel.vertices.values():
            inc = v.incident_edge.id if v.incident_edge else "None"
            f.write(f"{v.id:<8}{v.x:<8g}{v.y:<8g}{inc}\n")
            
    with open(f"{prefix}.aristas", "w") as f:
        f.write("#############################################\n")
        f.write(f"{'Nombre':<8}{'Origen':<8}{'Pareja':<8}{'Cara':<8}{'Sigue':<8}{'Antes'}\n")
        f.write("#############################################\n")
        
        # AQUÍ ESTÁ LA CORRECCIÓN: 
        # Se listan TODAS las medias-aristas (Half-Edges) como lo dicta el algoritmo Primo-Primo.
        # Cada arista apunta a su Pareja (Twin) real, y muestra la Cara que delimita.
        for e in dcel.edges.values():
            twin_id = e.twin.id if e.twin else "None"
            face_id = e.face.id if e.face else "None"
            nxt_id = e.next.id if e.next else "None"
            prv_id = e.prev.id if e.prev else "None"
            
            f.write(f"{e.id:<8}{e.origin.id:<8}{twin_id:<8}{face_id:<8}{nxt_id:<8}{prv_id}\n")
            
    with open(f"{prefix}.caras", "w") as f:
        f.write("#######################\n")
        f.write(f"{'Nombre':<8}{'Interno':<15}{'Externo'}\n")
        f.write("#######################\n")
        for fc in dcel.faces.values():
            outer = fc.outer_component.id if fc.outer_component else "None"
            inner = "[" + ",".join([ic.id for ic in fc.inner_components]) + "]" if fc.inner_components else "None"
            f.write(f"{fc.id:<8}{inner:<15}{outer}\n")
            
    with open(f"{prefix}.activos", "w") as f:
        f.write("#######################\n")
        f.write("Caras Activas\n")
        f.write("#######################\n")
        for fc in dcel.faces.values():
            if fc.active: 
                f.write(f"{fc.id}\n")

# ========================================================
# UI Y UTILIDADES DE DIBUJO
# ========================================================
def draw_skip_button(screen, font):
    btn_rect = pygame.Rect(screen.get_width() - 160, 10, 150, 30)
    pygame.draw.rect(screen, (200, 50, 50), btn_rect, border_radius=5)
    text = font.render("Saltar Animacion", True, (255, 255, 255))
    screen.blit(text, (btn_rect.x + 10, btn_rect.y + 5))
    return btn_rect

def setup_pygame_view(segments, width=800, height=600):
    all_x = [p[0] for s in segments for p in s]
    all_y = [p[1] for s in segments for p in s]
    min_x, max_x = min(all_x) - 2, max(all_x) + 2
    min_y, max_y = min(all_y) - 2, max(all_y) + 2
    scale = min(width / (max_x - min_x), height / (max_y - min_y)) * 0.9
    off_x = (width - (max_x - min_x) * scale) / 2
    off_y = (height - (max_y - min_y) * scale) / 2
    return min_x, max_x, min_y, max_y, scale, off_x, off_y

def cart_to_screen(cx, cy, min_x, min_y, scale, off_x, off_y, height):
    return int(off_x + (cx - min_x) * scale), int(height - (off_y + (cy - min_y) * scale))

# ========================================================
# VISTA TÉCNICA MATPLOTLIB (ARISTA DIFUMINADA Y CICLOS SIN ID)
# ========================================================
def open_matplotlib_technical_view(dcel):
    fig, ax = plt.subplots(figsize=(8, 6))
    fig.canvas.manager.set_window_title('Map Overlay - Vista Técnica de Ciclos')
    
    drawn_physical_edges = set()
    
    for e in dcel.edges.values():
        p1 = (e.origin.x, e.origin.y)
        p2 = (e.twin.origin.x, e.twin.origin.y)
        
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        length = math.hypot(dx, dy)
        
        # 1. Dibujar la ARISTA FÍSICA difuminada (una sola vez por línea)
        if e.physical_id not in drawn_physical_edges:
            ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color='gray', linewidth=5, alpha=0.3, zorder=1)
            
            # Etiqueta ÚNICA de la arista en el centro de la línea
            mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
            ax.text(mx, my, e.physical_id, color='black', fontsize=9, fontweight='bold',
                    ha='center', va='center', bbox=dict(facecolor='white', alpha=0.6, edgecolor='none', pad=1), zorder=4)
            
            drawn_physical_edges.add(e.physical_id)

        # 2. Dibujar las FLECHAS direccionales del ciclo SIN ID
        if length > 0:
            nx = -dy / length
            ny = dx / length
            offset = 0.08  # Separación para las flechas
            
            p1_off = (p1[0] + nx * offset, p1[1] + ny * offset)
            p2_off = (p2[0] + nx * offset, p2[1] + ny * offset)
            
            shrink = 0.15 
            p1_draw = (p1_off[0] + dx * shrink, p1_off[1] + dy * shrink)
            p2_draw = (p2_off[0] - dx * shrink, p2_off[1] - dy * shrink)
        else:
            p1_draw, p2_draw = p1, p2

        # Flecha indicadora (sin colocar texto)
        ax.annotate("", xy=p2_draw, xytext=p1_draw,
                    arrowprops=dict(arrowstyle="-|>", color='royalblue', lw=1.2), zorder=2)

    # Dibujar Vértices
    for v in dcel.vertices.values():
        ax.plot(v.x, v.y, marker='o', markersize=5, color='crimson', zorder=3)
        ax.annotate(f" {v.id}", (v.x, v.y), color='darkred', fontsize=8, fontweight='bold', zorder=4)

    # Dibujar Caras
    for fc in dcel.faces.values():
        if fc.id != "C1" and fc.outer_component:
            poly = get_cycle_polygon(fc.outer_component)
            if poly:
                cx = sum(p[0] for p in poly) / len(poly)
                cy = sum(p[1] for p in poly) / len(poly)
                ax.text(cx, cy, fc.id, color='forestgreen', fontsize=10, fontweight='bold', ha='center', va='center')

    ax.set_aspect('equal', adjustable='datalim')
    plt.title("Vista Técnica: Aristas difuminadas (1 ID) y Ciclos separados", fontsize=11, pad=12, fontweight='bold')
    plt.xlabel("Eje X")
    plt.ylabel("Eje Y")
    plt.grid(True, linestyle='--', alpha=0.5)
    
    plt.savefig("vista_tecnica_dcel.png", dpi=300, bbox_inches='tight')
    plt.show()  

# ========================================================
# ANIMACIONES Y SWEEP-LINE
# ========================================================
def animated_sweep_line(segments, screen, params):
    min_x, max_x, min_y, max_y, scale, off_x, off_y = params
    height = screen.get_height()
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 18)
    
    found_intersections = set()
    for i in range(len(segments)):
        for j in range(i+1, len(segments)):
            pt = intersect(segments[i], segments[j])
            if pt: found_intersections.add((round(pt[0], 4), round(pt[1], 4)))
    
    events = []
    for i, s in enumerate(segments):
        p1, p2 = s
        if p1[0] > p2[0]: p1, p2 = p2, p1
        heapq.heappush(events, (p1[0], p1[1], 'start', i, p1))
        heapq.heappush(events, (p2[0], p2[1], 'end', i, p2))
        
    for ix, iy in found_intersections:
        heapq.heappush(events, (ix, iy, 'intersect', -1, (ix, iy)))
        
    intersections = []
    active_segments = set()
    current_x = min_x
    running = True; skip_anim = False

    while events and running:
        x, y, e_type, idx, pt = heapq.heappop(events)
        current_x = x
        
        if e_type == 'start': active_segments.add(idx)
        elif e_type == 'end':
            if idx in active_segments: active_segments.remove(idx)
        elif e_type == 'intersect':
            if pt not in intersections: intersections.append(pt)

        if skip_anim: continue

        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                running = False; pygame.quit(); exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if btn_rect.collidepoint(event.pos): skip_anim = True

        screen.fill((30, 30, 30))
        for s in segments:
            p1 = cart_to_screen(s[0][0], s[0][1], min_x, min_y, scale, off_x, off_y, height)
            p2 = cart_to_screen(s[1][0], s[1][1], min_x, min_y, scale, off_x, off_y, height)
            pygame.draw.line(screen, (100, 100, 100), p1, p2, 1)
            
        for a_idx in active_segments:
            s = segments[a_idx]
            p1 = cart_to_screen(s[0][0], s[0][1], min_x, min_y, scale, off_x, off_y, height)
            p2 = cart_to_screen(s[1][0], s[1][1], min_x, min_y, scale, off_x, off_y, height)
            pygame.draw.line(screen, (0, 255, 0), p1, p2, 2)
            
        for ix, iy in intersections:
            ip = cart_to_screen(ix, iy, min_x, min_y, scale, off_x, off_y, height)
            pygame.draw.circle(screen, (255, 0, 0), ip, 4)

        sl_x = cart_to_screen(current_x, 0, min_x, min_y, scale, off_x, off_y, height)[0]
        pygame.draw.line(screen, (255, 255, 0), (sl_x, 0), (sl_x, height), 2)
        
        screen.blit(font.render(f"Fase 1: Sweep-Line Intersecciones ({len(intersections)})", True, (255, 255, 255)), (10, 10))
        btn_rect = draw_skip_button(screen, font)
        
        pygame.display.flip()
        clock.tick(60)
        
    if not skip_anim: pygame.time.delay(500)
    return list(found_intersections)

def build_and_animate_dcel(segments, inters, screen, params):
    min_x, max_x, min_y, max_y, scale, off_x, off_y = params
    height = screen.get_height()
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 18)
    
    unique_segments = []
    seen = set()
    for s in segments:
        p1, p2 = s
        key = tuple(sorted([(round(p1[0],4), round(p1[1],4)), (round(p2[0],4), round(p2[1],4))]))
        if key not in seen:
            seen.add(key); unique_segments.append(s)
            
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

    dcel = DCEL()
    edge_seen = set()
    
    for i, pts in seg_points.items():
        for j in range(len(pts)-1):
            v1 = dcel.add_vertex(pts[j][0], pts[j][1])
            v2 = dcel.add_vertex(pts[j+1][0], pts[j+1][1])
            if v1.id != v2.id:
                k1 = (v1.id, v2.id); k2 = (v2.id, v1.id)
                if k1 not in edge_seen and k2 not in edge_seen:
                    dcel.add_edge(v1, v2)
                    edge_seen.add(k1); edge_seen.add(k2)

    adj = {v.id: [] for v in dcel.vertices.values()}
    for e in dcel.edges.values(): adj[e.origin.id].append(e)

    for v_id, edges in adj.items():
        edges.sort(key=lambda e: math.atan2(e.twin.origin.y - e.origin.y, e.twin.origin.x - e.origin.x))
        for i in range(len(edges)):
            e_curr = edges[i]; e_prev = edges[(i-1) % len(edges)].twin
            e_curr.prev = e_prev; e_prev.next = e_curr

    visited = set()
    unbounded = dcel.add_face(is_unbounded=True)
    holes = []
    skip_anim = False
    
    for e in dcel.edges.values():
        if e in visited: continue
        cycle_edges = []; curr = e
        while curr not in visited:
            visited.add(curr); cycle_edges.append(curr); curr = curr.next
            
            if skip_anim: continue
            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if btn_rect.collidepoint(event.pos): skip_anim = True
            
            screen.fill((30, 30, 30))
            for de in dcel.edges.values():
                p1 = cart_to_screen(de.origin.x, de.origin.y, min_x, min_y, scale, off_x, off_y, height)
                p2 = cart_to_screen(de.twin.origin.x, de.twin.origin.y, min_x, min_y, scale, off_x, off_y, height)
                color = (0, 255, 255) if de in cycle_edges else (100, 100, 100)
                width = 3 if de in cycle_edges else 1
                pygame.draw.line(screen, color, p1, p2, width)
            
            screen.blit(font.render("Fase 2: Extrayendo Caras y Agujeros", True, (255, 255, 255)), (10, 10))
            btn_rect = draw_skip_button(screen, font)
            pygame.display.flip()
            clock.tick(30)
            
        area = 0.0
        for ce in cycle_edges: area += (ce.origin.x * ce.twin.origin.y - ce.twin.origin.x * ce.origin.y)
        area /= 2.0
        
        if area < -EPS:
            f = dcel.add_face(); f.outer_component = cycle_edges[0]; f.area = abs(area)
            for ce in cycle_edges: ce.face = f
        elif area > EPS:
            holes.append((cycle_edges, area))
            
    for hole_edges, hole_area in holes:
        he = hole_edges[0]
        v1 = he.origin; v2 = he.twin.origin
        dx = v2.x - v1.x; dy = v2.y - v1.y
        length = math.hypot(dx, dy)
        if length > 0:
            nx = -dy / length * 0.001
            ny = dx / length * 0.001
            test_pt = ((v1.x + v2.x)/2 + nx, (v1.y + v2.y)/2 + ny)
        else:
            test_pt = (v1.x, v1.y)

        containing_face = unbounded
        min_area = float('inf')
        for f in dcel.faces.values():
            if f.id != unbounded.id and f.outer_component:
                if f.area > abs(hole_area) + EPS:
                    if point_in_polygon(test_pt, get_cycle_polygon(f.outer_component)):
                        if f.area < min_area:
                            min_area = f.area; containing_face = f
                        
        for ce in hole_edges: ce.face = containing_face
        containing_face.inner_components.append(hole_edges[0])
            
    # REASIGNAR IDs FÍSICOS CONSECUTIVOS SIN SALTOS (e1, e2, e3...)
    c = 1
    assigned = set()
    for e in dcel.edges.values():
        if e.id not in assigned:
            pid = f"e{c}"
            e.physical_id = pid
            e.twin.physical_id = pid
            assigned.add(e.id)
            assigned.add(e.twin.id)
            c += 1

    if not skip_anim: pygame.time.delay(500)
    return dcel

def get_cycle_polygon(edge):
    if not edge: return []
    poly = []; start = edge; curr = start
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

# ========================================================
# 3. VISUALIZACIÓN INTERACTIVA PYGAME
# ========================================================
def pygame_interactive(dcel, initial_params, img_folder="imagenes"):
    min_x, max_x, min_y, max_y, scale, offset_x, offset_y = initial_params
    WIDTH, HEIGHT = 800, 600
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Map Overlay - Vista Interactiva")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 18)
    bg_color = (245, 245, 245)

    fallback_colors = [(144, 238, 144, 180), (173, 216, 230, 180), (255, 182, 193, 180), 
                       (255, 250, 205, 180), (221, 160, 221, 180), (240, 128, 128, 180)]

    images = []
    if os.path.exists(img_folder):
        for fname in sorted(os.listdir(img_folder)):
            if fname.lower().endswith(('.png', '.jpg', '.jpeg')):
                img = pygame.image.load(os.path.join(img_folder, fname)).convert_alpha()
                images.append(img)

    def cart_to_screen_local(cx, cy):
        sx = offset_x + (cx - min_x) * scale
        sy = HEIGHT - (offset_y + (cy - min_y) * scale)
        return int(sx), int(sy)

    running = True
    while running:
        screen.fill(bg_color) 

        btn_view_rect = pygame.Rect(WIDTH - 260, HEIGHT - 45, 250, 35)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: 
                    if btn_view_rect.collidepoint(event.pos):
                        open_matplotlib_technical_view(dcel)
                        continue

                    mx, my = event.pos
                    cx = (mx - offset_x) / scale + min_x
                    cy = (HEIGHT - my - offset_y) / scale + min_y
                    
                    best_face = None; min_area = float('inf')
                    for fc in dcel.faces.values():
                        if fc.id == "C1": continue
                        poly = get_cycle_polygon(fc.outer_component)
                        
                        if point_in_polygon((cx, cy), poly):
                            en_agujero = False
                            for ic in fc.inner_components:
                                if point_in_polygon((cx, cy), get_cycle_polygon(ic)):
                                    en_agujero = True
                                    break
                                    
                            if not en_agujero and fc.area < min_area:
                                min_area = fc.area; best_face = fc
                                
                    if best_face:
                        best_face.active = not best_face.active
                        save_dcel_full(dcel)
                        
            elif event.type == pygame.MOUSEWHEEL:
                mx, my = pygame.mouse.get_pos()
                zoom_factor = 1.1 if event.y > 0 else 0.9
                cx = (mx - offset_x) / scale + min_x
                cy = (HEIGHT - my - offset_y) / scale + min_y
                scale *= zoom_factor
                offset_x = mx - (cx - min_x) * scale
                offset_y = HEIGHT - my - (cy - min_y) * scale

        caras_ordenadas = sorted([f for f in dcel.faces.values() if f.id != "C1"], key=lambda x: x.area, reverse=True)

        for fc in caras_ordenadas:
            if fc.active and fc.outer_component:
                poly_cart = get_cycle_polygon(fc.outer_component)
                poly_scr = [cart_to_screen_local(p[0], p[1]) for p in poly_cart]
                
                if len(poly_scr) > 2:
                    if images:
                        img = images[int(fc.id[1:]) % len(images)]
                        mask_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                        pygame.draw.polygon(mask_surface, (255, 255, 255, 255), poly_scr)
                        
                        for ic in fc.inner_components:
                            h_scr = [cart_to_screen_local(p[0], p[1]) for p in get_cycle_polygon(ic)]
                            if len(h_scr) > 2:
                                hole_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                                pygame.draw.polygon(hole_surf, (255, 255, 255, 255), h_scr)
                                mask_surface.blit(hole_surf, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
                        
                        bx = [p[0] for p in poly_scr]; by = [p[1] for p in poly_scr]
                        min_bx, max_bx = min(bx), max(bx); min_by, max_by = min(by), max(by)
                        w = max_bx - min_bx; h = max_by - min_by
                        
                        if w > 0 and h > 0:
                            scaled_img = pygame.transform.scale(img, (w, h))
                            img_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                            img_surface.blit(scaled_img, (min_bx, min_by))
                            img_surface.blit(mask_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
                            screen.blit(img_surface, (0, 0))
                    else:
                        color = fallback_colors[int(fc.id[1:]) % len(fallback_colors)]
                        color_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                        pygame.draw.polygon(color_surface, color, poly_scr)
                        
                        for ic in fc.inner_components:
                            h_scr = [cart_to_screen_local(p[0], p[1]) for p in get_cycle_polygon(ic)]
                            if len(h_scr) > 2:
                                hole_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                                pygame.draw.polygon(hole_surf, (255, 255, 255, 255), h_scr)
                                color_surface.blit(hole_surf, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
                                
                        screen.blit(color_surface, (0, 0))

                    pygame.draw.polygon(screen, (0, 100, 0), poly_scr, 2)
                    for ic in fc.inner_components:
                        h_scr = [cart_to_screen_local(p[0], p[1]) for p in get_cycle_polygon(ic)]
                        if len(h_scr) > 2: pygame.draw.polygon(screen, (0, 100, 0), h_scr, 2)

        drawn_edges = set()
        for e in dcel.edges.values():
            if e.physical_id not in drawn_edges:
                p1 = cart_to_screen_local(e.origin.x, e.origin.y)
                p2 = cart_to_screen_local(e.twin.origin.x, e.twin.origin.y)
                pygame.draw.line(screen, (40, 40, 40), p1, p2, 2)
                drawn_edges.add(e.physical_id)
                
        screen.blit(font.render("Fase 3: Mapa Interactivo (Zoom: Rueda | Click: Seleccionar)", True, (0, 0, 0)), (10, 10))

        pygame.draw.rect(screen, (33, 150, 243), btn_view_rect, border_radius=6)
        pygame.draw.rect(screen, (13, 71, 161), btn_view_rect, width=2, border_radius=6)
        btn_text = font.render("Abrir Vista Tecnica (Matplotlib)", True, (255, 255, 255))
        screen.blit(btn_text, (btn_view_rect.x + 12, btn_view_rect.y + 6))

        pygame.display.flip()
        clock.tick(30)
    pygame.quit()

if __name__ == "__main__":
    folder = input("Introduce el nombre de la carpeta donde están los layers: ")
    if not os.path.exists(folder):
        print("La carpeta no existe."); exit()

    layers_prefixes = set()
    for fname in os.listdir(folder):
        if fname.endswith(".vertices"): layers_prefixes.add(fname.replace(".vertices", ""))

    if len(layers_prefixes) < 1:
        print("No se encontraron archivos .vertices en la carpeta."); exit()

    all_segments = []
    for prefix in layers_prefixes:
        dcel_orig = parse_layer_files(folder, prefix)
        all_segments.extend(extract_segments(dcel_orig))

    all_x = [p[0] for s in all_segments for p in s]
    all_y = [p[1] for s in all_segments for p in s]
    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)
    dx = max_x - min_x; dy = max_y - min_y
    margin = max(dx, dy) * 0.2 if max(dx, dy) > 0 else 10
    bx1, bx2 = min_x - margin, max_x + margin
    by1, by2 = min_y - margin, max_y + margin

    bb_segments = [
        ((bx1, by1), (bx2, by1)),
        ((bx2, by1), (bx2, by2)),
        ((bx2, by2), (bx1, by2)),
        ((bx1, by2), (bx1, by1))
    ]
    all_segments.extend(bb_segments)

    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Map Overlay Animations")
    params = setup_pygame_view(all_segments, width=800, height=600)

    inters = animated_sweep_line(all_segments, screen, params)
    overlay_dcel = build_and_animate_dcel(all_segments, inters, screen, params)
    
    save_dcel_full(overlay_dcel, prefix="overlay_result")
    pygame_interactive(overlay_dcel, params)