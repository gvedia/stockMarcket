import hashlib
import io
from pathlib import Path

import pandas as pd
import streamlit as st

from stock_market_prototipo import (
    cargar_datos,
    ingresar_mercaderia,
    limpiar_datos,
    predecir_demanda,
    registrar_venta,
    resumen_ventas,
    riesgo_faltante,
)


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_CSV = BASE_DIR / "dataset_stock_market_academico.csv"
REQUIRED_COLUMNS = {
    "fecha",
    "producto",
    "precio",
    "stock_inicial",
    "ingreso_mercaderia",
    "unidades_vendidas",
    "stock_final",
}

st.set_page_config(
    page_title="Mercado | Inventario",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
    :root {
        --ink: #17352b;
        --muted: #62736b;
        --paper: #f3f5ef;
        --panel: #ffffff;
        --green: #164b3b;
        --lime: #d5e75b;
        --coral: #dc674f;
        --line: #dfe5dc;
    }
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    .stApp { background: var(--paper); color: var(--ink); }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stSidebar"] { background: #17352b; }
    [data-testid="stSidebar"] * { color: #f5f7f0; }
    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
        background: #23483c; border: 1px dashed #91a99c;
    }
    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button {
        color: var(--ink) !important;
    }
    h1, h2, h3 { font-family: 'Manrope', sans-serif; color: var(--ink); }
    h1 { font-weight: 800; letter-spacing: 0; }
    [data-testid="stMetric"] {
        background: var(--panel); border: 1px solid var(--line);
        border-top: 3px solid var(--lime); border-radius: 5px;
        padding: 16px 18px;
    }
    [data-testid="stMetricLabel"] { color: var(--muted); }
    [data-testid="stMetricValue"] { color: var(--ink); font-family: 'Manrope', sans-serif; }
    [data-testid="stTabs"] button[aria-selected="true"] {
        color: var(--green); border-bottom-color: var(--coral);
    }
    .eyebrow { color: var(--coral); font-size: 0.75rem; font-weight: 700;
        letter-spacing: 0.08em; text-transform: uppercase; }
    .note { color: var(--muted); font-size: 0.85rem; }
    div.stButton > button {
        color: #ffffff; background: var(--green); border-color: var(--green);
        border-radius: 4px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def load_dataset(contents):
    frame = cargar_datos(io.BytesIO(contents))
    missing_columns = REQUIRED_COLUMNS.difference(frame.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Al CSV le faltan estas columnas: {missing}")

    frame = limpiar_datos(frame)
    frame = frame.dropna(subset=["fecha", "producto"])
    frame["producto"] = frame["producto"].astype(str)
    frame["stock_final"] = frame["stock_final"].fillna(0)
    if frame.empty:
        raise ValueError("El CSV no contiene filas con fecha y producto validos.")
    return frame.sort_values(["producto", "fecha"])


st.sidebar.markdown("## MERCADO / CONTROL")
st.sidebar.caption("Panel de ventas e inventario")
uploaded_file = st.sidebar.file_uploader("Usar otro archivo CSV", type=["csv"])

if uploaded_file is not None:
    csv_contents = uploaded_file.getvalue()
    source_label = uploaded_file.name
elif DEFAULT_CSV.exists():
    csv_contents = DEFAULT_CSV.read_bytes()
    source_label = DEFAULT_CSV.name
else:
    st.sidebar.warning("No se encontro el CSV de ejemplo.")
    st.stop()

try:
    data = load_dataset(csv_contents)
except Exception as error:
    st.error(f"No se pudo leer el archivo: {error}")
    st.stop()

products = sorted(data["producto"].unique())
latest_records = data.groupby("producto", sort=False).tail(1)
starting_stock = {
    row["producto"]: max(0, int(round(row["stock_final"])))
    for _, row in latest_records.iterrows()
}
data_id = hashlib.sha256(csv_contents).hexdigest()
if st.session_state.get("data_id") != data_id:
    st.session_state.data_id = data_id
    st.session_state.stock_by_product = starting_stock.copy()

if st.sidebar.button("Reiniciar stock de prueba", width="stretch"):
    st.session_state.stock_by_product = starting_stock.copy()
    st.session_state.flash_message = ("success", "Stock de prueba reiniciado desde el CSV.")
    st.rerun()

st.markdown('<div class="eyebrow">OPERACIONES / DATOS DE INVENTARIO</div>', unsafe_allow_html=True)
st.title("Mercado diario")
first_date = data["fecha"].min().strftime("%d/%m/%Y")
last_date = data["fecha"].max().strftime("%d/%m/%Y")
st.caption(f"Fuente: {source_label}  ·  Periodo: {first_date} - {last_date}")

flash_message = st.session_state.pop("flash_message", None)
if flash_message:
    message_type, message_text = flash_message
    getattr(st, message_type)(message_text)

inventory_rows = []
for product in products:
    current_stock = st.session_state.stock_by_product[product]
    demand = predecir_demanda(data, product)
    inventory_rows.append(
        {
            "Producto": product,
            "Stock actual": current_stock,
            "Demanda diaria": demand,
            "Estado": "Reponer" if riesgo_faltante(current_stock, demand) else "En nivel",
        }
    )
inventory = pd.DataFrame(inventory_rows)

metric_top = st.columns(2)
metric_bottom = st.columns(2)
metric_top[0].metric("Productos", len(products))
metric_top[1].metric("Unidades disponibles", f"{inventory['Stock actual'].sum():,}")
metric_bottom[0].metric("Demanda diaria estimada", f"{inventory['Demanda diaria'].sum():.1f}")
metric_bottom[1].metric("Necesitan reposicion", int((inventory["Estado"] == "Reponer").sum()))

summary_tab, product_tab, data_tab = st.tabs(["Resumen", "Producto y movimientos", "Datos"])

with summary_tab:
    summary_column, alerts_column = st.columns([1.6, 1])
    with summary_column:
        st.subheader("Inventario por producto")
        st.dataframe(
            inventory,
            hide_index=True,
            width="stretch",
            column_config={
                "Stock actual": st.column_config.NumberColumn(format="%d u"),
                "Demanda diaria": st.column_config.NumberColumn(format="%.2f u/dia"),
            },
        )
        sales_summary = resumen_ventas(data).reset_index()
        st.subheader("Rendimiento de ventas")
        st.dataframe(sales_summary, hide_index=True, width="stretch")

    with alerts_column:
        st.subheader("Alertas de reposicion")
        at_risk = inventory[inventory["Estado"] == "Reponer"]
        if at_risk.empty:
            st.success("Todos los productos tienen stock por encima de la demanda diaria.")
        else:
            for _, row in at_risk.iterrows():
                st.error(
                    f"{row['Producto']}: quedan {row['Stock actual']} unidades "
                    f"y la demanda estimada es {row['Demanda diaria']:.2f} por dia."
                )
        st.markdown(
            '<p class="note">La alerta compara el stock disponible con el promedio de ventas de los ultimos siete dias.</p>',
            unsafe_allow_html=True,
        )

with product_tab:
    selected_product = st.selectbox("Producto", products)
    product_data = data[data["producto"] == selected_product].sort_values("fecha")
    current_stock = st.session_state.stock_by_product[selected_product]
    demand = predecir_demanda(data, selected_product)

    chart_column, stock_column = st.columns(2)
    with chart_column:
        st.subheader("Unidades vendidas por dia")
        st.bar_chart(
            product_data,
            x="fecha",
            y="unidades_vendidas",
            x_label=None,
            y_label="Unidades",
            width="stretch",
        )
    with stock_column:
        st.subheader("Stock registrado")
        st.line_chart(
            product_data,
            x="fecha",
            y="stock_final",
            x_label=None,
            y_label="Unidades",
            width="stretch",
        )

    st.divider()
    st.subheader("Simular movimiento")
    st.caption(
        f"Stock actual: {current_stock} unidades  ·  Demanda diaria estimada: {demand:.2f} unidades"
    )
    sale_column, incoming_column = st.columns(2)
    with sale_column:
        with st.form("sale_form"):
            sale_quantity = st.number_input("Unidades vendidas", min_value=1, step=1, key="sale_quantity")
            sale_submitted = st.form_submit_button("Registrar venta", type="primary", width="stretch")
        if sale_submitted:
            try:
                new_stock = registrar_venta(current_stock, int(sale_quantity))
                st.session_state.stock_by_product[selected_product] = new_stock
                st.session_state.flash_message = ("success", f"Venta registrada. Nuevo stock: {new_stock} unidades.")
            except ValueError as error:
                st.session_state.flash_message = ("error", str(error))
            st.rerun()

    with incoming_column:
        with st.form("incoming_form"):
            incoming_quantity = st.number_input("Unidades recibidas", min_value=1, step=1, key="incoming_quantity")
            incoming_submitted = st.form_submit_button("Ingresar mercaderia", width="stretch")
        if incoming_submitted:
            new_stock = ingresar_mercaderia(current_stock, int(incoming_quantity))
            st.session_state.stock_by_product[selected_product] = new_stock
            st.session_state.flash_message = ("success", f"Ingreso registrado. Nuevo stock: {new_stock} unidades.")
            st.rerun()

    st.caption("Los movimientos son una simulacion temporal y no modifican el archivo CSV.")

with data_tab:
    st.subheader("Registros cargados")
    st.dataframe(data, hide_index=True, width="stretch")
    st.caption(f"{len(data)} filas cargadas desde {source_label}.")
