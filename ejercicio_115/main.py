import streamlit as st
import pandas as pd
import random
import math
from itertools import count

"""
Ejercicio 115 – Final de Simulación
Simulador discreto – Casa de Reparaciones de Zapatos
---------------------------------------------------
Vector de Estado solicitado (columnas):
  Nro_evento, Evento, Reloj,
  RND_llegada, Tiempo_entre_llegadas, Proxima_llegada,
  RND_peticion, Tipo_peticion,
  RND_atencion, Tiempo_atencion, Fin_atencion,
  RND_reparacion, Tiempo_reparacion, Fin_reparacion,
  Estado_zapatero,
  Acum_tiempo_reparacion, Cant_zapatos_reparados,
  Promedio_rep, Max_promedio_rep,
  Cant_max_cola,
  Zapatos_temporales (lista de pares {id, estado, inicio})
"""

# ---------------------------------------------------------------------
# 1) Interface Streamlit – parámetros de entrada (NO se han alterado)
# ---------------------------------------------------------------------
st.title("Ejercicio 115 – Final de Simulación")

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
    """Devuelve (rnd, valor) con distribución Exponencial(media)."""
    rnd = random.random()
    valor = -media * math.log(1 - rnd)
    return rnd, valor


def gen_uniforme(a: float, b: float) -> tuple[float, float]:
    """Devuelve (rnd, valor) con distribución U(a, b)."""
    rnd = random.random()
    valor = a + rnd * (b - a)
    return rnd, valor

# ---------------------------------------------------------------------
# 3) Simulación de un día
# ---------------------------------------------------------------------

def simular_dia(stock_inicial: int, mu: float, a1: float, b1: float,
                a2: float, b2: float, p_retiro: float, jornada: int):
    # ------------------------- variables de estado -------------------------
    reloj: float = 0.0
    nro_evento  = 0

    # Eventos programados (∞ = no programado)
    rnd_llegada, tiempo_entre = gen_exponencial(mu)
    prox_llegada   = reloj + tiempo_entre

    rnd_atencion   = None
    tiempo_atencion = None
    fin_atencion   = math.inf

    rnd_reparacion = None
    tiempo_reparacion = None
    fin_reparacion = math.inf
    reparacion_restante = None  # para interrupciones

    # Colas y recursos
    estado_zapatero = "Libre"  # Libre | Atendiendo | Reparando
    cola_pedidos: list[int] = []  # IDs de pares en espera de reparar
    id_generator = count(start=1)  # IDs incrementales para pares nuevos

    # Zapatos reparados listos para retiro (stock)
    zapatos_reparados = stock_inicial

    # Zapatos temporales en reparación o cola -> lista de dicts
    zapatos_temporales: list[dict] = []

    # ------------------------ variables estadísticas -----------------------
    acum_tiempo_reparacion: float = 0.0
    cant_pares_reparados_real: int = 0  # sin contar stock inicial
    max_promedio: float = 0.0
    cant_max_cola: int = 0

    # --------------------- helper para registrar vector --------------------
    filas: list[dict] = []

    def registrar(evento: str):
        nonlocal nro_evento, max_promedio
        promedio = (acum_tiempo_reparacion / cant_pares_reparados_real) if cant_pares_reparados_real else 0.0
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

    # Registrar fila 0 –  estado inicial
    rnd_peticion = None
    tipo_peticion = None
    registrar("Inicial")

    # ---------------------------- bucle principal ---------------------------
    while True:
        # ¿Cuál es el próximo evento?
        evento = None
        proximo = math.inf
        if prox_llegada < proximo:
            evento, proximo = "Llegada", prox_llegada
        if fin_atencion < proximo:
            evento, proximo = "Fin_atencion", fin_atencion
        if fin_reparacion < proximo:
            evento, proximo = "Fin_reparacion", fin_reparacion

        # Corte: no quedan eventos y no habrá más llegadas
        if evento is None:
            break

        # Avanzar reloj
        reloj = proximo

        # ---------------------- procesar tipo de evento ----------------------
        if evento == "Llegada":
            # Generar datos de la llegada
            rnd_peticion = random.random()
            tipo_peticion = "Retiro" if rnd_peticion < p_retiro else "Pedido"

            # Programar siguiente llegada (solo si aún dentro de jornada)
            if reloj < jornada:
                rnd_llegada, tiempo_entre = gen_exponencial(mu)
                prox_llegada = reloj + tiempo_entre
            else:
                rnd_llegada = None
                tiempo_entre = None
                prox_llegada = math.inf

            # Si zapatero estaba reparando, interrumpe
            if estado_zapatero == "Reparando":
                reparacion_restante = fin_reparacion - reloj
                fin_reparacion = math.inf
                rnd_reparacion = None  # cuando retome se genera nuevo rnd (solo a efectos de vector)

            # Atender al cliente (si hay lugar)
            rnd_atencion, tiempo_atencion = gen_uniforme(a1, b1)
            fin_atencion = reloj + tiempo_atencion
            estado_zapatero = "Atendiendo"

            registrar("Llegada")

        elif evento == "Fin_atencion":
            # Terminó de atender cliente
            fin_atencion = math.inf

            if tipo_peticion == "Retiro":
                if zapatos_reparados > 0:
                    zapatos_reparados -= 1  # entrega par
                # Si no había stock, **nada** (cliente ya se fue sin atender al inicio)
            else:  # Pedido de reparación
                nuevo_id = next(id_generator)
                cola_pedidos.append(nuevo_id)
                zapatos_temporales.append({"id": nuevo_id, "estado": "En cola"})

            # Decide qué hacer ahora (reparar si puede)
            if reparacion_restante is not None:  # reanuda reparación interrumpida
                rnd_reparacion = random.random()  # para vector, no afecta tiempo
                tiempo_reparacion = reparacion_restante
                fin_reparacion = reloj + tiempo_reparacion
                reparacion_restante = None
                estado_zapatero = "Reparando"
                registrar("Inicio_reparacion")
            elif cola_pedidos:
                # Saca próximo de cola y arranca reparación nueva
                nuevo_id = cola_pedidos.pop(0)
                for z in zapatos_temporales:
                    if z["id"] == nuevo_id:
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
            # Reparación concluida
            fin_reparacion = math.inf
            estado_zapatero = "Libre"
            zapatos_reparados += 1
            cant_pares_reparados_real += 1
            acum_tiempo_reparacion += tiempo_reparacion

            # Marcar zapato terminado y quitar de temporales
            terminados = [z for z in zapatos_temporales if z["estado"] == "En reparacion" and (z["inicio"] is not None)]
            if terminados:
                zapat = terminados[0]
                zapatos_temporales.remove(zapat)

            # Si hay más en cola, arranca siguiente
            if cola_pedidos:
                nuevo_id = cola_pedidos.pop(0)
                for z in zapatos_temporales:
                    if z["id"] == nuevo_id:
                        z.update({"estado": "En reparacion", "inicio": reloj})
                        break
                rnd_reparacion, tiempo_reparacion = gen_uniforme(a2, b2)
                fin_reparacion = reloj + tiempo_reparacion
                estado_zapatero = "Reparando"
                registrar("Inicio_reparacion")
            else:
                rnd_reparacion = None
                tiempo_reparacion = None
                registrar("Fin_reparacion")

        # Actualizar máximos
        cant_max_cola = max(cant_max_cola, len(cola_pedidos))

        # Corte del ciclo al final del día
        if prox_llegada == math.inf and fin_atencion == math.inf and fin_reparacion == math.inf:
            break

    # ------------------------ DataFrame y estadísticas finales ------------
    df = pd.DataFrame(filas)
    stats = {
        "Promedio_tiempo_reparacion": acum_tiempo_reparacion / cant_pares_reparados_real if cant_pares_reparados_real else 0.0,
        "Maximo_promedio_reparacion": max_promedio,
        "Cantidad_maxima_cola": cant_max_cola,
    }
    return df, stats

# ---------------------------------------------------------------------
# 4) Ejecutar desde Streamlit
# ---------------------------------------------------------------------
if st.sidebar.button("Arrancar simulación"):
    df, stats = simular_dia(stock_inicial, mu, a1, b1, a2, b2, p_retiro, jornada)
    st.subheader("Vector de Estado")
    st.dataframe(df)

    st.subheader("Estadísticas")
    st.write(stats)
