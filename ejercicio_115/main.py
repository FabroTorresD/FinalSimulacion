import streamlit as st
import pandas as pd
import random
import math
from itertools import count

"""
Ejercicio 115 – Final de Simulación
Simulador discreto – Casa de Reparaciones de Zapatos
"""

# -----------------------------------------------------------
# 1) Interface Streamlit – parámetros de entrada
# -----------------------------------------------------------
st.title("Ejercicio 115 – Final de Simulación")

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
    current_repair_id: int | None = None

    acum_tiempo_rep = 0.0
    cant_max_cola   = 0
    filas: list[dict] = []
    safe = lambda v: round(v, 2) if v is not None else None

    def registrar(evento: str, rnd_pet=None, tipo_pet=None):
        nonlocal nro_evento, cant_max_cola
        cant_max_cola = max(cant_max_cola, len(cola_pedidos))
        snapshot = zapatos_estado.copy()
        filas.append({
            "Nro_evento": nro_evento,
            "Evento": evento,
            "Reloj": safe(reloj),
            # Llegadas
            "RND_llegada": safe(rnd_llegada) if evento == "Llegada" else None,
            "Tiempo_entre_llegadas": safe(tiempo_entre) if evento == "Llegada" else None,
            "Proxima_llegada": safe(prox_llegada) if evento == "Llegada" else None,
            # Petición
            "RND_peticion": safe(rnd_pet) if evento == "Llegada" else None,
            "Tipo_peticion": tipo_pet if evento == "Llegada" else None,
            # Atención
            "RND_atencion": safe(rnd_atencion) if evento in ("Llegada","Fin_atencion") else None,
            "Tiempo_atencion": safe(tiempo_atencion) if evento in ("Llegada","Fin_atencion") else None,
            "Fin_atencion": safe(fin_atencion) if evento in ("Llegada","Fin_atencion") else None,
            # Reparación (inicio y fin)
            "RND_reparacion": safe(rnd_reparacion) if evento in ("Fin_atencion","Fin_reparacion") else None,
            "Tiempo_reparacion": safe(tiempo_reparacion) if evento in ("Fin_atencion","Fin_reparacion") else None,
            "Fin_reparacion": safe(fin_reparacion) if evento in ("Fin_atencion","Fin_reparacion") else None,
            # Estados y estadísticas
            "Estado_zapatero": estado_zapatero,
            "Cant_pares_reparados": cant_pares_reparados,
            "Zapatos_para_retirar": zapatos_para_retirar,
            "Objetos_temporales": snapshot,
        })
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
            else:
                if ready_queue:
                    id_retiro = ready_queue.pop(0)
                    zapatos_estado[id_retiro] = "Retirado"
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
                estado_zapatero = "Reparando"
            registrar("Fin_reparacion")

    df = pd.DataFrame(filas)
    df_objs = pd.json_normalize(df['Objetos_temporales']).rename(columns=lambda x: f'Zapato_{x}')
    df = pd.concat([df.drop(columns=['Objetos_temporales']), df_objs], axis=1)
    avg_rep = acum_tiempo_rep / cant_pares_reparados if cant_pares_reparados else 0.0
    return df, avg_rep, cant_max_cola

# -----------------------------------------------------------
# 4) Ejecución desde Streamlit
# -----------------------------------------------------------
if st.sidebar.button("Arrancar simulación"):
    df, avg_rep, max_cola = simular_dia(
        stock_inicial, mu, a1, b1, a2, b2, p_retiro, jornada
    )
    st.subheader("Vector de Estado")
    st.dataframe(df, use_container_width=True)
    col1, col2 = st.columns(2)
    col1.metric("Tiempo promedio reparación (min)", f"{avg_rep:.2f}")
    col2.metric("Máx. clientes en cola", max_cola)
