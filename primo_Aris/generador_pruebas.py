import os

def generate_layer(folder, prefix, shapes, active_faces):
    v_count = 0
    e_count = 0
    
    v_data = []
    e_data = []
    c_data = []
    
    # CARA1 siempre es la cara infinita/externa
    c1_inner = []
    
    for shape_idx, shape in enumerate(shapes):
        face_id = f"CARA{shape_idx + 2}"
        m = len(shape)
        start_v_idx = v_count
        start_e_idx = e_count
        
        # 1. Generar Vértices
        for i, (x, y) in enumerate(shape):
            vid = f"V{v_count}"
            # La arista incidente es la arista que sale de este vértice en sentido CCW
            inc_eid = f"e{start_e_idx + i*2}"
            v_data.append(f"{vid}\t{x:.2f}\t{y:.2f}\t{inc_eid}")
            v_count += 1
            
        # 2. Generar Aristas (Dobles enlazadas)
        for i in range(m):
            # Arista CCW (Borde de la cara CARA{k})
            e_ccw_id = f"e{start_e_idx + i*2}"
            v_orig_id = f"V{start_v_idx + i}"
            v_dest_id = f"V{start_v_idx + (i+1)%m}"
            twin_id = f"e{start_e_idx + i*2 + 1}"
            next_ccw_id = f"e{start_e_idx + ((i+1)%m)*2}"
            prev_ccw_id = f"e{start_e_idx + ((i-1)%m)*2}"
            
            e_data.append(f"{e_ccw_id}\t{v_orig_id}\t{twin_id}\t{face_id}\t{next_ccw_id}\t{prev_ccw_id}")
            
            # Arista CW (Borde de la cara infinita CARA1)
            e_cw_id = twin_id
            next_cw_id = f"e{start_e_idx + ((i-1)%m)*2 + 1}"
            prev_cw_id = f"e{start_e_idx + ((i+1)%m)*2 + 1}"
            
            e_data.append(f"{e_cw_id}\t{v_dest_id}\t{e_ccw_id}\tCARA1\t{next_cw_id}\t{prev_cw_id}")
            
        e_count += m * 2
        
        # 3. Datos de Caras
        c_data.append(f"{face_id}\tNone\t\te{start_e_idx}")
        # La primera arista CW de cada forma es un componente interno de CARA1
        c1_inner.append(f"e{start_e_idx + 1}") 
        
    # Insertar CARA1 al inicio
    c1_inners_str = "[" + ",".join(c1_inner) + "]"
    c_data.insert(0, f"CARA1\t{c1_inners_str}\tNone")
    
    # 4. Guardar Archivos con el formato exacto que espera tu parser
    with open(os.path.join(folder, f"{prefix}.vertices"), "w") as f:
        f.write("Archivo de vértices\n#################################\nNombre\tx\ty\tIncidente\n#################################\n")
        for line in v_data: f.write(line + "\n")
            
    with open(os.path.join(folder, f"{prefix}.aristas"), "w") as f:
        f.write("Archivo de aristas\n#############################################\nNombre\tOrigen\tPareja\tCara\tSigue\tAntes\n#############################################\n")
        for line in e_data: f.write(line + "\n")
        
    with open(os.path.join(folder, f"{prefix}.caras"), "w") as f:
        f.write("Archivo de caras\n#######################\nNombre\tInterno\t\tExterno\n#######################\n")
        for line in c_data: f.write(line + "\n")
        
    with open(os.path.join(folder, f"{prefix}.activos"), "w") as f:
        f.write("Archivo de activos\n#######################\nCaras Activas\n#######################\n")
        for face in active_faces: f.write(face + "\n")

if __name__ == "__main__":
    folder = "capas_prueba"
    if not os.path.exists(folder): os.makedirs(folder)

    # Layer 01 (Arena SMITE: Frontera, Centro, Base Superior, Base Inferior)
    # Coordenadas en sentido Antihorario (CCW) para áreas positivas
    s1 = [
        [(50, 95), (95, 50), (50, 5), (5, 50)],          # Frontera
        [(45, 60), (60, 60), (60, 40), (45, 40)],        # Centro
        [(40, 80), (60, 80), (60, 70), (40, 70)],        # Base Sup
        [(40, 30), (60, 30), (60, 20), (40, 20)]         # Base Inf
    ]
    generate_layer(folder, "layer01", s1, ["CARA2", "CARA3"])

    # Layer 02 (Gato Gigante: Ciudad, Edificio, Gato, Agua)
    s2 = [
        [(10, 90), (90, 90), (90, 10), (10, 10)],        # Ciudad
        [(15, 85), (40, 85), (40, 60), (15, 60)],        # Edificio
        [(45, 60), (60, 60), (60, 30), (45, 30)],        # Gato
        [(65, 20), (85, 20), (85, 10), (65, 10)]         # Agua
    ]
    generate_layer(folder, "layer02", s2, ["CARA3", "CARA4"])

    # Layer 03 (Personaje: Cielo, Luna, Cuerpo, Alas)
    s3 = [
        [(5, 95), (95, 95), (95, 5), (5, 5)],           # Cielo
        [(50, 90), (65, 75), (50, 60), (35, 75)],        # Luna (Diamante)
        [(45, 60), (55, 60), (55, 25), (45, 25)],        # Cuerpo
        [(10, 55), (45, 45), (25, 25)],                  # Ala Izq (Triángulo)
        [(90, 55), (55, 45), (75, 25)]                   # Ala Der (Triángulo)
    ]
    generate_layer(folder, "layer03", s3, ["CARA2", "CARA4", "CARA5"])

    # Layer 04 (Mapa México: 4 regiones separadas - NW, NE, SW, SE)
    s4 = [
        [(10, 95), (48, 95), (48, 52), (10, 52)],        # NW
        [(52, 95), (90, 95), (90, 52), (52, 52)],        # NE
        [(10, 48), (48, 48), (48, 10), (10, 10)],        # SW
        [(52, 48), (90, 48), (90, 10), (52, 10)]         # SE
    ]
    generate_layer(folder, "layer04", s4, ["CARA2", "CARA4"])

    print(f"¡Generación completada! Se crearon 16 archivos en la carpeta '{folder}'.")
    print("Ejecuta tu programa principal y usa 'capas_prueba' como nombre de carpeta.")