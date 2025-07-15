import streamlit as st
import pandas as pd
import random
import math
from itertools import count

# ---------------------------------------------------------------------
# 1) Interface Streamlit – parámetros de entrada
# ---------------------------------------------------------------------
st.title("Ejercicio 115 – Final de Simulación")

st.subheader("Simulador discreto – Casa de Reparaciones de Zapatos")

stock_inicial = st.sidebar.number_input("Stock inicial de zapatos reparados", 0, 100, 10)
mu            = st.sidebar.number_input("Media entre llegadas (min)", 1.0, 100.0, 20.0)
a1            = st.sidebar.number_input("Aten. a1 (min)", 0.1, 10.0, 3.0)
b1            = st.sidebar.number_input("Aten. b1 (min)", 0.1, 10.0, 4.0)
a2            = st.sidebar.number_input("Rep. a2 (min)", 1.0, 50.0, 10.0)
b2            = st.sidebar.number_input("Rep. b2 (min)", 1.0, 50.0, 20.0)
p_retiro      = st.sidebar.slider("Probabilidad retiro", 0.0, 1.0, 0.5, 0.01)
jornada       = st.sidebar.number_input("Duración jornada (min)", 1, 2000, 960)

# ---------------------------------------------------------------------
# 2) Generadores auxiliares
# ---------------------------------------------------------------------

def gen_exponencial(media: float) -> tuple[float, float]:
    rnd = random.random()
    valor = -media * math.log(1 - rnd)
    return rnd, valor


def gen_uniforme(a: float, b: float) -> tuple[float, float]:
    rnd = random.random()
    valor = a + rnd * (b - a)
    return rnd, valor

# ---------------------------------------------------------------------
# 3) Simulación de un día
# ---------------------------------------------------------------------

def simular_dia(stock_inicial: int, mu: float, a1: float, b1: float,
                a2: float, b2: float, p_retiro: float, jornada: int):
    reloj = 0.0
    nro_evento = 0

    # Eventos
    rnd_llegada, tiempo_entre = gen_exponencial(mu)
    prox_llegada = reloj + tiempo_entre
    rnd_atencion = None
    tiempo_atencion = None
    fin_atencion = math.inf
    rnd_reparacion = None
    tiempo_reparacion = None
    fin_reparacion = math.inf
    reparacion_restante = None

    # Estado y colas
    estado_zapatero = "Libre"
    cola_pedidos = []
    id_generator = count(start=1)
    zapatos_reparados = stock_inicial
    zapatos_temporales = []

    # Estadísticas
    acum_tiempo_reparacion = 0.0
    cant_pares_reparados_real = 0
    max_promedio = 0.0
    cant_max_cola = 0

    filas = []
    def registrar(evento: str):
        nonlocal nro_evento, max_promedio
        promedio = acum_tiempo_reparacion / cant_pares_reparados_real if cant_pares_reparados_real else 0.0
        max_promedio = max(max_promedio, promedio)
        filas.append({
            "Nro_evento": nro_evento,
            "Evento": evento,
            "Reloj": reloj,
            "RND_llegada": rnd_llegada if evento == "Llegada" else None,
            "Tiempo_entre_llegadas": tiempo_entre if evento == "Llegada" else None,
            "Proxima_llegada": prox_llegada if prox_llegada != math.inf else None,
            "RND_peticion": rnd_peticion if evento == "Llegada" else None,
            "Tipo_peticion": tipo_peticion if evento == "Llegada" else None,
            "RND_atencion": rnd_atencion if evento in ("Llegada", "Fin_atencion") else None,
            "Tiempo_atencion": tiempo_atencion if evento in ("Llegada", "Fin_atencion") else None,
            "Fin_atencion": fin_atencion if fin_atencion != math.inf else None,
            "RND_reparacion": rnd_reparacion if evento in ("Inicio_reparacion", "Fin_reparacion") else None,
            "Tiempo_reparacion": tiempo_reparacion if evento in ("Inicio_reparacion", "Fin_reparacion") else None,
            "Fin_reparacion": fin_reparacion if fin_reparacion != math.inf else None,
            "Estado_zapatero": estado_zapatero,
            "Acum_tiempo_reparacion": acum_tiempo_reparacion,
            "Cant_zapatos_reparados": zapatos_reparados,
            "Promedio_rep": promedio,
            "Max_promedio_rep": max_promedio,
            "Cant_max_cola": cant_max_cola,
        })
        nro_evento += 1

    rnd_peticion = None
    tipo_peticion = None
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
                rnd_llegada, tiempo_entre, prox_llegada = None, None, math.inf
            if estado_zapatero == "Reparando":
                reparacion_restante = fin_reparacion - reloj
                fin_reparacion = math.inf
            rnd_atencion, tiempo_atencion = gen_uniforme(a1, b1)
            fin_atencion = reloj + tiempo_atencion
            estado_zapatero = "Atendiendo"
            registrar("Llegada")

        elif evento == "Fin_atencion":
            fin_atencion = math.inf
            if tipo_peticion == "Retiro":
                if zapatos_reparados > 0:
                    zapatos_reparados -= 1
            else:
                nuevo_id = next(id_generator)
                cola_pedidos.append(nuevo_id)
                zapatos_temporales.append({"id": nuevo_id, "estado": "En cola"})
            if reparacion_restante is not None:
                rnd_reparacion = random.random()
                tiempo_reparacion = reparacion_restante
                fin_reparacion = reloj + tiempo_reparacion
                reparacion_restante = None
                estado_zapatero = "Reparando"
                registrar("Inicio_reparacion")
            elif cola_pedidos:
                nid = cola_pedidos.pop(0)
                for z in zapatos_temporales:
                    if z["id"] == nid:
                        z.update({"estado": "En reparacion", "inicio": reloj})
                        break
                rnd_reparacion, tiempo_reparacion = gen_uniforme(a2, b2)
                fin_reparacion = reloj + tiempo_reparacion
                estado_zapatero = "Reparando"
                registrar("Inicio_reparacion")
            else:
                estado_zapatero = "Libre"
                registrar("Fin_atencion")

        elif evento == "Fin_reparacion":
            fin_reparacion = math.inf
            estado_zapatero = "Libre"
            zapatos_reparados += 1
            cant_pares_reparados_real += 1
            acum_tiempo_reparacion += tiempo_reparacion
            term = [z for z in zapatos_temporales if z.get("estado") == "En reparacion"]
            if term:
                zapatos_temporales.remove(term[0])
            if cola_pedidos:
                nid = cola_pedidos.pop(0)
                for z in zapatos_temporales:
                    if z["id"] == nid:
                        z.update({"estado": "En reparacion", "inicio": reloj})
                        break
                rnd_reparacion, tiempo_reparacion = gen_uniforme(a2, b2)
                fin_reparacion = reloj + tiempo_reparacion
                estado_zapatero = "Reparando"
                registrar("Inicio_reparacion")
            else:
                rnd_reparacion, tiempo_reparacion = None, None
                registrar("Fin_reparacion")

        cant_max_cola = max(cant_max_cola, len(cola_pedidos))
        if prox_llegada == math.inf and fin_atencion == math.inf and fin_reparacion == math.inf:
            break

    df = pd.DataFrame(filas)
    stats = {
        "Promedio_tiempo_reparacion": acum_tiempo_reparacion / cant_pares_reparados_real if cant_pares_reparados_real else 0.0,
        "Maximo_promedio_reparacion": max_promedio,
        "Cantidad_maxima_cola": cant_max_cola,
    }
    return df, stats

# ---------------------------------------------------------------------
# 4) Ejecutar desde Streamlit con métricas bonitas
# ---------------------------------------------------------------------
if st.sidebar.button("Arrancar simulación"):
    df, stats = simular_dia(stock_inicial, mu, a1, b1, a2, b2, p_retiro, jornada)
    st.subheader("Vector de Estado")
    st.dataframe(df)

    st.subheader("Estadísticas")
    col1, col2, col3 = st.columns(3)
    col1.metric("Promedio reparación (min)", f"{stats['Promedio_tiempo_reparacion']:.2f}")
    col2.metric("Máximo prom. reparación (min)", f"{stats['Maximo_promedio_reparacion']:.2f}")
    col3.metric("Max clientes en cola", stats['Cantidad_maxima_cola'])
