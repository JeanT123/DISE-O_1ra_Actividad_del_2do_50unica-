from io import BytesIO

import pandas as pd
import plotly.express as px
import streamlit as st
from scipy.stats import f as distribucion_f

from utils.anova_utils import (
	ajustar_dca,
	cargar_datos,
	coeficiente_variacion,
	interpretar_dca,
	resumen_tratamientos,
	tabla_anova,
	tukey,
	validar_dca,
)


@st.cache_data(show_spinner=False)
def cargar_datos_cacheados(
	contenido_archivo: bytes | None, nombre_archivo: str | None
) -> pd.DataFrame:
	"""Carga desde la caché un archivo CSV/XLSX o el CSV de ejemplo.

	Args:
		contenido_archivo: Contenido binario del archivo cargado, o ``None``.
		nombre_archivo: Nombre con extensión del archivo cargado, o ``None``.

	Returns:
		Datos cargados mediante la función reutilizable del proyecto.
	"""
	# Si no se proporcionó contenido, se utiliza el conjunto de datos de los secadores solares.
	if contenido_archivo is None:
		return cargar_datos("data/dca_secadores.csv")

	# Se restaura el nombre para que el cargador identifique CSV o XLSX por su extensión.
	archivo = BytesIO(contenido_archivo)
	archivo.name = nombre_archivo or "datos.csv"
	return cargar_datos(archivo)


st.title("Diseño Completamente al Azar (DCA)")
st.write(
	"El DCA compara tratamientos asignados al azar cuando las unidades experimentales "
	"son relativamente homogéneas. En este ejemplo se compara la humedad final de "
	"granos secados con cuatro secadores solares (A, B, C y D), con cuatro réplicas por secador."
)

archivo_cargado = st.file_uploader(
	"Cargar datos del ensayo", type=["csv", "xlsx"], accept_multiple_files=False
)

if archivo_cargado is None:
	st.caption("No se cargó un archivo; se usan los datos de ejemplo data/dca_secadores.csv.")

try:
	if archivo_cargado is None:
		df = cargar_datos_cacheados(None, None)
	else:
		df = cargar_datos_cacheados(archivo_cargado.getvalue(), archivo_cargado.name)
except Exception as error:
	st.error(f"No fue posible cargar los datos: {error}")
	st.stop()

if df.empty or len(df.columns) == 0:
	st.error("El archivo no contiene datos ni columnas para analizar.")
	st.stop()

columnas = list(df.columns)
tratamiento_preferido = next(
	(columna for columna in columnas if str(columna).casefold() == "secador"),
	columnas[0],
)
indice_tratamiento = columnas.index(tratamiento_preferido)

columna_tratamiento = st.selectbox(
	"Columna de tratamiento", options=columnas, index=indice_tratamiento
)
opciones_respuesta = [columna for columna in columnas if columna != columna_tratamiento]
if not opciones_respuesta:
	st.error("El archivo debe tener columnas separadas para tratamiento y respuesta.")
	st.stop()

opciones_numericas = [
	columna
	for columna in opciones_respuesta
	if pd.api.types.is_numeric_dtype(df[columna])
]
respuesta_preferida = next(
	(columna for columna in opciones_respuesta if str(columna).casefold() == "humedad"),
	opciones_numericas[0] if opciones_numericas else opciones_respuesta[0],
)
columna_respuesta = st.selectbox(
	"Columna de respuesta", options=opciones_respuesta,
	index=opciones_respuesta.index(respuesta_preferida),
)
alfa = st.slider(
	"Nivel de significancia (alfa)",
	min_value=0.01,
	max_value=0.10,
	value=0.05,
	step=0.01,
	format="%.2f",
)

errores = validar_dca(df, columna_tratamiento, columna_respuesta)
for error in errores:
	st.error(error)
if errores:
	st.stop()

modelo = ajustar_dca(df, columna_tratamiento, columna_respuesta)
tabla = tabla_anova(modelo)
resumen = resumen_tratamientos(df, columna_tratamiento, columna_respuesta)
cv = coeficiente_variacion(modelo, df, columna_respuesta)
fila_tratamientos = tabla.loc[tabla["Fuente"] == "Tratamientos"].iloc[0]
fila_error = tabla.loc[tabla["Fuente"] == "Error"].iloc[0]
p_valor = float(fila_tratamientos["p-valor"])
# F crítica es el cuantil 1 - alfa de la distribución F con gl de tratamientos y de error.
f_critica = float(
	distribucion_f.ppf(1 - alfa, fila_tratamientos["gl"], fila_error["gl"])
)
interpretacion = interpretar_dca(tabla, alfa)

pestana_datos, pestana_anova, pestana_comparaciones, pestana_graficos = st.tabs(
	["Datos", "ANOVA", "Comparaciones", "Gráficos"]
)

with pestana_datos:
	st.subheader("Datos del ensayo")
	st.dataframe(df, width="stretch", hide_index=True)
	st.subheader("Resumen por tratamiento")
	st.dataframe(resumen, width="stretch", hide_index=True)

with pestana_anova:
	st.subheader("Análisis de varianza")
	st.dataframe(tabla.round(4), width="stretch", hide_index=True)
	columna_f, columna_cv = st.columns(2)
	columna_f.metric("F crítica", f"{f_critica:.4f}")
	columna_cv.metric("Coeficiente de variación", f"{cv:.4f}%")
	st.caption(
		f"F calculada = {float(fila_tratamientos['F']):.4f}; "
		f"gl de tratamientos = {fila_tratamientos['gl']:.0f}; "
		f"gl del error = {fila_error['gl']:.0f}."
	)
	if p_valor <= alfa:
		st.success(interpretacion)
	else:
		st.info(interpretacion)

with pestana_comparaciones:
	st.subheader("Comparaciones múltiples de Tukey")
	if p_valor < alfa:
		tabla_tukey, dms = tukey(
			df, columna_tratamiento, columna_respuesta, alfa=alfa
		)
		st.dataframe(tabla_tukey.round(4), width="stretch", hide_index=True)
		st.metric("Diferencia mínima significativa (DMS)", f"{dms:.4f}")
	else:
		st.info(
			f"No se realiza Tukey porque el ANOVA no detectó diferencias globales "
			f"al nivel alfa = {alfa:.2f} (p-valor = {p_valor:.4f})."
		)

with pestana_graficos:
	st.subheader("Distribución de la respuesta")
	figura_cajas = px.box(
		df,
		x=columna_tratamiento,
		y=columna_respuesta,
		color=columna_tratamiento,
		points="all",
		labels={
			columna_tratamiento: "Tratamiento",
			columna_respuesta: "Respuesta",
		},
	)
	figura_cajas.update_layout(showlegend=False)

	st.subheader("Media por tratamiento")
	figura_medias = px.bar(
		resumen,
		x=columna_tratamiento,
		y="media",
		error_y="desviación estándar",
		color=columna_tratamiento,
		labels={
			columna_tratamiento: "Tratamiento",
			"media": "Media de la respuesta",
			"desviación estándar": "Desviación estándar",
		},
	)
	figura_medias.update_layout(showlegend=False)

	columna_cajas, columna_medias = st.columns(2)
	columna_cajas.plotly_chart(figura_cajas, width="stretch")
	columna_medias.plotly_chart(figura_medias, width="stretch")