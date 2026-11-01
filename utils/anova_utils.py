import json
import warnings
from itertools import combinations
from pathlib import Path
from typing import IO

import pandas as pd
from scipy.stats import studentized_range
from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from statsmodels.regression.linear_model import RegressionResultsWrapper


def cargar_datos(archivo: str | Path | IO[bytes]) -> pd.DataFrame:
    """Carga un archivo CSV o Excel en un DataFrame.

    Args:
        archivo: Ruta del archivo o flujo binario con nombre y extensión.

    Returns:
        Los datos leídos desde el archivo.

    Raises:
        ValueError: Si la extensión no corresponde a CSV o XLSX.
    """
    # Se obtiene la extensión desde la ruta o el nombre del archivo cargado.
    nombre_archivo = getattr(archivo, "name", archivo)
    extension = Path(str(nombre_archivo)).suffix.lower()

    # Excel se lee directamente; para CSV, el motor de Python detecta coma o punto y coma.
    if extension == ".xlsx":
        return pd.read_excel(archivo)
    if extension == ".csv":
        return pd.read_csv(archivo, sep=None, engine="python")

    raise ValueError("Formato no compatible. Cargue un archivo .csv o .xlsx.")


def validar_dca(df: pd.DataFrame, col_trat: str, col_resp: str) -> list[str]:
    """Valida los datos necesarios para un DCA de un factor.

    Args:
        df: Datos del experimento.
        col_trat: Nombre de la columna que identifica los tratamientos.
        col_resp: Nombre de la columna con la respuesta numérica.

    Returns:
        Mensajes en español para los errores encontrados; lista vacía si no hay errores.
    """
    errores: list[str] = []

    # Se comprueba que las variables del modelo estén disponibles antes de analizarlas.
    if col_trat not in df.columns:
        errores.append(f"No se encontró la columna de tratamientos '{col_trat}'.")
    if col_resp not in df.columns:
        errores.append(f"No se encontró la columna de respuesta '{col_resp}'.")
    if errores:
        return errores

    # La respuesta debe ser cuantitativa para calcular medias y ajustar el ANOVA.
    if not pd.api.types.is_numeric_dtype(df[col_resp]):
        errores.append(f"La columna de respuesta '{col_resp}' debe ser numérica.")

    # Se buscan datos faltantes en las dos variables que intervienen en el análisis.
    if df[[col_trat, col_resp]].isna().any().any():
        errores.append("Hay datos faltantes en las columnas de tratamiento o respuesta.")

    # Se calcula k = número de niveles únicos del factor para exigir al menos dos tratamientos.
    cantidad_tratamientos = df[col_trat].nunique(dropna=True)
    if cantidad_tratamientos < 2:
        errores.append("El DCA requiere al menos dos tratamientos.")

    # Se calcula n_i = número de observaciones del tratamiento i para exigir al menos dos réplicas.
    replicas = df.groupby(col_trat, dropna=True).size()
    tratamientos_insuficientes = replicas[replicas < 2].index.tolist()
    if tratamientos_insuficientes:
        errores.append(
            "Cada tratamiento debe tener al menos dos réplicas. "
            f"Tratamientos con menos de dos: {tratamientos_insuficientes}."
        )

    return errores


def ajustar_dca(
    df: pd.DataFrame, col_trat: str, col_resp: str
) -> RegressionResultsWrapper:
    """Ajusta un modelo lineal para un DCA de un factor.

    Args:
        df: Datos del experimento.
        col_trat: Nombre de la columna que identifica los tratamientos.
        col_resp: Nombre de la columna con la respuesta numérica.

    Returns:
        El modelo lineal ajustado.

    Raises:
        ValueError: Si los datos no cumplen las condiciones básicas del DCA.
    """
    # Se detiene el ajuste si los datos no cumplen las condiciones para comparar tratamientos.
    errores = validar_dca(df, col_trat, col_resp)
    if errores:
        raise ValueError("No se puede ajustar el DCA: " + " ".join(errores))

    # Q() protege nombres con espacios, tildes o palabras reservadas en la fórmula del modelo.
    respuesta_q = f"Q({json.dumps(col_resp, ensure_ascii=False)})"
    tratamiento_q = f"Q({json.dumps(col_trat, ensure_ascii=False)})"
    formula = f"{respuesta_q} ~ C({tratamiento_q})"

    # El modelo del DCA es Y_ij = mu + tau_i + error_ij, donde tau_i es el efecto del tratamiento.
    return ols(formula, data=df).fit()


def tabla_anova(modelo: RegressionResultsWrapper) -> pd.DataFrame:
    """Construye una tabla ANOVA tipo II en español e incluye el total.

    Args:
        modelo: Modelo lineal ajustado para el DCA.

    Returns:
        Tabla con fuente, grados de libertad, sumas y cuadrados medios, F y p-valor.
    """
    # El ANOVA tipo II separa la variación atribuible al tratamiento y al error experimental.
    tabla_base = anova_lm(modelo, typ=2)
    fila_tratamientos = tabla_base.loc[tabla_base.index != "Residual"].iloc[0]
    fila_error = tabla_base.loc["Residual"]

    # Las sumas de cuadrados y grados de libertad totales son la suma de tratamientos y error.
    sc_tratamientos = float(fila_tratamientos["sum_sq"])
    gl_tratamientos = float(fila_tratamientos["df"])
    sc_error = float(fila_error["sum_sq"])
    gl_error = float(fila_error["df"])
    sc_total = sc_tratamientos + sc_error
    gl_total = gl_tratamientos + gl_error

    # El cuadrado medio se calcula como CM = SC / gl para cada fuente, incluido el total.
    cm_tratamientos = sc_tratamientos / gl_tratamientos
    cm_error = sc_error / gl_error
    cm_total = sc_total / gl_total

    # El estadístico de prueba es F = CM_tratamientos / CM_error; el ANOVA aporta su p-valor.
    return pd.DataFrame(
        [
            {
                "Fuente": "Tratamientos",
                "gl": gl_tratamientos,
                "SC": sc_tratamientos,
                "CM": cm_tratamientos,
                "F": float(fila_tratamientos["F"]),
                "p-valor": float(fila_tratamientos["PR(>F)"]),
            },
            {
                "Fuente": "Error",
                "gl": gl_error,
                "SC": sc_error,
                "CM": cm_error,
                "F": float("nan"),
                "p-valor": float("nan"),
            },
            {
                "Fuente": "Total",
                "gl": gl_total,
                "SC": sc_total,
                "CM": cm_total,
                "F": float("nan"),
                "p-valor": float("nan"),
            },
        ],
        columns=["Fuente", "gl", "SC", "CM", "F", "p-valor"],
    )


def resumen_tratamientos(
    df: pd.DataFrame, col_trat: str, col_resp: str
) -> pd.DataFrame:
    """Resume el número de réplicas y la respuesta por tratamiento.

    Args:
        df: Datos del experimento.
        col_trat: Nombre de la columna que identifica los tratamientos.
        col_resp: Nombre de la columna con la respuesta numérica.

    Returns:
        DataFrame con el número de observaciones, total, media y desviación estándar.
    """
    # Por tratamiento, n cuenta observaciones; total = suma(Y), media = total / n.
    resumen = df.groupby(col_trat, as_index=False, sort=False).agg(
        n=(col_resp, "count"),
        total=(col_resp, "sum"),
        media=(col_resp, "mean"),
        desviacion_estandar=(col_resp, "std"),
    )

    # La desviación estándar muestral es s = sqrt(sum((Y - media)^2) / (n - 1)).
    return resumen.rename(columns={"desviacion_estandar": "desviación estándar"})


def coeficiente_variacion(
    modelo: RegressionResultsWrapper, df: pd.DataFrame, col_resp: str
) -> float:
    """Calcula el coeficiente de variación del experimento.

    Args:
        modelo: Modelo lineal ajustado para el DCA.
        df: Datos del experimento.
        col_resp: Nombre de la columna con la respuesta numérica.

    Returns:
        Coeficiente de variación expresado como porcentaje.

    Raises:
        ValueError: Si la media general es cero.
    """
    # El CME proviene del error residual del modelo y la media general resume la respuesta observada.
    cme = float(modelo.mse_resid)
    media_general = float(df[col_resp].mean())
    if media_general == 0:
        raise ValueError("No se puede calcular el CV porque la media general es cero.")

    # La fórmula solicitada es CV = sqrt(CME) / media_general * 100.
    return float((cme**0.5 / media_general) * 100)


def tukey(
    df: pd.DataFrame,
    col_trat: str,
    col_resp: str,
    alfa: float = 0.05,
) -> tuple[pd.DataFrame, float]:
    """Compara tratamientos con Tukey y calcula una DMS para el diseño.

    Args:
        df: Datos del experimento.
        col_trat: Nombre de la columna que identifica los tratamientos.
        col_resp: Nombre de la columna con la respuesta numérica.
        alfa: Nivel de significancia entre cero y uno.

    Returns:
        Una tabla de comparaciones de Tukey en español y la DMS.

    Raises:
        ValueError: Si alfa o los datos no son válidos para el DCA.
    """
    # Se valida alfa y la estructura del ensayo antes de realizar comparaciones múltiples.
    if not 0 < alfa < 1:
        raise ValueError("alfa debe estar entre cero y uno.")
    errores = validar_dca(df, col_trat, col_resp)
    if errores:
        raise ValueError("No se puede realizar Tukey: " + " ".join(errores))

    # Tukey compara cada par de medias y ajusta la inferencia por comparaciones múltiples.
    resultado = pairwise_tukeyhsd(
        endog=df[col_resp], groups=df[col_trat], alpha=alfa
    )
    pares = list(combinations(resultado.groupsunique, 2))
    tabla_tukey = pd.DataFrame(
        {
            "Tratamiento 1": [par[0] for par in pares],
            "Tratamiento 2": [par[1] for par in pares],
            "Diferencia de medias": resultado.meandiffs,
            "p-valor ajustado": resultado.pvalues,
            "Límite inferior": resultado.confint[:, 0],
            "Límite superior": resultado.confint[:, 1],
            "Rechaza H0": resultado.reject,
        }
    )

    # El ANOVA del mismo modelo proporciona CME y glE; q usa el cuantil 1 - alfa.
    tabla_base = anova_lm(ajustar_dca(df, col_trat, col_resp), typ=2)
    cme = float(tabla_base.loc["Residual", "sum_sq"] / tabla_base.loc["Residual", "df"])
    gl_error = float(tabla_base.loc["Residual", "df"])
    cantidad_tratamientos = len(resultado.groupsunique)
    q_critico = float(
        studentized_range.ppf(1 - alfa, cantidad_tratamientos, gl_error)
    )

    # En datos balanceados r es el número común de réplicas; si no, se aproxima con la media armónica.
    replicas = df.groupby(col_trat, sort=False).size().astype(float)
    balanceado = replicas.nunique() == 1
    if balanceado:
        r = float(replicas.iloc[0])
    else:
        r = float(len(replicas) / (1 / replicas).sum())
        warnings.warn(
            "El diseño no está balanceado; la DMS calculada con la media armónica "
            "de réplicas es aproximada.",
            RuntimeWarning,
            stacklevel=2,
        )

    # La diferencia mínima significativa aproximada es DMS = q * sqrt(CME / r).
    dms = q_critico * (cme / r) ** 0.5
    return tabla_tukey, float(dms)


def interpretar_dca(tabla: pd.DataFrame, alfa: float = 0.05) -> str:
    """Interpreta la prueba global de tratamientos del ANOVA.

    Args:
        tabla: Tabla generada por ``tabla_anova``.
        alfa: Nivel de significancia entre cero y uno.

    Returns:
        Interpretación sencilla de la decisión sobre la hipótesis nula.

    Raises:
        ValueError: Si alfa es inválido o la tabla no contiene el resultado de tratamientos.
    """
    # Se verifica el nivel de significancia y se localiza el p-valor de tratamientos.
    if not 0 < alfa < 1:
        raise ValueError("alfa debe estar entre cero y uno.")
    fila_tratamientos = tabla.loc[tabla["Fuente"] == "Tratamientos"]
    if fila_tratamientos.empty:
        raise ValueError("La tabla debe incluir una fila 'Tratamientos'.")
    p_valor = float(fila_tratamientos.iloc[0]["p-valor"])

    # La regla de decisión compara p con alfa: rechazar H0 indica que no todas las medias son iguales.
    if p_valor <= alfa:
        return (
            f"Se rechaza H0 al nivel de significancia {alfa:.3f}: hay evidencia de "
            "diferencias entre las medias de los tratamientos. Para decidir cuál "
            "tratamiento conviene, revise las comparaciones múltiples y el contexto agrícola."
        )
    return (
        f"No se rechaza H0 al nivel de significancia {alfa:.3f}: no hay evidencia "
        "suficiente de diferencias entre las medias de los tratamientos. No se "
        "concluye que sean iguales; considere la precisión del ensayo y sus objetivos."
    )