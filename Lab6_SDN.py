import yaml
import requests
import json
from collections import deque, defaultdict
# Clases
class Alumno:
    def __init__(self, nombre, codigo, mac):
        self.nombre = nombre 
        self.codigo = codigo
        self.mac = mac

class Curso:
    def __init__(self, codigo, nombre, estado, alumnos=None, servidores=None, servidores_info=None):
        self.codigo = codigo
        self.nombre = nombre
        self.estado = estado
        self.alumnos = alumnos or []
        self.servidores = servidores or []
        self.servidores_info = servidores_info or []

class Servidor:
    def __init__(self, nombre, ip, servicios=None):
        self.nombre = nombre
        self.ip = ip
        self.servicios = servicios or []

class Conexion:
    def __init__(self, handler, alumno, servidor, servicio, ruta):
        self.handler = handler  
        self.alumno = alumno
        self.servidor = servidor
        self.servicio = servicio
        self.ruta = ruta  


# Datos globales
alumnos = []
cursos = []
servidores = []
conexiones=[]
# Menu CLI:
def menu():
    while True:
        print("\n=== MENÚ PRINCIPAL ===")
        print("1) Importar")
        print("2) Exportar")
        print("3) Cursos")
        print("4) Alumnos")
        print("5) Servidores")
        print("6) Políticas")
        print("7) Conexiones")
        print("0) Salir")

        opcion = input("Seleccione una opción: ")

        if opcion == "1":
            importar_datos()
        elif opcion == "2":
            exportar_datos()
        elif opcion == "3":
            menu_cursos()
        elif opcion == "4":
            menu_alumnos()
        elif opcion == "5":
            menu_servidores()
        elif opcion == "6":
            print("Pendiente de implementación.")
        elif opcion == "7":
            menu_conexiones()
        elif opcion == "0":
            print("Saliendo...")
            break
        else:
            print("Opción inválida")

def importar_datos():
    global alumnos, cursos, servidores
    ruta = input("Ingrese el nombre del archivo YAML a importar (Enter para cancelar): ")
    if not ruta.strip():
        print("Importación cancelada.")
        return
    if not ruta.endswith(".yaml"):
        ruta += ".yaml"
    try:
        with open(ruta, 'r') as f:
            data = yaml.safe_load(f)

        print("Archivo cargado correctamente.")

        alumnos.clear()
        cursos.clear()
        servidores.clear()

        # ----- Alumnos -----
        codigo_a_alumno = {}
        for a in data.get('alumnos', []):
            alumno = Alumno(a['nombre'], a['codigo'], a['mac'])
            alumnos.append(alumno)
            codigo_a_alumno[a['codigo']] = alumno

        # ----- Servidores -----
        nombre_a_servidor = {}
        for s in data.get('servidores', []):
            servicios = []
            for svc in s.get('servicios', []):
                servicios.append({
                    'nombre': svc['nombre'],
                    'protocolo': svc['protocolo'],
                    'puerto': svc['puerto']
                })
            servidor = Servidor(s['nombre'], s['ip'], servicios)
            servidores.append(servidor)
            nombre_a_servidor[s['nombre']] = servidor

        # ----- Cursos -----
        for c in data.get('cursos', []):
            curso = Curso(c['codigo'], c['nombre'], c['estado'])

            # Cargar alumnos por código
            for cod in c.get('alumnos', []):
                alumno = codigo_a_alumno.get(cod)
                if alumno:
                    curso.alumnos.append(alumno)

            # Cargar servidores por nombre y registrar servicios permitidos
            servidores_info = []
            for s in c.get('servidores', []):
                nombre = s['nombre']
                if nombre in nombre_a_servidor:
                    curso.servidores.append(nombre_a_servidor[nombre])
                    servidores_info.append({
                        'nombre': nombre,
                        'servicios_permitidos': s.get('servicios_permitidos', [])
                    })
            curso.servidores_info = servidores_info

            cursos.append(curso)

    except Exception as e:
        print(f"Error al cargar el archivo: {e}")


def exportar_datos():
    ruta = input("Ingrese el nombre del archivo YAML para exportar (Enter para cancelar): ")
    if not ruta.strip():
        print("Exportación cancelada.")
        return
    if not ruta.endswith(".yaml"):
        ruta += ".yaml"
    try:
        data = {}

        # Alumnos
        data['alumnos'] = [
            {
                'nombre': a.nombre,
                'codigo': a.codigo,
                'mac': a.mac
            }
            for a in alumnos
        ]

        # Servidores
        data['servidores'] = []
        for s in servidores:
            servicios = [
                {
                    'nombre': svc['nombre'],
                    'protocolo': svc['protocolo'],
                    'puerto': svc['puerto']
                }
                for svc in s.servicios
            ]
            data['servidores'].append({
                'nombre': s.nombre,
                'ip': s.ip,
                'servicios': servicios
            })

        # Cursos
        data['cursos'] = []
        for c in cursos:
            curso_dict = {
                'codigo': c.codigo,
                'nombre': c.nombre,
                'estado': c.estado,
                'alumnos': [a.codigo for a in c.alumnos],
                'servidores': [
                    {
                        'nombre': s.nombre,
                        'servicios_permitidos': [svc['nombre'] for svc in s.servicios]
                    }
                    for s in c.servidores
                ]
            }
            data['cursos'].append(curso_dict)

        with open(ruta, 'w') as f:
            yaml.dump(data, f, sort_keys=False)

        print(f"Datos exportados exitosamente a '{ruta}'.")

    except Exception as e:
        print(f"Error al exportar los datos: {e}")

#Submenú de cursos:
def menu_cursos():
    while True:
        print("\n--- CURSOS ---")
        print("1) Listar cursos")
        print("2) Mostrar detalle de un curso")
        print("3) Actualizar (agregar/eliminar alumno)")
        print("4) Eliminar curso")
        print("0) Volver")
        opcion = input("Seleccione una opción: ")

        if opcion == "1":
            listar_cursos()
        elif opcion == "2":
            mostrar_curso()
        elif opcion == "3":
            actualizar_curso()
        elif opcion == "4":
            eliminar_curso()  
        elif opcion == "0":
            break
        else:
            print("Opción inválida")

def eliminar_curso():
    codigo = input("Ingrese el código del curso a eliminar: ")
    curso = next((c for c in cursos if c.codigo == codigo), None)
    if curso:
        cursos.remove(curso)
        print(f"Curso '{codigo}' eliminado correctamente.")
    else:
        print("Curso no encontrado.")


def listar_cursos():
    for curso in cursos:
        print(f"{curso.codigo} - {curso.nombre} ({curso.estado})")

def mostrar_curso():
    codigo = input("Ingrese el código del curso: ")
    curso = next((c for c in cursos if c.codigo == codigo), None)
    if curso:
        print(f"Nombre: {curso.nombre}\nEstado: {curso.estado}")
        print("Alumnos:")
        for alumno in curso.alumnos:
            print(f"  - {alumno.nombre} ({alumno.codigo})")
        print("Servidores:")
        for s in curso.servidores:
            print(f"  - {s.nombre} ({s.ip})")

    else:
        print("Curso no encontrado")

def actualizar_curso():
    codigo = input("Ingrese el código del curso que desea actualizar: ")
    curso = next((c for c in cursos if c.codigo == codigo), None)

    if not curso:
        print("Curso no encontrado.")
        return

    while True:
        print(f"\n--- Actualizando curso: {curso.nombre} ({curso.codigo}) ---")
        print("1) Agregar alumno")
        print("2) Eliminar alumno")
        print("0) Volver")
        opcion = input("Seleccione una opción: ")

        if opcion == "1":
            agregar_alumno_a_curso(curso)
        elif opcion == "2":
            eliminar_alumno_de_curso(curso)
        elif opcion == "0":
            break
        else:
            print("Opción inválida")

def agregar_alumno_a_curso(curso):
    print("\n--- Alumnos disponibles ---")
    disponibles = [a for a in alumnos if a not in curso.alumnos]
    if not disponibles:
        print("No hay alumnos disponibles para agregar.")
        return

    for a in disponibles:
        print(f"{a.codigo} - {a.nombre}")

    codigo_alumno = input("Ingrese el código del alumno a agregar: ")
    alumno = next((a for a in disponibles if str(a.codigo) == codigo_alumno), None)

    if alumno:
        curso.alumnos.append(alumno)
        print(f"Alumno {alumno.nombre} agregado al curso.")
    else:
        print("Código inválido o alumno ya inscrito.")

def eliminar_alumno_de_curso(curso):
    print("\n--- Alumnos en el curso ---")
    if not curso.alumnos:
        print("Este curso no tiene alumnos inscritos.")
        return

    for a in curso.alumnos:
        print(f"{a.codigo} - {a.nombre}")

    codigo_alumno = input("Ingrese el código del alumno a eliminar: ")
    alumno = next((a for a in curso.alumnos if str(a.codigo) == codigo_alumno), None)

    if alumno:
        curso.alumnos.remove(alumno)
        print(f"Alumno {alumno.nombre} eliminado del curso.")
    else:
        print("Código inválido o alumno no encontrado en este curso.")

#Submenú alumnos
def menu_alumnos():
    while True:
        print("\n--- ALUMNOS ---")
        print("1) Listar todos los alumnos")
        print("2) Mostrar detalle de un alumno")
        print("3) Eliminar un alumno") 
        print("4) Agregar un alumno") 
        print("0) Volver")
        opcion = input("Seleccione una opción: ")

        if opcion == "1":
            listar_alumnos()
        elif opcion == "2":
            mostrar_alumno()
        elif opcion == "3":
            eliminar_alumno()
        elif opcion == "4":
            agregar_alumno()
        elif opcion == "0":
            break
        else:
            print("Opción inválida")

def eliminar_alumno():
    codigo = input("Ingrese el código del alumno a eliminar: ")
    alumno = next((a for a in alumnos if str(a.codigo) == codigo), None)
    
    if alumno:
        # También eliminarlo de todos los cursos
        for curso in cursos:
            if alumno in curso.alumnos:
                curso.alumnos.remove(alumno)

        alumnos.remove(alumno)
        print(f"Alumno {alumno.nombre} eliminado.")
    else:
        print("Alumno no encontrado.")

def agregar_alumno():
    print("\n--- Agregar nuevo alumno ---")
    nombre = input("Nombre del alumno: ")
    codigo = input("Código del alumno: ")
    mac = input("Dirección MAC: ")

    # Validar que no exista el código ya
    if any(a.codigo == codigo for a in alumnos):
        print("Ya existe un alumno con ese código.")
        return

    nuevo_alumno = Alumno(nombre, codigo, mac)
    alumnos.append(nuevo_alumno)
    print(f"Alumno '{nombre}' agregado exitosamente.")


def listar_alumnos():
    for alumno in alumnos:
        print(f"{alumno.codigo} - {alumno.nombre} ({alumno.mac})")

def mostrar_alumno():
    codigo = input("Ingrese el código del alumno: ")
    alumno = next((a for a in alumnos if a.codigo == codigo), None)
    if alumno:
        print(f"Nombre: {alumno.nombre}, Código: {alumno.codigo}, MAC: {alumno.mac}")
    else:
        print("Alumno no encontrado")

#Submenú servidores
def menu_servidores():
    while True:
        print("\n--- SERVIDORES ---")
        print("1) Listar servidores")
        print("2) Mostrar detalle de servidor")
        print("3) Eliminar servidor")  
        print("0) Volver")
        opcion = input("Seleccione una opción: ")

        if opcion == "1":
            listar_servidores()
        elif opcion == "2":
            mostrar_servidor()
        elif opcion == "3":
            eliminar_servidor() 
        elif opcion == "0":
            break
        else:
            print("Opción inválida")

def eliminar_servidor():
    ip = input("Ingrese la IP del servidor a eliminar: ")
    servidor = next((s for s in servidores if s.ip == ip), None)

    if servidor:
        # Eliminar el servidor de todos los cursos
        for curso in cursos:
            if servidor in curso.servidores:
                curso.servidores.remove(servidor)

        servidores.remove(servidor)
        print(f"Servidor '{servidor.nombre}' con IP: '{ip}' eliminado correctamente.")
    else:
        print("Servidor no encontrado.")


def listar_servidores():
    for servidor in servidores:
        print("---------------------------")
        print(f"Nombre: {servidor.nombre}")
        print(f"IP: {servidor.ip}")
        print("---------------------------")
       
def mostrar_servidor():
    nombre = input("Ingrese el nombre del servidor: ")
    servidor = next((s for s in servidores if s.nombre == nombre), None)
    if not servidor:
        print("Servidor no encontrado")
        return

    print(f"\n=== Detalles del servidor '{servidor.nombre}' ===")
    print(f"IP: {servidor.ip}")
    print("Servicios ofrecidos (a nivel general):")
    for servicio in servidor.servicios:
        print(f"  - {servicio['nombre']} ({servicio['protocolo']}:{servicio['puerto']})")

    print("\n=== Cursos que utilizan este servidor ===")
    encontrado = False
    for curso in cursos:
        for s in curso.servidores_info:
            if s['nombre'] == servidor.nombre:
                encontrado = True
                print(f"\nCurso: {curso.codigo} - {curso.nombre} ({curso.estado})")
                print("Servicios permitidos en este curso:")
                for svc in s.get('servicios_permitidos', []):
                    print(f"  - {svc}")

    if not encontrado:
        print("Este servidor no está siendo utilizado por ningún curso.")



#Submenú conexiones
def menu_conexiones():
    while True:
        print("\n--- CONEXIONES ---")
        print("1) Crear conexión")
        print("2) Listar conexiones")
        print("3) Mostrar detalle de conexión")
        print("4) Borrar conexión")
        print("0) Volver")
        opcion = input("Seleccione una opción: ")

        if opcion == "1":
            crear_conexion()
        elif opcion == "2":
            listar_conexiones()
        elif opcion == "3":
            mostrar_conexion()
        elif opcion == "4":
            borrar_conexion()
        elif opcion == "0":
            break
        else:
            print("Opción inválida")

def build_route(route, alumno, servidor, servicio):
    controller_ip = "10.20.12.162"
    url = f"http://{controller_ip}:8080/wm/staticflowpusher/json"

    protocolo = servicio['protocolo'].upper()
    puerto = int(servicio['puerto'])
    mac_src = alumno.mac
    ip_dst = servidor.ip

    # Determinar protocolo L4
    ip_proto = 6 if protocolo == "TCP" else 17  # TCP=6, UDP=17

    for i, hop in enumerate(route):
        dpid = hop['dpid']
        in_port = hop['in_port']
        out_port = hop['out_port']

        # --- FLOW Alumno → Servidor (match L2 + L3 + L4)
        flow_fwd = {
            "switch": dpid,
            "name": f"flow_{alumno.codigo}_to_{servidor.nombre}_{i}",
            "priority": int(40000),
            "active": True,
            "eth_type": "0x800",
            "eth_src": mac_src,
            "ip_proto": ip_proto,
            "ipv4_dst": ip_dst,
            "tp_dst": puerto,
            "in_port": in_port,
            "actions": f"output={out_port}"
        }

        # --- FLOW Servidor → Alumno (match L2 + L3 + L4)
        flow_rev = {
            "switch": dpid,
            "name": f"flow_{servidor.nombre}_to_{alumno.codigo}_{i}",
            "priority": 40000,
            "active": True,
            "eth_type": "0x800",
            "ip_proto": ip_proto,
            "ipv4_src": ip_dst,
            "tp_src": puerto,
            "eth_dst": mac_src,
            "in_port": out_port,
            "actions": f"output={in_port}"
        }

        # --- FLOW ARP Alumno → Servidor
        flow_arp_fwd = {
            "switch": dpid,
            "name": f"arp_{alumno.codigo}_{i}",
            "priority": 10000,
            "eth_type": "0x806",
            "in_port": in_port,
            "actions": f"output={out_port}"
        }

        # --- FLOW ARP Servidor → Alumno
        flow_arp_rev = {
            "switch": dpid,
            "name": f"arp_{servidor.nombre}_{i}",
            "priority": 10000,
            "eth_type": "0x806",
            "in_port": out_port,
            "actions": f"output={in_port}"
        }

        # Enviar todos los flows
        for flow in [flow_fwd, flow_rev, flow_arp_fwd, flow_arp_rev]:
            response = requests.post(url, data=json.dumps(flow), headers={'Content-Type': 'application/json'})
            if response.status_code != 200:
                print(f"[!] Error al insertar flow '{flow['name']}': {response.status_code}")
            else:
                print(f"[✓] Flow '{flow['name']}' insertado correctamente.")

def crear_conexion():
    codigo = input("Código del alumno: ")
    alumno = next((a for a in alumnos if str(a.codigo) == codigo), None)
    if not alumno:
        print("Alumno no encontrado.")
        return

    ip_servidor = input("IP del servidor: ")
    servidor = next((s for s in servidores if s.ip == ip_servidor), None)
    if not servidor:
        print("Servidor no encontrado.")
        return

    print("Servicios disponibles:")
    for i, svc in enumerate(servidor.servicios, 1):
        print(f"{i}) {svc['nombre']} ({svc['protocolo']}:{svc['puerto']})")
    opc = input("Seleccione un servicio por número: ")

    try:
        index = int(opc) - 1
        servicio = servidor.servicios[index]
    except:
        print("Opción inválida.")
        return

    if not es_autorizado(alumno, servidor, servicio['nombre']):
        print("[X] El alumno no está autorizado para usar este servicio en este servidor.")
        return

    ap_src = get_attachment_point(alumno.mac)
    if not ap_src:
        print("[X] No se encontró el punto de acceso del alumno.")
        return

    ruta = get_route(alumno.mac, servidor.ip)
    if not ruta:
        print("[X] No se encontró ruta entre el alumno y el servidor.")
        return

    handler = f"{alumno.codigo}_{servicio['nombre']}_{servidor.nombre}"
    print(f"[✓] Ruta encontrada, instalando flows para handler '{handler}'...")
    build_route(ruta, alumno, servidor, servicio)

    conexion = Conexion(handler, alumno, servidor, servicio, ruta)
    conexiones.append(conexion)
    print(f"[✓] Conexión '{handler}' creada exitosamente.")

def es_autorizado(alumno, servidor, servicio_nombre):
    for curso in cursos:
        if curso.estado != "DICTANDO":
            continue
        if alumno not in curso.alumnos:
            continue
        for s in curso.servidores:
            if s.nombre == servidor.nombre:
                servicios_permitidos = [svc['nombre'] for svc in s.servicios]
                if servicio_nombre in servicios_permitidos:
                    return True
    return False

def listar_conexiones():
    if not conexiones:
        print("No hay conexiones creadas.")
        return
    for c in conexiones:
        print(f"- Handler: {c.handler}")

def get_attachment_point(mac):
    url = "http://10.20.12.162:8080/wm/device/"
    try:
        response = requests.get(url)
        if response.status_code != 200:
            print("[X] No se pudo acceder a /wm/device/")
            return None

        devices = response.json()
        for d in devices:
            if d.get("mac") and mac.lower() in [m.lower() for m in d["mac"]]:
                ap = d.get("attachmentPoint", [])
                if ap:
                    return {"dpid": ap[0]["switchDPID"], "port": ap[0]["port"]}
    except Exception as e:
        print(f"[X] Error en get_attachment_point(): {e}")
    return None



FLOODLIGHT_URL = "http://10.20.12.162:8080"

def get_route(mac_src, mac_dst):
    """
    Determina la ruta entre dos hosts usando BFS a nivel de switches.
    Retorna una lista de hops con dpid, in_port y out_port.
    """

    def obtener_punto_de_conexion(mac_o_ip):
        url = f"{FLOODLIGHT_URL}/wm/device/"
        try:
            respuesta = requests.get(url)
            respuesta.raise_for_status()
            dispositivos = respuesta.json()

            for dispositivo in dispositivos:
                # Buscar por MAC
                if mac_o_ip.lower() in [m.lower() for m in dispositivo.get("mac", [])]:
                    puntos = dispositivo.get("attachmentPoint", [])
                    if puntos:
                        return puntos[0]["switchDPID"], puntos[0]["port"]
                # Buscar por IP
                if mac_o_ip in dispositivo.get("ipv4", []):
                    puntos = dispositivo.get("attachmentPoint", [])
                    if puntos:
                        return puntos[0]["switchDPID"], puntos[0]["port"]
            print(f"[!] El valor {mac_o_ip} no se encuentra conectado (ni como MAC ni como IP).")
            return None
        except requests.RequestException as e:
            print("[!] Error al contactar al controlador Floodlight:", e)
            return None


    def obtener_enlaces_topologia():
        url = f"{FLOODLIGHT_URL}/wm/topology/links/json"
        try:
            respuesta = requests.get(url)
            respuesta.raise_for_status()
            return respuesta.json()
        except requests.RequestException as e:
            print("[!] Error al obtener los enlaces de topología:", e)
            return []

    def construir_grafo(enlaces):
        grafo = defaultdict(list)
        for enlace in enlaces:
            src = enlace["src-switch"]
            dst = enlace["dst-switch"]
            port_src = enlace["src-port"]
            port_dst = enlace["dst-port"]
            grafo[src].append((dst, port_src, port_dst))
            grafo[dst].append((src, port_dst, port_src))  # bidireccional
        return grafo

    def buscar_ruta_bfs(grafo, inicio, fin):
        cola = deque([(inicio, [])])
        visitados = set()

        while cola:
            actual, camino = cola.popleft()
            if actual in visitados:
                continue
            visitados.add(actual)

            if actual == fin:
                return camino + [actual]

            for vecino, _, _ in grafo.get(actual, []):
                if vecino not in visitados:
                    cola.append((vecino, camino + [actual]))

        return None

    def obtener_ruta_detallada(ruta, grafo, puerto_final):
        path = []
        for i in range(len(ruta) - 1):
            origen = ruta[i]
            destino = ruta[i + 1]
            for vecino, port_out, port_in in grafo[origen]:
                if vecino == destino:
                    hop = {
                        "dpid": origen,
                        "in_port": port_in,
                        "out_port": port_out
                    }
                    path.append(hop)
                    break
        path.append({
            "dpid": ruta[-1],
            "in_port": "desconocido",
            "out_port": puerto_final
        })
        return path

    # --- Ejecución ---
    origen = obtener_punto_de_conexion(mac_src)
    destino = obtener_punto_de_conexion(mac_dst)

    if not origen or not destino:
        print("[X] No se pudo determinar el punto de conexión de origen o destino.")
        return None

    dpid_src, port_src = origen
    dpid_dst, port_dst = destino

    enlaces = obtener_enlaces_topologia()
    grafo = construir_grafo(enlaces)
    ruta = buscar_ruta_bfs(grafo, dpid_src, dpid_dst)

    if ruta:
        return obtener_ruta_detallada(ruta, grafo, port_dst)
    else:
        print("[X] No se encontró una ruta en la topología.")
        return None


def mostrar_conexion():
    handler = input("Ingrese el handler de la conexión: ")
    c = next((x for x in conexiones if x.handler == handler), None)
    if not c:
        print("Conexión no encontrada.")
        return

    print(f"\n=== Detalles de '{handler}' ===")
    print(f"Alumno   : {c.alumno.nombre} ({c.alumno.codigo})")
    print(f"Servidor : {c.servidor.nombre} ({c.servidor.ip})")
    print(f"Servicio : {c.servicio['nombre']} ({c.servicio['protocolo']}:{c.servicio['puerto']})")
    print("Ruta:")
    for hop in c.ruta:
        print(f"  Switch: {hop['dpid']} | in: {hop['in_port']} -> out: {hop['out_port']}")

def borrar_conexion():
    handler = input("Ingrese el handler de la conexión a borrar: ")
    c = next((x for x in conexiones if x.handler == handler), None)
    if not c:
        print("Conexión no encontrada.")
        return

    controller_ip = "10.20.12.162"
    url = f"http://{controller_ip}:8080/wm/staticflowpusher/json"

    for i, hop in enumerate(c.ruta):
        names = [
            f"flow_{c.alumno.codigo}_to_{c.servidor.nombre}_{i}",
            f"flow_{c.servidor.nombre}_to_{c.alumno.codigo}_{i}",
            f"arp_{c.alumno.codigo}_{i}",
            f"arp_{c.servidor.nombre}_{i}"
        ]
        for name in names:
            payload = {"name": name}
            res = requests.delete(url, json=payload)
            if res.status_code == 200:
                print(f"[✓] Flow '{name}' eliminado")
            else:
                print(f"[!] No se pudo eliminar '{name}'")

    conexiones.remove(c)
    print(f"[✓] Conexión '{handler}' eliminada.")


#Main ejecutable
if __name__ == "__main__":
    menu()
