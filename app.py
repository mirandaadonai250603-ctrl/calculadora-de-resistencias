from collections import Counter
import itertools
import streamlit as st

# --- Configuración de la página ---
st.set_page_config(
    page_title="Optimizador de Redes de Resistencias", page_icon="⚡", layout="centered"
)


# --- Series comerciales estándar ---
SERIE_E12 = [1.0, 1.2, 1.5, 1.8, 2.2, 2.7, 3.3, 3.9, 4.7, 5.6, 6.8, 8.2]
SERIE_E24 = [
    1.0,
    1.1,
    1.2,
    1.3,
    1.5,
    1.6,
    1.8,
    2.0,
    2.2,
    2.4,
    2.7,
    3.0,
    3.3,
    3.6,
    3.9,
    4.3,
    4.7,
    5.1,
    5.6,
    6.2,
    6.8,
    7.5,
    8.2,
    9.1,
]


def construir_catalogo(base_serie, decadas=6):
  catalogo = []
  for d in range(decadas):
    for b in base_serie:
      catalogo.append(round(b * (10 ** d), 2))
  return sorted(list(set(catalogo)))


def seleccionar_serie_segun_tolerancia(tol):
  if tol >= 10:
    return construir_catalogo(SERIE_E12), "E12 (10%)"
  else:
    return construir_catalogo(SERIE_E24), "E24 (1%)"


def evaluar_topologias_mixtas(x, y, z):
  coleccion = {}
  for focal, p_a, p_b in [(x, y, z), (y, x, z), (z, x, y)]:
    denominador = p_a + p_b + focal
    if denominador > 0:
      val = (p_a + p_b) * focal / denominador
      coleccion[f"({p_a:g} + {p_b:g}) || {focal:g}"] = ("Serie-Paralelo", val)
    if p_a + p_b > 0:
      val = (p_a * p_b / (p_a + p_b)) + focal
      coleccion[f"({p_a:g} || {p_b:g}) + {focal:g}"] = ("Paralelo-Serie", val)
  return [(t, v, e) for e, (t, v) in coleccion.items()]


def buscar_combinaciones_optimas(meta, inventario, max_tol):
  hallazgos = []
  for cantidad in range(1, 4):
    for combinacion in itertools.combinations_with_replacement(
        inventario, cantidad
    ):
      if cantidad >= 1:
        v_eq = sum(combinacion)
        error = abs(v_eq - meta) / meta * 100
        if error <= max_tol:
          hallazgos.append({
              "modo": "Serie",
              "formula": " + ".join(f"{el:g}" for el in combinacion),
              "elementos": combinacion,
              "valor": round(v_eq, 2),
              "error": round(error, 3),
              "piezas": cantidad,
          })
      if cantidad > 1:
        suma_inversos = sum(1 / el for el in combinacion)
        if suma_inversos > 0:
          v_eq = 1 / suma_inversos
          error = abs(v_eq - meta) / meta * 100
          if error <= max_tol:
            hallazgos.append({
                "modo": "Paralelo",
                "formula": " || ".join(f"{el:g}" for el in combinacion),
                "elementos": combinacion,
                "valor": round(v_eq, 2),
                "error": round(error, 3),
                "piezas": cantidad,
            })
      if cantidad == 3:
        for modo, v_eq, formula in evaluar_topologias_mixtas(*combinacion):
          error = abs(v_eq - meta) / meta * 100
          if error <= max_tol:
            hallazgos.append({
                "modo": modo,
                "formula": formula,
                "elementos": combinacion,
                "valor": round(v_eq, 2),
                "error": round(error, 3),
                "piezas": cantidad,
            })

  registros_unicos = {}
  for h in hallazgos:
    llave = (h["formula"], h["valor"])
    if llave not in registros_unicos:
      registros_unicos[llave] = h

  lista_final = list(registros_unicos.values())
  lista_final.sort(key=lambda item: (item["error"], item["piezas"]))
  return lista_final[:3]


# --- Interfaz Gráfica con Streamlit ---
st.title("⚡ Calculadora Comercial de Resistencias")
st.write(
    "Encuentra la mejor combinación de hasta 3 resistencias comerciales"
    " (Series E12 y E24) mediante arreglos en serie, paralelo o mixtos."
)

with st.container():
  st.subheader("Parámetros de Búsqueda")
  meta = st.number_input(
      "Valor Deseado (Ohms):", min_value=0.1, value=1000.0, step=10.0
  )
  tol_sel = st.selectbox("Tolerancia:", ["1% (E24)", "10% (E12)"])

  btn_calcular = st.button(
      "Calcular Mejores Opciones", type="primary", use_container_width=True
  )

if btn_calcular:
  if meta <= 0:
    st.error("El valor de la resistencia debe ser mayor a cero.")
  else:
    tolerancia = 10.0 if "10" in tol_sel else 1.0
    inventario, etiqueta_serie = seleccionar_serie_segun_tolerancia(tolerancia)

    with st.spinner("Calculando combinaciones óptimas..."):
      top_tres = buscar_combinaciones_optimas(meta, inventario, tolerancia)

    if not top_tres:
      st.warning(
          f"No se encontraron combinaciones válidas dentro de la tolerancia del"
          f" {tolerancia}%. Intenta con un valor o tolerancia mayor."
      )
    else:
      st.success(
          f"Búsqueda exitosa en serie {etiqueta_serie} para {meta} Ohms:"
      )
      st.markdown("---")

      for idx, res in enumerate(top_tres, 1):
        col1, col2 = st.columns([2, 1])

        with col1:
          st.markdown(f"### Opción #{idx}: {res['modo']}")
          st.markdown(f"**Expresión:** `{res['formula']}`")
          st.markdown(f"**Valor Equivalente:** `{res['valor']:.2f} Ohms`")
          st.markdown(f"**Margen de Error:** `{res['error']:.3f} %`")

        with col2:
          st.markdown("**🛒 Lista de Compras:**")
          conteo_piezas = Counter(res["elementos"])
          for ohm, cantidad in sorted(conteo_piezas.items()):
            st.text(f"• {cantidad}x {ohm:g} Ohms")

        st.markdown("---")