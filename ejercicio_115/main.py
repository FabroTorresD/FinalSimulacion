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
a1            = st.sidebar.number_input("Aten. a1 (min)", 0.1, 10.0, 3.0)
b1            = st.sidebar.number_input("Aten. b1 (min)", 0.1, 10.0, 4.0)
a2            = st.sidebar.number_input("Rep. a2 (min)", 1.0, 50.0, 10.0)
b2            = st.sidebar.number_input("Rep. b2 (min)", 1.0, 50.0, 20.0)
p_retiro      = st.sidebar.slider("Probabilidad retiro", 0.0, 1.0, 0.5, 0.01)
jornada       = st.sidebar.number_input("Duración jornada (min)", 1, 2000, 960)

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

    # ---------------- variables de estado -----------------
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
    # Generador de nuevos IDs inicia después de los iniciales
    id_generator = count(start=stock_inicial+1)

    # Estado de stock inicial: IDs 1..stock_inicial
    ready_queue = list(range(1, stock_inicial+1))
    zapatos_para_retirar = stock_inicial   # stock listo (initial)
    cant_pares_reparados = 0               # sólo los reparados en esta simulación

    # Seguimiento de objetos temporales (Todos: "Listo para retiro" o estados posteriores)
    zapatos_estado: dict[int, str] = {i: 'Listo para retiro' for i in ready_queue}
    current_repair_id: int | None = None

    # estadísticas
    acum_tiempo_rep = 0.0
    max_avg_rep     = 0.0
    cant_max_cola   = 0

    filas: list[dict] = []

    # helper safe-round
    safe = lambda v: round(v, 2) if v is not None else None

    def registrar(evento: str, rnd_pet=None, tipo_pet=None):
        nonlocal nro_evento, max_avg_rep, cant_max_cola
        promedio_act = (acum_tiempo_rep / cant_pares_reparados) if cant_pares_reparados else 0.0
        max_avg_rep  = max(max_avg_rep, promedio_act)
        cant_max_cola = max(cant_max_cola, len(cola_pedidos))

        # snapshot de estado de zapatos
        snapshot = zapatos_estado.copy()

        filas.append({
            "Nro_evento": nro_evento,
            "Evento": evento,
            "Reloj": safe(reloj),
            "RND_llegada": safe(rnd_llegada) if evento == "Llegada" else None,
            "Tiempo_entre_llegadas": safe(tiempo_entre) if (evento == "Llegada" and tiempo_entre is not None) else None,
            "Proxima_llegada": safe(prox_llegada) if prox_llegada != math.inf else None,
            "RND_peticion": safe(rnd_pet) if evento == "Llegada" else None,
            "Tipo_peticion": tipo_pet if evento == "Llegada" else None,
            "RND_atencion": safe(rnd_atencion) if evento in ("Llegada", "Fin_atencion") else None,
            "Tiempo_atencion": safe(tiempo_atencion) if evento in ("Llegada", "Fin_atencion") else None,
            "Fin_atencion": safe(fin_atencion) if fin_atencion != math.inf else None,
            "RND_reparacion": safe(rnd_reparacion) if evento == "Fin_reparacion" else None,
            "Tiempo_reparacion": safe(tiempo_reparacion) if evento == "Fin_reparacion" else None,
            "Fin_reparacion": safe(fin_reparacion) if fin_reparacion != math.inf else None,
            "Estado_zapatero": estado_zapatero,
            "Cant_pares_reparados": cant_pares_reparados,
            "Zapatos_para_retirar": zapatos_para_retirar,
            "Objetos_temporales": snapshot,
        })
        nro_evento += 1

    # fila inicial
    registrar("Inicial")

    while True:
        evento = None
        proximo = math.inf
        if prox_llegada < proximo:
            evento, proximo = "Llegada", prox_llegada
        if fin_atencion < proximo:
            evento, proximo = "Fin_atencion", fin_atencion
        if fin_reparacion < proximo:
            evento, proximo = "Fin_reparacion", fin_reparacion
        if evento is None:
            break

        reloj = proximo

        if evento == "Llegada":
            rnd_peticion = random.random()
            tipo_peticion = "Retiro" if rnd_peticion < p_retiro else "Pedido"

            if reloj < jornada:
                rnd_llegada, tiempo_entre = gen_exponencial(mu)
                prox_llegada = reloj + tiempo_entre
            else:
                rnd_llegada = tiempo_entre = None
                prox_llegada = math.inf

            if estado_zapatero == "Reparando":
                reparacion_restante = fin_reparacion - reloj
                fin_reparacion = math.inf
                rnd_reparacion = tiempo_reparacion = None

            rnd_atencion, tiempo_atencion = gen_uniforme(a1, b1)
            fin_atencion = reloj + tiempo_atencion
            estado_zapatero = "Atendiendo"

            # Pedido: encolar nuevo zapato
            if tipo_peticion == "Pedido":
                nuevo_id = next(id_generator)
                cola_pedidos.append(nuevo_id)
                zapatos_estado[nuevo_id] = "En cola"

            # Retiro: sacar del ready_queue y marcar Retirado
            if tipo_peticion == "Retiro" and ready_queue:
                id_retiro = ready_queue.pop(0)
                zapatos_estado[id_retiro] = "Retirado"
                zapatos_para_retirar -= 1

            registrar("Llegada", rnd_peticion, tipo_peticion)

        elif evento == "Fin_atencion":
            fin_atencion = math.inf

            # decidir siguiente acción
            if reparacion_restante is not None:
                tiempo_reparacion = reparacion_restante
                fin_reparacion = reloj + tiempo_reparacion
                reparacion_restante = None
                rnd_reparacion = random.random()
                if current_repair_id is not None:
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
            cant_pares_reparados += 1
            acum_tiempo_rep += tiempo_reparacion

            # terminar reparación: nuevo ready
            if current_repair_id is not None:
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

        if prox_llegada == math.inf and fin_atencion == math.inf and fin_reparacion == math.inf:
            break

    df = pd.DataFrame(filas)
    # desplegar objetos temporales como columnas dinámicas
    df_objs = pd.json_normalize(df['Objetos_temporales']).rename(columns=lambda x: f'Zapato_{x}')
    df = pd.concat([df.drop(columns=['Objetos_temporales']), df_objs], axis=1)
    return df, max_avg_rep, cant_max_cola

# -----------------------------------------------------------
# 4) Ejecución desde Streamlit
# -----------------------------------------------------------
if st.sidebar.button("Arrancar simulación"):
    df, max_prom_rep, max_cola = simular_dia(
        stock_inicial, mu, a1, b1, a2, b2, p_retiro, jornada
    )

    st.subheader("Vector de Estado")
    st.dataframe(df, use_container_width=True)

    col1, col2 = st.columns(2)
    col1.metric("Máx. promedio reparación (min)", f"{max_prom_rep:.2f}")
    col2.metric("Máx. clientes en cola", max_cola)
