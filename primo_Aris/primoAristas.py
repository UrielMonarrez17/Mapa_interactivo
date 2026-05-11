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

class Vertice:
    def __init__(self, nombre, x, y):
        self.nombre = nombre
        self.x = float(x)
        self.y = float(y)
        self.incidente = None

    def __repr__(self):
        return f"V({self.nombre}: {self.x}, {self.y})"

class Arista:
    def __init__(self, nombre, origen_id, pareja_id, cara_id, sigue_id, antes_id):
        self.nombre = nombre
        self.origen_id = origen_id
        self.pareja_id = pareja_id
        self.cara_id = cara_id
        self.sigue_id = sigue_id
        self.antes_id = antes_id
        self.origen = None
        self.pareja = None
        self.sigue = None

class Cara:
    def __init__(self, nombre, interno_raw, externo_id):
        self.nombre = nombre
        self.interno_ids = interno_raw.strip("[]").split(",") if interno_raw != "None" else []
        self.externo_id = externo_id
        self.activa = True

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
                    print("linea: ",line)
                    print("va a entrar: ",(line.startswith('#') or ('Nombre' in line or 'Archivo' in line)))
                    if line.startswith('#') or ('Nombre'in line or 'Archivo' in line): continue
                    parts = line.split()
                    
                    fig.vertices[parts[0]] = Vertice(parts[0], parts[1], parts[2])

        path_a = os.path.join(carpeta, f"{ly}.aristas")
        if os.path.exists(path_a):
            with open(path_a, 'r') as f:
                for line in f:
                    if line.startswith('#') or 'Nombre' in line or 'Archivo' in line : continue
                    p = line.split()
                    fig.aristas[p[0]] = Arista(p[0], p[1], p[2], p[3], p[4], p[5])

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

def reconstruir_caras_dcel(vertices_dict, aristas_dict):
    """
    Reconstruccion avanzada de caras siguiendo los pasos solicitados:
    1. Extraccion de ciclos.
    2. Clasificacion (Interno/Externo) via orientacion.
    3. Grafo de contencion.
    4. Registro de caras y huecos.
    5. Actualizacion de aristas.
    """
    # 1. Extraccion de sitios (ciclos)
    visitadas = set()
    ciclos = []
    for aid in sorted(aristas_dict.keys()):
        if aid not in visitadas:
            ciclo_actual = []
            curr = aid
            while curr not in visitadas:
                visitadas.add(curr)
                ciclo_actual.append(aristas_dict[curr])
                curr = aristas_dict[curr].sigue_id
            if ciclo_actual:
                ciclos.append(ciclo_actual)

    # 2. Clasificar ciclos (Area signada: >0 CCW = Cara, <0 CW = Hueco)
    caras_potenciales = [] # Ciclos CCW
    huecos = []            # Ciclos CW

    for c in ciclos:
        area = 0.0
        for i in range(len(c)):
            p1 = c[i].origen
            p2 = aristas_dict[c[i].sigue_id].origen
            area += (p1.x * p2.y) - (p2.x * p1.y)
        
        # Guardar info del ciclo: (aristas, area, punto_izquierdo)
        leftmost_idx = min(range(len(c)), key=lambda i: (c[i].origen.x, c[i].origen.y))
        info = {
            'aristas': c,
            'area': area / 2.0,
            'p_min': c[leftmost_idx].origen,
            'externo_id': c[0].nombre
        }
        
        if info['area'] > 0:
            caras_potenciales.append(info)
        else:
            huecos.append(info)

    # 3. Grafo de contencion (Asociar huecos a la cara que los contiene)
    # Cara infinita por defecto
    face_map = {"Cara_Infinita": {"externo": "None", "internos": []}}
    
    for h in huecos:
        contenedor = "Cara_Infinita"
        min_x_dist = float('inf')
        
        # Ray-casting simplificado: buscar la arista a la izquierda mas cercana
        for cp in caras_potenciales:
            # Verificar si el hueco esta dentro de la cara potencial
            # (Usando el punto mas a la izquierda del hueco)
            p = h['p_min']
            inside = False
            poly = cp['aristas']
            for i in range(len(poly)):
                v1 = poly[i].origen
                v2 = aristas_dict[poly[i].sigue_id].origen
                if ((v1.y > p.y) != (v2.y > p.y)) and \
                   (p.x < (v2.x - v1.x) * (p.y - v1.y) / (v2.y - v1.y + 1e-10) + v1.x):
                    inside = not inside
            
            if inside:
                # Si hay varias, podriamos jerarquizar, aqui tomamos la primera
                contenedor = cp['externo_id'] + "_face"
                break
        
        h['parent'] = contenedor

    # 4. Registro de objetos Cara
    caras_finales = {}
    
    # Registrar la cara infinita si tiene huecos
    inf_holes = [h['externo_id'] for h in huecos if h['parent'] == "Cara_Infinita"]
    caras_finales["Cara_Infinita"] = Cara("Cara_Infinita", f"[{','.join(inf_holes)}]" if inf_holes else "None", "None")

    for cp in caras_potenciales:
        c_name = cp['externo_id'] + "_face"
        c_holes = [h['externo_id'] for h in huecos if h['parent'] == c_name]
        caras_finales[c_name] = Cara(c_name, f"[{','.join(c_holes)}]" if c_holes else "None", cp['externo_id'])
        
        # 5. Actualizar aristas con su cara
        for a in cp['aristas']:
            aristas_dict[a.nombre].cara_id = c_name
            
    for h in huecos:
        for a in h['aristas']:
            aristas_dict[a.nombre].cara_id = h['parent']

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
                
                he_fw = Arista(n_fw, u_v.nombre, n_bw, "None", "None", "None")
                he_fw.origen = u_v
                he_bw = Arista(n_bw, v_v.nombre, n_fw, "None", "None", "None")
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
    
    caras_fusion = reconstruir_caras_dcel(final_vertices, final_aristas)
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

ruta_carpeta = "./ejemplo_01"
figuras = cargar_datos(ruta_carpeta)

if figuras:
    # Ejecutar fusion de listas de aristas y obtener vertices, aristas y caras
    v_fusion, a_fusion, c_fusion = ejecutar_primo_primos(figuras)
    
    # Guardar resultados de la fusion en archivos
    guardar_resultado_fusion(a_fusion, "fusion_aristas.aristas")
    guardar_vertices_fusion(v_fusion, a_fusion, "fusion_vertices.vertices")
    guardar_caras_fusion(c_fusion, "fusion_caras.caras")

    fig_plot, ax = plt.subplots(figsize=(10, 8))
    
    # Crear una lista de todas las caras activas para asignar colores unicos
    caras_totales = []
    for ly_id, fig_obj in figuras.items():
        for c_id, cara_obj in fig_obj.caras.items():
            if cara_obj.activa:
                caras_totales.append((ly_id, c_id))
    
    # Generar paleta de colores basada en el numero de caras
    n_colores = len(caras_totales) if len(caras_totales) > 0 else 1
    color_list = cm.tab20(np.linspace(0, 1, n_colores))
    mapa_colores_global = {key: color_list[i] for i, key in enumerate(caras_totales)}

    for nombre, figura_obj in figuras.items():
        figura_obj.dibujar_en_eje(ax, mapa_colores_global)

    ax.grid(True, linestyle='--', alpha=0.6)
    ax.legend() 
    plt.show()
else:
    print("No se encontraron archivos layerXX en la carpeta especificada.")