"""
PRIMO PRIMOS 
fusion de listas de aristas
1 interseccion
2 aristas que interactuan
3 eliminarlas
4 por cada arista agregar dos aristas, cada uno se va a partir a la mitad
*los primos inician en el vertice original
*los primo primos empiezan en X
5 acomodar todos en un ordenamiento circular (sacar los vectores y acomodarlos respecto al circulo, una secuencia en forma de circulo)
6  la pareja del primo seria el primo primo de su pareja anterior
7 el siguiente de los primo primos no cambia , se queda igual
(los primo primos siguientes no cambian)
8 el siguiente de los primos es el siguiente en el circulo en el ordenamiento del reloj 
9 el siguiente se pone en el siguiente de los primo primos 
*tambien funciona si intersecan mas de dos
10 en el anterior es justo lo contrario de los siguientes
11 los primos conservan los anteriores del original antes de la interseccion 
12 como los partimos y ya no existen, hay que ponerle su anterior pero en primo primo 
13 el anterior es el que se encuentra mas cerca en sentido ANTI horario 
14 ya con hacer esos cambios la lista ligada esta actualizada
15 implementar el algoritmo de las caras para rearmarlas e insertarlas al archivo de resultado
"""
import os
import matplotlib.pyplot as plt
import re
import matplotlib.cm as cm 
import numpy as np
import math
import random

class Vertice:
    def __init__(self, nombre, x, y):
        self.nombre = nombre
        self.x = float(x)
        self.y = float(y)
        self.incidente = None

    def __repr__(self):
        return f"V({self.nombre}: {self.x}, {self.y})"

class Arista:
    def __init__(self, nombre, origen_id, pareja_id, cara_id, sigue_id, antes_id, layer_id=None):
        self.nombre = nombre
        self.origen_id = origen_id
        self.pareja_id = pareja_id
        self.cara_id = cara_id
        self.sigue_id = sigue_id
        self.antes_id = antes_id
        self.layer_id = layer_id
        self.origen = None
        self.pareja = None
        self.sigue = None
        self.cycle_type = None # Atributo para clasificar si es parte de un ciclo externo o interno

class Cara:
    def __init__(self, nombre, interno_raw, externo_id, activa=True):
        self.nombre = nombre
        self.interno_ids = interno_raw.strip("[]").split(",") if interno_raw != "None" else []
        self.externo_id = externo_id
        self.activa = activa

class Figura:
    def __init__(self, id_layer):
        self.id_layer = id_layer
        self.vertices = {}
        self.aristas = {}
        self.caras = {}

    def vincular_objetos(self):
        for a in self.aristas.values():
            if a.origen_id in self.vertices:
                a.origen = self.vertices[a.origen_id]
            if a.pareja_id in self.aristas:
                a.pareja = self.aristas[a.pareja_id]
            if a.sigue_id in self.aristas:
                a.sigue = self.aristas[a.sigue_id]

    def dibujar_en_eje(self, ax, mapa_colores):
        ya_etiquetado = False 
        
        for a in self.aristas.values():
            # Verificar si la cara de la arista esta activa
            cara_obj = self.caras.get(a.cara_id)
            if cara_obj and cara_obj.activa and a.origen and a.sigue and a.sigue.origen:
                p1 = a.origen
                p2 = a.sigue.origen
                
                etiqueta = self.id_layer if not ya_etiquetado else ""
                color_asignado = mapa_colores.get((self.id_layer, a.cara_id), "gray")
                
                ax.plot([p1.x, p2.x], [p1.y, p2.y], 
                        marker='o', 
                        color=color_asignado, 
                        label=etiqueta,
                        linewidth=2)
                
                ax.annotate('', xy=((p1.x + p2.x)/2, (p1.y + p2.y)/2), 
                            xytext=(p1.x, p1.y),
                            arrowprops=dict(arrowstyle='-', color=color_asignado, alpha=0.5))
                
                ya_etiquetado = True

        for v in self.vertices.values():
            # Dibujamos los nombres de los vertices en un color neutro o el de la capa
            ax.text(v.x, v.y, f' {v.nombre}', fontsize=9, color="black", alpha=0.7)

def cargar_datos(carpeta):
    figuras = {}

    archivos = [f for f in os.listdir(carpeta) if os.path.isfile(os.path.join(carpeta, f))]
    
    layers = set(re.match(r"^(layer\d+)", f).group(1) for f in archivos if f.startswith("layer"))

    for ly in sorted(layers):
        fig = Figura(ly)
        
        path_v = os.path.join(carpeta, f"{ly}.vertices")
        if os.path.exists(path_v):
            with open(path_v, 'r') as f:
                for line in f:
                    if line.startswith('#') or 'Nombre' in line or 'Archivo' in line: continue
                    parts = line.split()
                    
                    fig.vertices[parts[0]] = Vertice(parts[0], parts[1], parts[2])

        path_a = os.path.join(carpeta, f"{ly}.aristas")
        if os.path.exists(path_a):
            with open(path_a, 'r') as f:
                for line in f:
                    if line.startswith('#') or 'Nombre' in line or 'Archivo' in line : continue
                    p = line.split()
                    fig.aristas[p[0]] = Arista(p[0], p[1], p[2], p[3], p[4], p[5], layer_id=ly)

        path_c = os.path.join(carpeta, f"{ly}.caras")
        if os.path.exists(path_c):
            with open(path_c, 'r') as f:
                for line in f:
                    if line.startswith('#') or 'Nombre' in line or 'Archivo' in line : continue
                    p = line.split()
                    fig.caras[p[0]] = Cara(p[0], p[1], p[2])

        #  Logica de Caras Activas 
        path_act = os.path.join(carpeta, f"{ly}.activos")
        if os.path.exists(path_act):
            # Si existe el archivo, desactivamos todas primero
            for c in fig.caras.values():
                c.activa = False
            
            with open(path_act, 'r') as f_act:
                for line in f_act:
                    cid = line.strip()
                    if cid and not cid.startswith('#') and 'Archivo' not in cid:
                        if cid in fig.caras:
                            fig.caras[cid].activa = True
        else:
            # Si no existe, todas son activas (valor por defecto)
            for c in fig.caras.values():
                c.activa = True

        fig.vincular_objetos()
        figuras[ly] = fig

    return figuras

def find_intersection(p1, p2, p3, p4):
    """Calcula el punto de interseccion entre el segmento p1p2 y p3p4."""
    x1, y1 = p1.x, p1.y
    x2, y2 = p2.x, p2.y
    x3, y3 = p3.x, p3.y
    x4, y4 = p4.x, p4.y
    
    denom = (y4-y3)*(x2-x1) - (x4-x3)*(y2-y1)
    if abs(denom) < 1e-10: return None, None, None
    
    ua = ((x4-x3)*(y1-y3) - (y4-y3)*(x1-x3)) / denom
    ub = ((x2-x1)*(y1-y3) - (y2-y1)*(x1-x3)) / denom
    
    # Se consideran intersecciones estrictamente internas
    if 1e-6 < ua < 1.0 - 1e-6 and 1e-6 < ub < 1.0 - 1e-6:
        return ua, ub, (x1 + ua*(x2-x1), y1 + ua*(y2-y1))
    return None, None, None

def reconstruir_caras_dcel(vertices_dict, aristas_dict, original_activity=None):
    if original_activity is None: original_activity = {}
    for a in aristas_dict.values():
        if a.origen_id in vertices_dict:
            a.origen = vertices_dict[a.origen_id]
        if a.pareja_id in aristas_dict:
            a.pareja = aristas_dict[a.pareja_id]
        if a.sigue_id in aristas_dict:
            a.sigue = aristas_dict[a.sigue_id]

    # 1. Extracción de sitios mediante un recorrido de aristas con ciclos (sigue_id)
    visitadas = set()
    ciclos = []
    for aid in sorted(aristas_dict.keys()):
        if aid not in visitadas:
            ciclo_actual = []
            curr = aid
            while curr not in visitadas:
                if curr not in aristas_dict: break
                visitadas.add(curr)
                ciclo_actual.append(aristas_dict[curr])
                curr = aristas_dict[curr].sigue_id
            if ciclo_actual: ciclos.append(ciclo_actual)

    # 2. Clasificar si son ciclos externos o internos (Area signada o giro)
    # Area > 0 -> CCW (Externo/Cara), Area < 0 -> CW (Interno/Hueco)
    caras_potenciales = [] # Ciclos CCW
    huecos = []            # Ciclos CW

    for c in ciclos:
        area = 0.0
        for i in range(len(c)):
            p1 = c[i].origen
            p2 = c[i].sigue.origen
            area += (p1.x * p2.y) - (p2.x * p1.y)
        
        # Nodo más izquierdo para el paso 3
        p_izq = min((a.origen for a in c), key=lambda v: (v.x, v.y))
        info = {
            'aristas': c,
            'area': area / 2.0,
            'p_min': p_izq,
            'ref_id': c[0].nombre
        }
        if info['area'] > 0: caras_potenciales.append(info)
        else: huecos.append(info)

    # 3. Nombramiento y Grafo de caras (C1, C2, C3...)
    face_counter = 1
    inf_face_name = f"C{face_counter}"
    face_counter += 1
    used_names = {inf_face_name}

    # Asignar nombres finales y determinar actividad
    for cp in caras_potenciales:
        # Identificar orígenes (capa, cara) originales involucrados
        orig_sources = {(a.layer_id, a.cara_id) for a in cp['aristas'] if a.cara_id and a.cara_id != "None"}
        unique_face_ids = {s[1] for s in orig_sources}
        
        # Lógica de Naming: Preservar si el ID de cara es único entre sus componentes, de lo contrario Cx
        if len(unique_face_ids) == 1:
            cand_name = list(unique_face_ids)[0]
            if cand_name not in used_names:
                cp['final_name'] = cand_name
            else:
                cp['final_name'] = f"{cand_name}_{face_counter}"
                face_counter += 1
        else:
            cp['final_name'] = f"C{face_counter}"
            face_counter += 1
        used_names.add(cp['final_name'])

        # Lógica de Actividad: Solo activa si TODAS las contribuciones originales eran activas.
        # Se usa la tupla (layer_id, cara_id) para consultar el estado real de la capa original.
        cp['activa'] = True
        for src in orig_sources:
            if not original_activity.get(src, True):
                cp['activa'] = False
                break

    for h in huecos:
        p_h = h['p_min']
        parent = inf_face_name
        max_x_left = float('-inf')

        for cp in caras_potenciales:
            # Point-in-polygon
            inside = False
            for a in cp['aristas']:
                v1, v2 = a.origen, a.sigue.origen
                if ((v1.y > p_h.y) != (v2.y > p_h.y)) and \
                   (p_h.x < (v2.x - v1.x) * (p_h.y - v1.y) / (v2.y - v1.y) + v1.x):
                    inside = not inside
            
            if inside:
                # Barrido a la izquierda para encontrar la arista más cercana (paso 3)
                for a in cp['aristas']:
                    v1, v2 = a.origen, a.sigue.origen
                    if (v1.y <= p_h.y < v2.y) or (v2.y <= p_h.y < v1.y):
                        ix = v1.x + (v2.x - v1.x) * (p_h.y - v1.y) / (v2.y - v1.y)
                        if ix < p_h.x and ix > max_x_left:
                            max_x_left = ix
                            parent = cp['final_name']
        h['parent'] = parent

    # 4. Reregistro de caras y generación de listas de ligas internas
    caras_finales = {}
    
    # Registrar cara Infinita
    inf_holes = [h['ref_id'] for h in huecos if h['parent'] == inf_face_name]
    caras_finales[inf_face_name] = Cara(inf_face_name, f"[{','.join(inf_holes)}]" if inf_holes else "None", "None", activa=True)

    for cp in caras_potenciales:
        c_name = cp['final_name']
        c_holes = [h['ref_id'] for h in huecos if h['parent'] == c_name]
        caras_finales[c_name] = Cara(c_name, f"[{','.join(c_holes)}]" if c_holes else "None", cp['ref_id'], activa=cp['activa'])
        # 5. Actualizar cada arista con su cara y tipo de ciclo
        for a in cp['aristas']:
            aristas_dict[a.nombre].cara_id = c_name
            aristas_dict[a.nombre].cycle_type = 'external' # Tipo para límites externos

    for h in huecos:
        for a in h['aristas']:
            aristas_dict[a.nombre].cara_id = h['parent']
            aristas_dict[a.nombre].cycle_type = 'internal' # Tipo para límites internos (huecos)

    return caras_finales

def guardar_caras_fusion(caras, filename):
    """Genera el archivo .caras con el formato solicitado."""
    header = f"{'Nombre':<20} {'Interno':<30} {'Externo':<15}"
    with open(filename, 'w') as f:
        f.write("# Archivo de caras generado por reconstruccion DCEL\n")
        f.write(header + "\n")
        f.write("-" * 65 + "\n")
        for cid in sorted(caras.keys()):
            c = caras[cid]
            # Formatear lista de internos
            internos = f"[{','.join(c.interno_ids)}]" if c.interno_ids and c.interno_ids != ['None'] else "None"
            line = f"{c.nombre:<20} {internos:<30} {c.externo_id:<15}"
            f.write(line + "\n")
    print(f"Archivo de caras guardado en: {filename}")

def ejecutar_primo_primos(figuras):
    """Algoritmo de fusion de listas de aristas (Primo Primos)."""
    all_he = []
    for fig in figuras.values():
        for a in fig.aristas.values():
            # Evitar procesar gemelas dos veces para deteccion de interseccion
            if a.nombre < a.pareja_id:
                if a.origen and a.sigue and a.sigue.origen:
                    all_he.append(a)

    # Deteccion de intersecciones y aristas que interactuan
    nodes_on_edge = {}
    inter_count = 1
    new_vertices = {}
    for i in range(len(all_he)):
        for j in range(i+1, len(all_he)):
            e1, e2 = all_he[i], all_he[j]
            ua, ub, coords = find_intersection(e1.origen, e1.sigue.origen, e2.origen, e2.sigue.origen)
            if coords:
                v_name = f"X{inter_count}"
                v = Vertice(v_name, coords[0], coords[1])
                new_vertices[v_name] = v
                inter_count += 1
                nodes_on_edge.setdefault(e1.nombre, []).append((ua, v))
                nodes_on_edge.setdefault(e1.pareja_id, []).append((1.0 - ua, v))
                nodes_on_edge.setdefault(e2.nombre, []).append((ub, v))
                nodes_on_edge.setdefault(e2.pareja_id, []).append((1.0 - ub, v))

    #  Division de aristas en primos (origen) y primo-primos (X)
    final_aristas = {}
    final_vertices = {}
    for fig in figuras.values():
        final_vertices.update(fig.vertices)
    final_vertices.update(new_vertices)

    processed_orig = set()
    for fig in figuras.values():
        for a_orig in fig.aristas.values():
            if a_orig.nombre in processed_orig: continue
            a_twin_orig = a_orig.pareja
            if not a_twin_orig: continue
            processed_orig.add(a_orig.nombre)
            processed_orig.add(a_twin_orig.nombre)
            
            pts = [(0.0, a_orig.origen)]
            if a_orig.nombre in nodes_on_edge:
                pts.extend(nodes_on_edge[a_orig.nombre])
            pts.append((1.0, a_orig.sigue.origen))
            pts.sort(key=lambda x: x[0])
            
            for i in range(len(pts)-1):
                u_v, v_v = pts[i][1], pts[i+1][1]
                # Nombramiento: s_p (primo), s_pp (primo-primo)
                n_fw = f"{a_orig.nombre}_p" if i == 0 else f"{a_orig.nombre}_pp{i}"
                rev_idx = len(pts) - i - 2
                n_bw = f"{a_twin_orig.nombre}_p" if rev_idx == 0 else f"{a_twin_orig.nombre}_pp{rev_idx}"
                
                he_fw = Arista(n_fw, u_v.nombre, n_bw, a_orig.cara_id, "None", "None", layer_id=a_orig.layer_id)
                he_fw.origen = u_v
                he_bw = Arista(n_bw, v_v.nombre, n_fw, a_twin_orig.cara_id, "None", "None", layer_id=a_twin_orig.layer_id)
                he_bw.origen = v_v
                final_aristas[n_fw] = he_fw
                final_aristas[n_bw] = he_bw

    # Ordenamiento circular en X y actualizacion de la lista ligada
    adj = {}
    for he in final_aristas.values():
        adj.setdefault(he.origen_id, []).append(he)
    
    for v_id, outgoing in adj.items():
        v_orig = final_vertices[v_id]
        def get_angle_he(he):
            twin = final_aristas[he.pareja_id]
            dest = final_vertices[twin.origen_id]
            return math.atan2(dest.y - v_orig.y, dest.x - v_orig.x)
        
        # Ordenamiento circular (sentido del reloj)
        outgoing.sort(key=get_angle_he, reverse=True)
        n = len(outgoing)
        for i in range(n):
            o_curr = outgoing[i]
            # El siguiente del primo (entrante) es el siguiente en el ordenamiento del reloj (saliente)
            t_prev = final_aristas[outgoing[(i-1)%n].pareja_id]
            t_prev.sigue_id = o_curr.nombre
            o_curr.antes_id = t_prev.nombre

    # Rearmar caras e insertar a la estructura final
    for he in final_aristas.values():
        if he.pareja_id in final_aristas: he.pareja = final_aristas[he.pareja_id]
        if he.sigue_id in final_aristas: he.sigue = final_aristas[he.sigue_id]
    
    # Recopilar mapa de actividad original
    original_activity = {}
    for fig in figuras.values():
        for c in fig.caras.values():
            original_activity[(fig.id_layer, c.nombre)] = c.activa

    caras_fusion = reconstruir_caras_dcel(final_vertices, final_aristas, original_activity)
    return final_vertices, final_aristas, caras_fusion

def guardar_resultado_fusion(aristas, filename):
    """Guarda la tabla final de aristas fusionadas en formato .aristas con alineacion y la imprime."""
    header_text = "# Archivo de aristas generado por el algoritmo Primo Primos"
    col_names = f"{'Nombre':<15} {'Origen':<10} {'Pareja':<15} {'Cara':<10} {'Sigue':<15} {'Antes':<15}"
    
    print(f"\n Tabla de Fusion de Aristas ({filename}) ")
    print(header_text)
    print("-" * 85)
    print(col_names)
    print("-" * 85)

    with open(filename, 'w') as f:
        f.write(header_text + "\n")
        f.write(col_names + "\n")
        for a_id in sorted(aristas.keys()):
            a = aristas[a_id]
            line = f"{a.nombre:<15} {a.origen_id:<10} {a.pareja_id:<15} {a.cara_id:<10} {a.sigue_id:<15} {a.antes_id:<15}"
            f.write(line + "\n")
            print(line)
    print(f"\nAlgoritmo finalizado. Tabla de fusion guardada en: {filename}")

def guardar_vertices_fusion(vertices, aristas, filename):
    """Genera el archivo .vertices para los puntos originales y las nuevas intersecciones."""
    # Determinar una arista incidente para cada vertice (la primera que lo tenga como origen)
    incidente_map = {}
    for a in aristas.values():
        if a.origen_id not in incidente_map:
            incidente_map[a.origen_id] = a.nombre

    header_text = "Archivo de vertices generado por la fusion"
    sep = "#" * 55
    col_names = f"{'Nombre':<12} {'x':<12} {'y':<12} {'Incidente':<15}"

    with open(filename, 'w') as f:
        f.write(header_text + "\n")
        f.write(sep + "\n")
        f.write(col_names + "\n")
        f.write(sep + "\n")
        for v_id in sorted(vertices.keys()):
            v = vertices[v_id]
            inc = incidente_map.get(v_id, "None")
            f.write(f"{v.nombre:<12} {v.x:<12.4f} {v.y:<12.4f} {inc:<15}\n")
    print(f"Archivo de vertices guardado en: {filename}")

def dibujar_ciclos_dcel(ax, vertices, aristas, caras):
    """Dibuja el resultado de la fusión con flechas desplazadas (offset) para no encimarse."""
    # Generar colores aleatorios para las caras
    face_colors = {c_id: [random.random() for _ in range(3)] for c_id, obj in caras.items() if obj.activa}
    
    # Dibujar el relleno de las caras primero (alpha para transparencia)
    for c_id, cara_obj in caras.items():
        if cara_obj.activa and cara_obj.externo_id and cara_obj.externo_id != "None":
            start_edge = aristas.get(cara_obj.externo_id)
            if start_edge:
                poly_pts = []
                curr = start_edge
                for _ in range(len(aristas)): # Límite de seguridad
                    poly_pts.append((curr.origen.x, curr.origen.y))
                    curr = curr.sigue
                    if curr == start_edge or curr is None: break
                if len(poly_pts) > 2:
                    xs, ys = zip(*poly_pts)
                    ax.fill(xs, ys, color=face_colors[c_id], alpha=0.3, label=f"Relleno {c_id}")
    
    # Calcular la extensión total de los datos para un offset adaptable (2.5% de la pantalla)
    all_x = [v.x for v in vertices.values()]
    all_y = [v.y for v in vertices.values()]
    if all_x and all_y:
        max_span = max(max(all_x) - min(all_x), max(all_y) - min(all_y))
        global_offset = max_span * 0.01  # Offset incrementado para separar flechas opuestas
    else:
        global_offset = 0.1

    for a in aristas.values():
        if not (a.origen and a.sigue and a.sigue.origen): continue
        
        p1, p2 = a.origen, a.sigue.origen
        dx, dy = p2.x - p1.x, p2.y - p1.y
        dist = math.sqrt(dx**2 + dy**2)
        if dist == 0: continue

        # Vector unitario y normal (izquierda)
        ux, uy = dx/dist, dy/dist
        nx, ny = -uy, ux  # Normal hacia la izquierda del vector (p1->p2)

        # Ajuste fino de offset
        current_offset = min(global_offset, dist * 0.4)

        # Determinar si la cara de la arista está activa para el color
        cara_obj = caras.get(a.cara_id)
        is_active = cara_obj.activa if cara_obj else True
        alpha_val = 1.0 if is_active else 0.3

        # Determinar color y lado del offset
        if a.cycle_type == 'external' and is_active:
            color = "blue"
            ox, oy = nx * current_offset, ny * current_offset # Izquierda (Interior cara)
        elif a.cycle_type == 'internal' and is_active:
            color = "red"
            ox, oy = -nx * current_offset, -ny * current_offset # Derecha (Interior hueco)
        else:
            color = "gray"
            ox, oy = 0, 0

        # Puntos con desplazamiento
        p1_off = (p1.x + ox, p1.y + oy)
        p2_off = (p2.x + ox, p2.y + oy)

        # Dibujar la línea base (el segmento real)
        ax.plot([p1.x, p2.x], [p1.y, p2.y], color='gray', linestyle='--', alpha=0.3, linewidth=1)

        # Dibujar la flecha del ciclo con offset
        ax.annotate("", xy=p2_off, xytext=p1_off,
                    arrowprops=dict(arrowstyle="->", color=color, mutation_scale=10, lw=1.3, alpha=alpha_val))
        
        # Texto de la arista con un ligero ajuste para centrarlo respecto a la flecha
        ax.text(p1_off[0] + (p2_off[0]-p1_off[0])/2 + ox*0.3, 
                p1_off[1] + (p2_off[1]-p1_off[1])/2 + oy*0.3, 
                a.nombre, fontsize=7, color=color, alpha=alpha_val,
                fontweight='bold', ha='center', va='center')

    for v in vertices.values():
        ax.plot(v.x, v.y, 'ko', markersize=3)
        ax.text(v.x+0.1, v.y+0.1, v.nombre, fontsize=8, fontweight='bold')

ruta_carpeta = "./ejemplo_03"
figuras = cargar_datos(ruta_carpeta)

if figuras:
    # Ejecutar fusion de listas de aristas y obtener vertices, aristas y caras
    v_fusion, a_fusion, c_fusion = ejecutar_primo_primos(figuras)
    
    # Guardar resultados de la fusion en archivos
    # La función `reconstruir_caras_dcel` ahora se llama dentro de `ejecutar_primo_primos`
    # y opera sobre las aristas y vértices resultantes de la fusión.
    # Los archivos de salida reflejarán esta reconstrucción.
    
    guardar_resultado_fusion(a_fusion, "fusion_aristas.aristas")
    guardar_vertices_fusion(v_fusion, a_fusion, "fusion_vertices.vertices")
    guardar_caras_fusion(c_fusion, "fusion_caras.caras")

    fig_plot, ax = plt.subplots(figsize=(10, 8))
    # Graficar el resultado de la fusion resaltando los ciclos
    dibujar_ciclos_dcel(ax, v_fusion, a_fusion, c_fusion)
    ax.set_title("Visualización de Ciclos y Caras Fusionadas (Primo Primos)")
    ax.set_aspect('equal')

    # Añadir una leyenda para los colores de los ciclos
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], color='blue', lw=2, label='Ciclo Externo '),
        Line2D([0], [0], color='red', lw=2, label='Ciclo Interno ')
    ]
    ax.legend(handles=legend_elements, loc='upper right')

    ax.grid(True, linestyle='--', alpha=0.6)
    plt.show()
else:
    print("No se encontraron archivos layerXX en la carpeta especificada.")