import streamlit as st

AUTOR = "Escribe aquí tu nombre"

st.set_page_config(
    page_title="App de Diseño Experimental",
    page_icon="🌱",
    layout="wide",
)

st.title("Diseño Experimental en Ingeniería Agrícola")
st.subheader("Ingeniería Agrícola – Universidad de Sucre")
st.write(
    "El diseño experimental permite planear ensayos de campo para comparar "
    "tratamientos de manera ordenada, controlar fuentes de variación y obtener "
    "evidencia útil para tomar decisiones sobre cultivos y prácticas agrícolas."
)

st.header("Módulos")
st.table(
    [
        {
            "Módulo": "DCA – Diseño Completamente al Azar",
            "Cuándo se usa": "Cuando las unidades experimentales son homogéneas y los tratamientos se asignan al azar.",
            "Ejemplo agrícola": "Comparar dosis de fertilizante en parcelas uniformes de maíz.",
            "Estado": "Disponible",
        },
        {
            "Módulo": "DBCA – Diseño en Bloques Completos al Azar",
            "Cuándo se usa": "Cuando se puede agrupar las unidades en bloques para controlar una fuente de variación.",
            "Ejemplo agrícola": "Comparar variedades de arroz agrupando parcelas por gradiente de fertilidad.",
            "Estado": "En construcción",
        },
        {
            "Módulo": "DCL – Diseño en Cuadrado Latino",
            "Cuándo se usa": "Cuando se requiere controlar dos fuentes de variación mediante filas y columnas.",
            "Ejemplo agrícola": "Evaluar tratamientos de riego controlando filas y columnas de un lote.",
            "Estado": "En construcción",
        },
        {
            "Módulo": "DPD – Diseño de Parcelas Divididas",
            "Cuándo se usa": "Cuando dos factores se aplican con distinta facilidad o escala experimental.",
            "Ejemplo agrícola": "Evaluar labranza en parcelas grandes y variedades en subparcelas.",
            "Estado": "En construcción",
        },
        {
            "Módulo": "Diseños Factoriales",
            "Cuándo se usa": "Cuando se estudian simultáneamente varios factores y sus interacciones.",
            "Ejemplo agrícola": "Evaluar combinaciones de niveles de riego y fertilización en fríjol.",
            "Estado": "En construcción",
        },
        {
            "Módulo": "Metodología de Superficie de Respuesta (RSM)",
            "Cuándo se usa": "Cuando se busca modelar y optimizar una respuesta según niveles de varios factores.",
            "Ejemplo agrícola": "Optimizar dosis de nitrógeno y densidad de siembra para el rendimiento.",
            "Estado": "En construcción",
        },
    ]
)

st.header("Instrucciones de uso")
st.markdown(
    """
1. Elige un módulo en el menú lateral.
2. Carga los datos del ensayo cuando el módulo esté disponible.
3. Revisa los resultados y su interpretación.
4. Verifica los supuestos y compara los resultados con tu cálculo manual.
"""
)

st.warning(
    "Esta app apoya el aprendizaje. El estudiante interpreta los resultados, "
    "verifica supuestos y compara con su cálculo manual."
)

with st.sidebar:
    st.header("Información del curso")
    st.write(f"Autor: {AUTOR}")
    st.write("Curso: Diseño Experimental")
    st.write("Semestre: 2026-2")