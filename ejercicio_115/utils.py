# utils.py
import random
import math

# ------------------------------------------------------------
# 1) Generación de variables aleatorias
# ------------------------------------------------------------
def generar_numeros_aleatorios(tipo: str, params):
    """
    Devuelve (valor, rnd) según la distribución solicitada.

    • tipo = "Uniforme": params = (a, b)
    • tipo = "Exponencial": params = (lambda_,)   [media = 1/lambda_]
    """
    rnd = random.random()

    if tipo.lower() == "uniforme":
        a, b = params
        valor = a + rnd * (b - a)
        return valor, rnd

    elif tipo.lower() == "exponencial":
        (lam,) = params if isinstance(params, tuple) else (params,)
        valor = -math.log(1 - rnd) / lam
        return valor, rnd

    else:
        raise ValueError(f"Distribución no soportada: {tipo}")

# ------------------------------------------------------------
# 2) Conversión de un dict de estado a fila con Multi-Index
# ------------------------------------------------------------
def generar_nueva_fila_multiindex(estado_actual, con_objetos_temporales=True):
    """
    Genera una fila con multi-índice para el DataFrame de simulación.
    Similar al patrón usado en el TP de canchas deportivas pero adaptado 
    para la zapatería.
    
    Args:
        estado_actual: dict con el estado actual de la simulación
        con_objetos_temporales: bool, si incluir o no los objetos temporales
    
    Returns:
        dict con estructura de multi-índice (categoria, campo): valor
    """
    
    # Función auxiliar para formatear valores
    def format_value(v, es_id=False):
        if v is None:
            return ""
        elif es_id and isinstance(v, (int, float)):
            return int(v)  # IDs como enteros
        elif isinstance(v, (int, float)):
            return round(float(v), 2)  # Números con 2 decimales
        else:
            return v
    
    nueva_fila = {
        ("", "Nro_evento"): format_value(estado_actual.get("nro_evento"), es_id=True),
        ("", "Evento"): estado_actual.get("evento", ""),
        ("", "Reloj"): format_value(estado_actual.get("reloj")),
        ("", "RND_llegada"): format_value(estado_actual.get("rnd_llegada")),
        ("", "Tiempo_entre_llegadas"): format_value(estado_actual.get("tiempo_entre_llegadas")),
        ("", "Proxima_llegada"): format_value(estado_actual.get("proxima_llegada")),
        ("", "RND_peticion"): format_value(estado_actual.get("rnd_peticion")),
        ("", "Tipo_peticion"): estado_actual.get("tipo_peticion", ""),
        ("", "RND_atencion"): format_value(estado_actual.get("rnd_atencion")),
        ("", "Tiempo_atencion"): format_value(estado_actual.get("tiempo_atencion")),
        ("", "Fin_atencion"): format_value(estado_actual.get("fin_atencion")),
        ("", "RND_reparacion"): format_value(estado_actual.get("rnd_reparacion")),
        ("", "Tiempo_reparacion"): format_value(estado_actual.get("tiempo_reparacion")),
        ("", "Fin_reparacion"): format_value(estado_actual.get("fin_reparacion")),
        ("", "Estado_zapatero"): estado_actual.get("estado_zapatero", ""),
        ("", "Cant_pares_reparados"): format_value(estado_actual.get("cant_pares_reparados"), es_id=True),
        ("", "Zapatos_para_retirar"): format_value(estado_actual.get("zapatos_para_retirar"), es_id=True),
        
        # Columnas de estadísticas agregadas
        ("Estadísticas", "Cola_pedidos"): format_value(estado_actual.get("cola_pedidos"), es_id=True),
        ("Estadísticas", "Max_cola"): format_value(estado_actual.get("max_cola"), es_id=True),
        ("Estadísticas", "Acum_tiempo_reparacion"): format_value(estado_actual.get("acum_tiempo_reparacion")),
        ("Estadísticas", "Tiempo_promedio_reparacion"): format_value(estado_actual.get("tiempo_promedio_reparacion")),
    }
    
    if con_objetos_temporales:
        objetos_temporales = estado_actual.get("objetos_temporales", {})
        for zapato_id, estado_zapato in objetos_temporales.items():
            # Cambiar de "Zapato N" a solo "Zapato"
            obj_nombre = "Zapato"
            nueva_fila[(obj_nombre, f"ID_{zapato_id}")] = format_value(zapato_id, es_id=True)
            nueva_fila[(obj_nombre, f"Estado_{zapato_id}")] = estado_zapato
    
    return nueva_fila

# ------------------------------------------------------------
# 3) Función auxiliar para procesar objetos temporales desde dict
# ------------------------------------------------------------
def procesar_objetos_temporales_desde_dict(zapatos_estado: dict):
    """
    Convierte el diccionario zapatos_estado a formato de objetos temporales
    para usar con generar_nueva_fila_multiindex.
    
    Args:
        zapatos_estado: dict {id: estado} de los zapatos
    
    Returns:
        dict en formato para objetos_temporales
    """
    return zapatos_estado

# ------------------------------------------------------------
# 4) Función para marcar zapatos retirados (eliminados del sistema)
# ------------------------------------------------------------
def marcar_zapatos_retirados(zapatos_estado: dict, retirados: set):
    """
    Marca los zapatos retirados para visualización especial.
    Los zapatos retirados se mantienen por una fila más con estado especial
    antes de ser eliminados completamente.
    
    Args:
        zapatos_estado: dict actual de estados de zapatos
        retirados: set de IDs de zapatos recién retirados
    
    Returns:
        dict actualizado con marcado especial para retirados
    """
    estado_actualizado = zapatos_estado.copy()
    
    # Marcar los recién retirados con estado especial (sin emoji)
    for zapato_id in retirados:
        if zapato_id in estado_actualizado:
            estado_actualizado[zapato_id] = "Retirado"  # Sin emoji
    
    return estado_actualizado

def limpiar_zapatos_retirados(zapatos_estado: dict):
    """
    Elimina los zapatos que ya fueron marcados como retirados en la iteración anterior.
    
    Args:
        zapatos_estado: dict de estados de zapatos
    
    Returns:
        dict sin los zapatos ya retirados
    """
    return {id_zapato: estado for id_zapato, estado in zapatos_estado.items() 
            if estado != "Retirado"}

# ------------------------------------------------------------
# 5) Función para generar colores de fondo (para Streamlit styling)
# ------------------------------------------------------------
def generar_estilos_dataframe():
    """
    Genera estilos CSS para el DataFrame que resalte los zapatos retirados.
    
    Returns:
        dict con estilos para aplicar al DataFrame
    """
    def colorear_retirados(val):
        """Aplica color de fondo rojo claro a zapatos retirados"""
        if isinstance(val, str) and val == "Retirado":
            return 'background-color: #ffcccb'  # Rojo claro
        return ''
    
    return colorear_retirados