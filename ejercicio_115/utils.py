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
def generar_nueva_fila_multiindex(estado: dict, usar_multi=True):
    """
    Aplana `estado`:
    • Si usar_multi=True, devuelve un dict cuyas claves son tuplas
      (Categoría, Campo) para poder armar un DataFrame MultiIndex.
    • Si usar_multi=False, devuelve el mismo dict (sin aplastar nada).
    """
    if not usar_multi:
        return estado

    fila = {}
    for clave, valor in estado.items():
        if isinstance(valor, dict):
            for subclave, subvalor in valor.items():
                fila[(clave, subclave)] = subvalor
        else:
            fila[("General", clave)] = valor
    return fila
