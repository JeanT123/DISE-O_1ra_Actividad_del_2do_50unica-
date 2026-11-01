# Instrucciones del repositorio

## Proyecto

Aplicación de Diseño Experimental desarrollada en Python y Streamlit para el curso de Diseño Experimental del programa de Ingeniería Agrícola de la Universidad de Sucre.

## Estructura

- `app.py`: portada de la aplicación.
- `pages/`: una página por cada diseño experimental.
- `utils/`: funciones reutilizables; incluir `__init__.py`.
- `data/`: archivos CSV de ejemplo.
- `verificacion/`: scripts de R para verificar los análisis.

Respeta esta organización al agregar funcionalidades y evita concentrar lógica reutilizable en las páginas.

## Idioma y documentación

- Escribe en español todo el código, los comentarios, los docstrings y los mensajes de la interfaz.
- Añade un comentario en cada paso estadístico que explique qué se calcula y por qué, con una explicación apropiada para estudiantes de Ingeniería Agrícola.
- Declara type hints en las funciones y documenta cada función con docstrings en español, siguiendo el estilo Google.

## Dependencias y análisis estadístico

- Usa únicamente estas librerías: `streamlit`, `pandas`, `numpy`, `scipy`, `statsmodels`, `plotly` y `openpyxl`. Pide permiso antes de agregar cualquier otra dependencia.
- Ajusta los modelos de ANOVA con `statsmodels.formula.api.ols` y calcula la tabla con `statsmodels.stats.anova.anova_lm`, usando `typ=2`.
- Realiza las comparaciones de Tukey con `statsmodels.stats.multicomp.pairwise_tukeyhsd`.
- No inventes ni codifiques resultados estadísticos de ejemplo como si fueran resultados del análisis: todos los números presentados deben provenir del cálculo realizado con los datos.

## Verificación

Antes de terminar una tarea, ejecuta el código pertinente y corrige los errores que aparezcan. Si la tarea no incluye código ejecutable o no es posible ejecutarlo en el entorno disponible, indícalo claramente y verifica lo que sí corresponda.
