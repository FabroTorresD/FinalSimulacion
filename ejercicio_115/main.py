import streamlit as st
import pandas as pd
import random
import math
from itertools import count
from utils import generar_nueva_fila_multiindex, marcar_zapatos_retirados, limpiar_zapatos_retirados, generar_estilos_dataframe


# -----------------------------------------------------------
# 1) Interface Streamlit – parámetros de entrada
# -----------------------------------------------------------
st.title("Ejercicio 115 – Final de Simulación")

"""
Simulador discreto – Casa de Reparaciones de Zapatos
"""

stock_inicial = st.sidebar.number_input("Stock inicial de zapatos reparados", 0, 100, 10)
mu            = st.sidebar.number_input("Media entre llegadas (min)", 1.0, 100.0, 20.0)
a1            = st.sidebar.number_input("Atención (min) - mínimo", 0.1, 10.0, 3.0)
b1            = st.sidebar.number_input("Atención (min) - máximo", 0.1, 10.0, 4.0)
a2            = st.sidebar.number_input("Reparación (min) - mínimo", 1.0, 50.0, 10.0)
b2            = st.sidebar.number_input("Reparación (min) - máximo", 1.0, 50.0, 20.0)
p_retiro      = st.sidebar.slider("Probabilidad de retiro", 0.0, 1.0, 0.5, 0.01)
jornada       = st.sidebar.number_input("Duración de la jornada (min)", 1, 2000, 480)

# -----------------------------------------------------------
# 2) Generadores auxiliares
# -----------------------------------------------------------
def gen_exponencial(media: float) -> tuple[float, float]:
    rnd = random.random()
    valor = -media * math.log(1 - rnd)
    return rnd, valor


def gen_uniforme(a: float, b: float) -> tuple[float, float]:
    rnd = random.random()
    valor = a + rnd * (b - a)
    return rnd, valor

# -----------------------------------------------------------
# 3) Simulación de un día
# -----------------------------------------------------------
def simular_dia(stock_inicial: int, mu: float, a1: float, b1: float,
                a2: float, b2: float, p_retiro: float, jornada: int):
    reloj           = 0.0
    nro_evento      = 0
    rnd_llegada, tiempo_entre = gen_exponencial(mu)
    prox_llegada    = reloj + tiempo_entre

    rnd_atencion = tiempo_atencion = None
    fin_atencion  = math.inf

    rnd_reparacion = tiempo_reparacion = None
    fin_reparacion = math.inf
    reparacion_restante = None

    estado_zapatero = "Libre"
    cola_pedidos: list[int] = []
    id_generator = count(start=stock_inicial+1)

    # IDs iniciales como "Listo para retiro"
    ready_queue = list(range(1, stock_inicial+1))
    zapatos_para_retirar = stock_inicial
    cant_pares_reparados = 0
    zapatos_estado: dict[int, str] = {i: 'Listo para retiro' for i in ready_queue}
    zapatos_hora_inicio: dict[int, float] = {i: None for i in ready_queue}  # Hora inicio reparación
    current_repair_id: int | None = None

    # Variables para estadísticas
    acum_tiempo_rep = 0.0
    cant_max_cola   = 0
    filas: list[dict] = []
    
    # Modificar la función safe para asegurar 2 decimales en todos los números, enteros para IDs
    def safe(v, es_id=False):
        if v is None:
            return None
        elif es_id and isinstance(v, (int, float)):
            return int(v)
        elif isinstance(v, (int, float)):
            return round(float(v), 2)
        else:
            return v

    # Variables para persistir eventos futuros
    eventos_persistentes = {
        "Proxima_llegada": None,
        "Fin_atencion": None,
        "Fin_reparacion": None,
        "RND_llegada": None,
        "Tiempo_entre_llegadas": None,
        "RND_atencion": None,
        "Tiempo_atencion": None,
        "RND_reparacion": None,
        "Tiempo_reparacion": None
    }
    
    # Para tracking de zapatos retirados
    zapatos_recien_retirados = set()

    def actualizar_eventos_persistentes(evento_actual):
        # Actualizar valores persistentes
        if prox_llegada != math.inf:
            eventos_persistentes["Proxima_llegada"] = safe(prox_llegada)
            eventos_persistentes["RND_llegada"] = safe(rnd_llegada)
            eventos_persistentes["Tiempo_entre_llegadas"] = safe(tiempo_entre)
        else:
            if evento_actual != "Llegada":
                # Mantener valores previos si no es una llegada
                pass
            else:
                eventos_persistentes["Proxima_llegada"] = None
                eventos_persistentes["RND_llegada"] = None
                eventos_persistentes["Tiempo_entre_llegadas"] = None

        if fin_atencion != math.inf:
            eventos_persistentes["Fin_atencion"] = safe(fin_atencion)
            eventos_persistentes["RND_atencion"] = safe(rnd_atencion)
            eventos_persistentes["Tiempo_atencion"] = safe(tiempo_atencion)
        else:
            if evento_actual != "Fin_atencion":
                # Mantener valores previos si no es fin de atención
                pass
            else:
                eventos_persistentes["Fin_atencion"] = None
                eventos_persistentes["RND_atencion"] = None
                eventos_persistentes["Tiempo_atencion"] = None

        if fin_reparacion != math.inf:
            eventos_persistentes["Fin_reparacion"] = safe(fin_reparacion)
            eventos_persistentes["RND_reparacion"] = safe(rnd_reparacion)
            eventos_persistentes["Tiempo_reparacion"] = safe(tiempo_reparacion)
        else:
            if evento_actual != "Fin_reparacion":
                # Mantener valores previos si no es fin de reparación
                pass
            else:
                eventos_persistentes["Fin_reparacion"] = None
                eventos_persistentes["RND_reparacion"] = None
                eventos_persistentes["Tiempo_reparacion"] = None

    def crear_columnas_objetos_multiindex():
        """Crea las columnas de objetos temporales con multi-índice"""
        objetos_cols = {}
        for zapato_id, estado in zapatos_estado.items():
            objetos_cols[f"Zapato_{zapato_id}"] = estado
        return objetos_cols

    def registrar(evento: str, rnd_pet=None, tipo_pet=None):
        nonlocal nro_evento, cant_max_cola, zapatos_recien_retirados
        cant_max_cola = max(cant_max_cola, len(cola_pedidos))
        
        actualizar_eventos_persistentes(evento)
        
        # Marcar zapatos retirados antes de crear la fila
        if zapatos_recien_retirados:
            zapatos_estado_marcado = marcar_zapatos_retirados(zapatos_estado, zapatos_recien_retirados)
        else:
            zapatos_estado_marcado = zapatos_estado.copy()
        
        # Crear estado actual para generar fila con multi-índice
        estado_actual = {
            "nro_evento": nro_evento,
            "evento": evento,
            "reloj": safe(reloj),
            "rnd_llegada": eventos_persistentes["RND_llegada"],
            "tiempo_entre_llegadas": eventos_persistentes["Tiempo_entre_llegadas"],
            "proxima_llegada": eventos_persistentes["Proxima_llegada"],
            "rnd_peticion": safe(rnd_pet) if evento == "Llegada" else None,
            "tipo_peticion": tipo_pet if evento == "Llegada" else None,
            "rnd_atencion": eventos_persistentes["RND_atencion"],
            "tiempo_atencion": eventos_persistentes["Tiempo_atencion"],
            "fin_atencion": eventos_persistentes["Fin_atencion"],
            "rnd_reparacion": eventos_persistentes["RND_reparacion"],
            "tiempo_reparacion": eventos_persistentes["Tiempo_reparacion"],
            "fin_reparacion": eventos_persistentes["Fin_reparacion"],
            "estado_zapatero": estado_zapatero,
            "cant_pares_reparados": cant_pares_reparados,
            "zapatos_para_retirar": zapatos_para_retirar,
            # Columnas de estadísticas agregadas
            "cola_pedidos": len(cola_pedidos),
            "max_cola": cant_max_cola,
            "acum_tiempo_reparacion": acum_tiempo_rep,
            "objetos_temporales": zapatos_estado_marcado,
            "horas_inicio_reparacion": zapatos_hora_inicio
        }
        
        # Generar fila con multi-índice usando utils.py
        fila_multiindex = generar_nueva_fila_multiindex(estado_actual, con_objetos_temporales=True)
        filas.append(fila_multiindex)
        
        # Limpiar zapatos retirados después de registrar
        if zapatos_recien_retirados:
            for zapato_id in zapatos_recien_retirados:
                if zapato_id in zapatos_estado:
                    del zapatos_estado[zapato_id]
                if zapato_id in zapatos_hora_inicio:
                    del zapatos_hora_inicio[zapato_id]
            zapatos_recien_retirados.clear()
        
        nro_evento += 1

    registrar("Inicial")
    while True:
        evento, proximo = min(
            ("Llegada", prox_llegada),
            ("Fin_atencion", fin_atencion),
            ("Fin_reparacion", fin_reparacion),
            key=lambda x: x[1]
        )
        if proximo == math.inf:
            break
        reloj = proximo

        if evento == "Llegada":
            rnd_peticion = random.random()
            tipo_peticion = "Retiro" if rnd_peticion < p_retiro else "Pedido"
            if reloj < jornada:
                rnd_llegada, tiempo_entre = gen_exponencial(mu)
                prox_llegada = reloj + tiempo_entre
            else:
                prox_llegada = math.inf
            if estado_zapatero == "Reparando":
                reparacion_restante = fin_reparacion - reloj
                fin_reparacion = math.inf
            rnd_atencion, tiempo_atencion = gen_uniforme(a1, b1)
            fin_atencion = reloj + tiempo_atencion
            estado_zapatero = "Atendiendo"
            if tipo_peticion == "Pedido":
                nuevo_id = next(id_generator)
                cola_pedidos.append(nuevo_id)
                rnd_reparacion, tiempo_reparacion = gen_uniforme(a2, b2)
                zapatos_estado[nuevo_id] = "En cola"
                zapatos_hora_inicio[nuevo_id] = None  # Inicializar hora inicio
            else:
                if ready_queue:
                    id_retiro = ready_queue.pop(0)
                    zapatos_recien_retirados.add(id_retiro)  # Marcar como retirado
                    zapatos_para_retirar -= 1
            registrar("Llegada", rnd_peticion, tipo_peticion)

        elif evento == "Fin_atencion":
            fin_atencion = math.inf
            if reparacion_restante is not None:
                tiempo_reparacion = reparacion_restante
                fin_reparacion = reloj + tiempo_reparacion
                reparacion_restante = None
                if current_repair_id:
                    zapatos_estado[current_repair_id] = "Reparando"
                estado_zapatero = "Reparando"
            elif cola_pedidos:
                current_repair_id = cola_pedidos.pop(0)
                rnd_reparacion, tiempo_reparacion = gen_uniforme(a2, b2)
                fin_reparacion = reloj + tiempo_reparacion
                zapatos_estado[current_repair_id] = "Reparando"
                zapatos_hora_inicio[current_repair_id] = reloj  # Registrar hora inicio
                estado_zapatero = "Reparando"
            else:
                estado_zapatero = "Libre"
            registrar("Fin_atencion")

        elif evento == "Fin_reparacion":
            fin_reparacion = math.inf
            estado_zapatero = "Libre"
            acum_tiempo_rep += tiempo_reparacion
            cant_pares_reparados += 1
            if current_repair_id:
                ready_queue.append(current_repair_id)
                zapatos_estado[current_repair_id] = "Listo para retiro"
                zapatos_para_retirar += 1
            if cola_pedidos:
                current_repair_id = cola_pedidos.pop(0)
                rnd_reparacion, tiempo_reparacion = gen_uniforme(a2, b2)
                fin_reparacion = reloj + tiempo_reparacion
                zapatos_estado[current_repair_id] = "Reparando"
                zapatos_hora_inicio[current_repair_id] = reloj  # Registrar hora inicio
                estado_zapatero = "Reparando"
            registrar("Fin_reparacion")

    # Crear DataFrame con multi-índice
    df = pd.DataFrame(filas)
    
    # El DataFrame ya viene con estructura multi-índice desde generar_nueva_fila_multiindex
    if not df.empty:
        # Convertir las tuplas de columnas a MultiIndex
        columnas_tuples = [col if isinstance(col, tuple) else ("", col) for col in df.columns]
        df.columns = pd.MultiIndex.from_tuples(columnas_tuples)
    
    avg_rep = acum_tiempo_rep / cant_pares_reparados if cant_pares_reparados else 0.0
    return df, avg_rep, cant_max_cola

# -----------------------------------------------------------
# 4) Ejecución desde Streamlit
# -----------------------------------------------------------
if st.sidebar.button("Arrancar simulación"):
    df, avg_rep, max_cola = simular_dia(
        stock_inicial, mu, a1, b1, a2, b2, p_retiro, jornada
    )
    st.subheader("Simulacion")
    
    # Aplicar estilos para resaltar zapatos retirados
    try:
        styled_df = df.style.applymap(generar_estilos_dataframe())
        st.dataframe(styled_df, use_container_width=True)
    except:
        # Si hay error con el styling, mostrar DataFrame sin estilos
        st.dataframe(df, use_container_width=True)
    
    col1, col2 = st.columns(2)
    col1.metric("Tiempo promedio reparación", f"{avg_rep:.2f}")
    col2.metric("Máx. clientes en cola", max_cola)