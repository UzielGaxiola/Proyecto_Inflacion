
# Interfaz.py  —  Dashboard Interactivo: Inflación y Poder Adquisitivo en México

# Descripción:
#   Panel financiero de 4 secciones que visualiza el impacto de la inflación,
#   el tipo de cambio y el salario mínimo en México (2012–2025).
#
# Dependencias (instalar antes de correr):
#   pip install streamlit pandas sqlalchemy pymysql plotly numpy
#   pip install statsmodels          # solo para la línea de tendencia (OLS) en Dash 3
#
# Cómo correr:
#   streamlit run Interfaz.py
#
# IMPORTANTE: Antes de correr este archivo, ejecuta los 3 pasos del ETL:
#   1. python extraccion.py       → descarga datos de Banxico
#   2. python transformacion.py   → limpia y calcula métricas
#   3. python carga_sql.py        → inserta a MySQL


import sys
import warnings

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import create_engine, text

# Credenciales de la base de datos — editables en config.py
from config import (
    DB_HOST,
    DB_NAME,
    DB_PASSWORD,
    DB_PORT,
    DB_USER,
    TABLA_PRINCIPAL,
)

warnings.filterwarnings("ignore")


# 0. CONFIGURACIÓN GLOBAL DE LA PÁGINA  (debe ser lo primero que llame Streamlit)

st.set_page_config(
    page_title  = "Inflación México | Dashboard ETL",
    page_icon   = "📊",
    layout      = "wide",
    initial_sidebar_state = "expanded",
)


# 1. CSS PERSONALIZADO — DARK DASHBOARD

CSS_DARK = """
<style>
/* ── Google Fonts ─────────────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500;600&display=swap');

/* ── Fondo general ────────────────────────────────────────────────────────── */
.stApp {
    background-color: #070B12;
    font-family: 'DM Sans', sans-serif;
    color: #CBD5E1;
}

/* ── Sidebar ──────────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0A0F1A 0%, #0D1422 100%);
    border-right: 1px solid #162032;
}
[data-testid="stSidebar"] .stRadio label {
    padding: 11px 16px !important;
    border-radius: 9px !important;
    font-size: 0.87rem !important;
    font-weight: 500 !important;
    color: #64748B !important;
    transition: all 0.18s ease;
}
[data-testid="stSidebar"] .stRadio label:hover {
    background: #141E30 !important;
    color: #E2E8F0 !important;
}
[data-testid="stSidebar"] .stRadio [aria-checked="true"] + label,
[data-testid="stSidebar"] .stRadio input:checked + label {
    background: linear-gradient(90deg, #0B2240 0%, #102840 100%) !important;
    color: #38BDF8 !important;
    border: 1px solid #1E3A5F !important;
}

/* ── Tipografía de títulos ────────────────────────────────────────────────── */
h1, h2, h3, h4 {
    font-family: 'Syne', sans-serif !important;
    color: #F1F5F9 !important;
    letter-spacing: -0.01em;
}

/* ── Tarjetas de métricas (st.metric) ────────────────────────────────────── */
[data-testid="metric-container"] {
    background: linear-gradient(145deg, #0F1829 0%, #141E30 100%) !important;
    border: 1px solid #1E2D47 !important;
    border-radius: 14px !important;
    padding: 18px 20px !important;
    position: relative;
    overflow: hidden;
    transition: transform 0.2s, box-shadow 0.2s;
}
[data-testid="metric-container"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 24px rgba(14, 165, 233, 0.07) !important;
}
[data-testid="metric-container"] label {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.69rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.09em !important;
    text-transform: uppercase !important;
    color: #475569 !important;
}
[data-testid="stMetricValue"] {
    font-family: 'Syne', sans-serif !important;
    font-size: 1.75rem !important;
    font-weight: 800 !important;
    color: #F1F5F9 !important;
    line-height: 1.15 !important;
}
[data-testid="stMetricDelta"] svg { display: none; }
[data-testid="stMetricDelta"] > div {
    font-size: 0.78rem !important;
    font-weight: 500 !important;
}

/* ── Selectbox oscuro ─────────────────────────────────────────────────────── */
[data-testid="stSelectbox"] > div > div {
    background: #0F1829 !important;
    border: 1px solid #1E2D47 !important;
    border-radius: 10px !important;
    color: #CBD5E1 !important;
}

/* ── Plotly charts: borde y radio ─────────────────────────────────────────── */
[data-testid="stPlotlyChart"] > div {
    border: 1px solid #162032 !important;
    border-radius: 14px !important;
    overflow: hidden !important;
}

/* ── Info box educativa ───────────────────────────────────────────────────── */
.info-box {
    background: linear-gradient(135deg, #0A1828 0%, #0D1E38 100%);
    border: 1px solid #1A3354;
    border-left: 4px solid #0EA5E9;
    border-radius: 0 14px 14px 0;
    padding: 22px 28px;
    margin: 4px 0 8px;
}
.info-box h4 {
    font-family: 'Syne', sans-serif !important;
    color: #38BDF8 !important;
    font-size: 0.97rem !important;
    margin: 0 0 10px !important;
}
.info-box p {
    color: #94A3B8;
    font-size: 0.87rem;
    line-height: 1.78;
    margin: 0;
}

/* ── Separador decorativo ─────────────────────────────────────────────────── */
.hr-dark {
    height: 1px;
    background: linear-gradient(90deg, transparent 0%, #1E2D47 40%, #1E2D47 60%, transparent 100%);
    margin: 20px 0;
    border: none;
}

/* ── Card de intro ────────────────────────────────────────────────────────── */
.intro-card {
    background: linear-gradient(135deg, #0B1828 0%, #0F1E35 100%);
    border: 1px solid #1A3050;
    border-radius: 16px;
    padding: 24px 28px;
    height: 100%;
}
.intro-card h3 {
    color: #38BDF8 !important;
    font-size: 0.97rem !important;
    margin-bottom: 16px !important;
}
.intro-card-item {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    margin-bottom: 10px;
    font-size: 0.85rem;
    color: #94A3B8;
}
.intro-card-item strong {
    color: #E2E8F0;
}

/* ── Ocultar chrome de Streamlit ──────────────────────────────────────────── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 26px; padding-bottom: 30px; max-width: 1400px; }

/* ── Equipo badge ─────────────────────────────────────────────────────────── */
.team-badge {
    display: inline-block;
    background: #0F1829;
    border: 1px solid #1E2D47;
    border-radius: 10px;
    padding: 14px 22px;
    margin-top: 6px;
}
.team-badge .label {
    font-size: 0.67rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #334155;
    margin-bottom: 8px;
}
.team-badge .names {
    font-family: 'Syne', sans-serif;
    font-size: 0.88rem;
    color: #94A3B8;
}
</style>
"""
st.markdown(CSS_DARK, unsafe_allow_html=True)


# =============================================================================
# 2. CONEXIÓN A MySQL CON SQLAlchemy
# =============================================================================

@st.cache_resource(show_spinner=False)
def _engine():
    """
    Crea el engine de SQLAlchemy una sola vez y lo reutiliza en toda la sesión.
    cache_resource es el correcto aquí porque los engines de SQLAlchemy no
    son serializables (no van en cache_data).
    """
    cadena = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    return create_engine(cadena, pool_pre_ping=True, pool_recycle=3600)


@st.cache_data(ttl=300, show_spinner="Conectando con la base de datos…")
def cargar_datos() -> pd.DataFrame:
    """
    Carga todos los registros de la tabla principal desde MySQL.
    El resultado se almacena en caché durante 5 minutos para no
    hacer una query en cada interacción del usuario.
    """
    engine = _engine()
    query  = f"SELECT * FROM `{TABLA_PRINCIPAL}` ORDER BY fecha_registro ASC"
    df     = pd.read_sql(query, con=engine, parse_dates=["fecha_registro"])
    return df


def obtener_datos_con_error() -> pd.DataFrame:
    """
    Wrapper con manejo de errores amigable. Si MySQL no está disponible,
    muestra un mensaje claro y detiene la app en lugar de crashear feo.
    """
    try:
        df = cargar_datos()
        if df.empty:
            st.warning(
                "⚠️  La tabla está vacía. Asegúrate de haber corrido los 3 pasos del ETL:\n"
                "1. `python extraccion.py`\n"
                "2. `python transformacion.py`\n"
                "3. `python carga_sql.py`"
            )
            st.stop()
        return df
    except Exception as err:
        st.error(f"❌  No se pudo conectar a MySQL: **{err}**")
        st.info(
            "Verifica que MySQL esté corriendo y que `config.py` tenga "
            "las credenciales correctas."
        )
        st.stop()


# =============================================================================
# 3. CONSTANTES VISUALES
# =============================================================================

# Paleta de colores por sexenio
COLOR_SEXENIO = {
    "Peña Nieto": "#60A5FA",   # Azul claro
    "AMLO":       "#34D399",   # Verde esmeralda
    "Sheinbaum":  "#F87171",   # Rojo coral
    "Todos":      "#22D3EE",   # Cian
}
# Colores individuales para gráficas
C_TEAL   = "#22D3EE"    # Cian principal
C_BLUE   = "#60A5FA"    # Azul
C_GREEN  = "#34D399"    # Verde
C_RED    = "#F87171"    # Rojo
C_YELLOW = "#FBBF24"    # Amarillo
C_PURPLE = "#A78BFA"    # Morado

# Layout base que aplica a todos los gráficos Plotly
_PLOT_BASE = dict(
    template      = "plotly_dark",
    paper_bgcolor = "#0F1829",
    plot_bgcolor  = "#0F1829",
    font          = dict(family="DM Sans, sans-serif", color="#94A3B8", size=12),
    margin        = dict(l=48, r=20, t=46, b=40),
    legend        = dict(
        bgcolor     = "rgba(0,0,0,0)",
        bordercolor = "rgba(0,0,0,0)",
        font        = dict(size=11),
    ),
    xaxis = dict(
        gridcolor     = "#141E30",
        linecolor     = "#1E2D47",
        zerolinecolor = "#1E2D47",
        tickfont      = dict(size=10),
    ),
    yaxis = dict(
        gridcolor     = "#141E30",
        linecolor     = "#1E2D47",
        zerolinecolor = "#1E2D47",
        tickfont      = dict(size=10),
    ),
    hoverlabel = dict(
        bgcolor   = "#0F1829",
        font_size = 13,
        bordercolor = "#1E3A5F",
    ),
)


def plotly_layout(**extra) -> dict:
    """
    Combina el layout base con argumentos adicionales.
    Permite personalizar por gráfica sin repetir todo el dict.
    Uso: fig.update_layout(**plotly_layout(title="...", height=300))
    """
    return {**_PLOT_BASE, **extra}


# =============================================================================
# 4. COMPONENTES REUTILIZABLES
# =============================================================================

def html_divider():
    """Línea horizontal decorativa."""
    st.markdown('<hr class="hr-dark">', unsafe_allow_html=True)


def render_info_box(titulo: str, texto: str):
    """
    Renderiza el bloque educativo '💡 Economía para no economistas'.
    Aparece al final de cada dashboard para contextualizar las gráficas.
    """
    st.markdown(
        f"""
        <div class="info-box">
            <h4>💡 Economía para no economistas — {titulo}</h4>
            <p>{texto}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def filtro_sexenio(df: pd.DataFrame, key: str):
    """
    Muestra un selectbox con los sexenios disponibles (+ "Todos").
    Retorna una tupla: (DataFrame filtrado, nombre del sexenio seleccionado).
    Debe llamarse dentro del bloque 'with col:' donde quieres que aparezca.
    """
    opciones = ["Todos"] + sorted(df["sexenio"].dropna().unique().tolist())
    sel = st.selectbox("🗓️ Filtrar por Sexenio", opciones, key=key)
    if sel != "Todos":
        return df[df["sexenio"] == sel].copy(), sel
    return df.copy(), "Todos"


def safe_last(series: pd.Series, decimals: int = 2) -> float:
    """Devuelve el último valor no-nulo de una serie, o 0.0 si está vacía."""
    clean = series.dropna()
    return round(float(clean.iloc[-1]), decimals) if not clean.empty else 0.0


def safe_first(series: pd.Series, decimals: int = 2) -> float:
    """Devuelve el primer valor no-nulo de una serie, o 1.0 si está vacía."""
    clean = series.dropna()
    return round(float(clean.iloc[0]), decimals) if not clean.empty else 1.0


def pct_variacion(actual: float, base: float) -> float:
    """Calcula la variación porcentual; evita división por cero."""
    return round(((actual / base) - 1) * 100, 2) if base != 0 else 0.0


def fecha_de_max(df: pd.DataFrame, columna: str) -> str:
    """Retorna la fecha (como string 'Mes AAAA') del valor máximo de la columna."""
    if df.empty or columna not in df.columns:
        return "—"
    idx = df[columna].idxmax()
    return df.loc[idx, "fecha_registro"].strftime("%b %Y")


# =============================================================================
# 5. SIDEBAR — MENÚ DE NAVEGACIÓN
# =============================================================================
with st.sidebar:
    st.markdown("""
        <div style="text-align:center; padding:14px 0 22px;">
            <div style="font-family:'Syne',sans-serif; font-size:1.25rem;
                        font-weight:800; color:#F1F5F9; letter-spacing:0.02em;">
                📊 Inflación MX
            </div>
            <div style="font-size:0.67rem; color:#334155;
                        letter-spacing:0.12em; text-transform:uppercase; margin-top:5px;">
                Panel Económico 2012 – 2025
            </div>
        </div>
        <hr style="border:none; border-top:1px solid #162032; margin-bottom:14px;">
    """, unsafe_allow_html=True)

    SECCIONES = [
        "🏠  Inicio",
        "📈  Dashboard 1 — El Costo de la Vida",
        "💰  Dashboard 2 — Salario vs Realidad",
        "💵  Dashboard 3 — El Factor Dólar",
    ]
    seccion = st.radio("Secciones", SECCIONES, label_visibility="collapsed")

    st.markdown("""
        <hr style="border:none; border-top:1px solid #162032; margin-top:22px;">
        <div style="font-size:0.67rem; color:#1E3050; text-align:center;
                    padding-top:10px; line-height:1.9;">
            Fuente de datos:<br>
            Banxico API · CONASAMI<br>
            Rango: 2012 – 2025
        </div>
    """, unsafe_allow_html=True)

# Carga única de datos para toda la sesión
df_all = obtener_datos_con_error()


# =============================================================================
# SECCIÓN 1 ─ INICIO / HOME
# =============================================================================
if seccion == SECCIONES[0]:

    # ── Encabezado principal ──────────────────────────────────────────────────
    st.markdown("""
        <h1 style="font-size:2.5rem; font-weight:800; margin:0 0 6px; line-height:1.1;">
            La Inflación en México
            <span style="color:#22D3EE;">2012 – 2025</span>
        </h1>
        <p style="color:#475569; font-size:1rem; margin:0 0 18px; max-width:680px;">
            Análisis del impacto económico en el poder adquisitivo de las familias
            mexicanas a lo largo de tres sexenios presidenciales.
        </p>
    """, unsafe_allow_html=True)

    # ── Equipo ────────────────────────────────────────────────────────────────
    st.markdown("""
        <div class="team-badge">
            <div class="label">👥 Equipo de Investigación</div>
            <div class="names">
                [Gaxiola Elizalde Uziel] &nbsp;·&nbsp;
                [Merin Zepeda Esteban] &nbsp;·&nbsp;
                [Chan Lauro Josheb] &nbsp;·&nbsp;
            </div>
        </div>
    """, unsafe_allow_html=True)

    html_divider()

    # ── Introducción al problema social ──────────────────────────────────────
    col_txt, col_card = st.columns([3, 2], gap="large")

    with col_txt:
        st.markdown("""
            <h2 style="font-size:1.4rem; margin-bottom:14px;">🔍 El problema social</h2>
            <div style="color:#94A3B8; font-size:0.9rem; line-height:1.88;">
                <p>La <strong style="color:#E2E8F0;">inflación</strong> es el aumento sostenido
                en los precios de bienes y servicios. Para la familia mexicana promedio esto no
                es un índice abstracto: es el carrito del supermercado que cada semana trae
                menos cosas con los mismos billetes, la renta que sube mientras el sueldo no
                alcanza, y la medicina que se vuelve un lujo.</p>
                <p>Entre 2012 y 2025, el <strong style="color:#E2E8F0;">INPC</strong> (Índice
                Nacional de Precios al Consumidor) ha registrado variaciones dramáticas
                impulsadas por la depreciación del peso, la pandemia de COVID-19, el conflicto
                en Ucrania y las políticas de cada administración.</p>
                <p>Este dashboard responde tres preguntas concretas:
                <strong style="color:#22D3EE;">¿En qué sexenio subieron más los precios?
                ¿El aumento salarial le ganó a la inflación?
                ¿Cómo nos afecta que el dólar esté caro?</strong></p>
            </div>
        """, unsafe_allow_html=True)

    with col_card:
        st.markdown("""
            <div class="intro-card">
                <h3>📌 Contenido del dashboard</h3>
                <div class="intro-card-item">
                    📈 <span><strong>Inflación</strong> — INPC mensual y anual por sexenio</span>
                </div>
                <div class="intro-card-item">
                    💰 <span><strong>Salario Real</strong> — Poder de compra vs sueldo nominal</span>
                </div>
                <div class="intro-card-item">
                    💵 <span><strong>Tipo de Cambio</strong> — Correlación dólar-precios</span>
                </div>
                <div class="intro-card-item">
                    🏛️ <span><strong>Tres sexenios</strong> — Peña Nieto, AMLO, Sheinbaum</span>
                </div>
                <div class="intro-card-item">
                    📊 <span><strong>3 dashboards</strong> interactivos con filtros dinámicos</span>
                </div>
                <div class="intro-card-item">
                    🗓️ <span><strong>Rango</strong> — Diciembre 2012 a junio 2025</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

    html_divider()

    # ── KPIs Globales ─────────────────────────────────────────────────────────
    st.markdown(
        "<h2 style='font-size:1.25rem; margin-bottom:18px;'>📊 Indicadores al Último Registro</h2>",
        unsafe_allow_html=True,
    )

    ultimo  = df_all.dropna(subset=["inpc_general"]).iloc[-1]
    primero = df_all.dropna(subset=["inpc_general"]).iloc[0]

    inf_act   = safe_last(df_all["inflacion_anual_porc"])
    tc_act    = safe_last(df_all["tipo_cambio_dolar"])
    sal_act   = safe_last(df_all["salario_minimo_diario"])
    poder_act = safe_last(df_all["poder_adquisitivo_relativo"], decimals=4)

    tc_2012  = safe_first(df_all["tipo_cambio_dolar"])
    sal_2012 = safe_first(df_all["salario_minimo_diario"])

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric(
            "🔥 Inflación Anual",
            f"{inf_act:.2f}%",
            delta=f"INPC: {safe_last(df_all['inpc_general'], 1)} pts"
        )
    with k2:
        st.metric(
            "💵 Tipo de Cambio (USD/MXN)",
            f"${tc_act:.2f}",
            delta=f"{pct_variacion(tc_act, tc_2012):+.1f}% vs dic 2012",
        )
    with k3:
        st.metric(
            "💰 Salario Mínimo Diario",
            f"${sal_act:.2f}",
            delta=f"{pct_variacion(sal_act, sal_2012):+.1f}% vs dic 2012",
        )
    with k4:
        st.metric(
            "📉 Poder Adquisitivo",
            f"{poder_act:.4f}",
            delta="Base 1.0000 en 2012",
            delta_color="off",
        )

    html_divider()

    # ── Gráfica panorámica de inflación ──────────────────────────────────────
    st.markdown(
        "<h2 style='font-size:1.25rem; margin-bottom:14px;'>"
        "📉 Vista General: Inflación Anual 2012 – 2025</h2>",
        unsafe_allow_html=True,
    )

    df_home = df_all.dropna(subset=["inflacion_anual_porc"]).copy()

    # Colores RGBA para rellenos semitransparentes por sexenio
    _FILL_RGBA = {
        "Peña Nieto": "rgba(96,165,250,0.10)",
        "AMLO":       "rgba(52,211,153,0.10)",
        "Sheinbaum":  "rgba(248,113,113,0.10)",
    }

    fig_home = go.Figure()
    for sx, color in COLOR_SEXENIO.items():
        if sx == "Todos":
            continue
        mask = df_home["sexenio"] == sx
        if not mask.any():
            continue
        df_sx = df_home[mask]
        fig_home.add_trace(go.Scatter(
            x         = df_sx["fecha_registro"],
            y         = df_sx["inflacion_anual_porc"],
            fill      = "tozeroy",
            fillcolor = _FILL_RGBA.get(sx, "rgba(34,211,238,0.08)"),
            line      = dict(color=color, width=2.5),
            name      = sx,
            mode      = "lines",
            hovertemplate = (
                "<b>%{x|%b %Y}</b><br>"
                "Inflación anual: <b>%{y:.2f}%</b><extra></extra>"
            ),
        ))

    # Línea de referencia: meta del Banco de México
    fig_home.add_hline(
        y                    = 4,
        line_dash            = "dot",
        line_color           = "#334155",
        annotation_text      = "Meta Banxico +4%",
        annotation_font_size = 11,
        annotation_font_color= "#475569",
    )
    fig_home.update_layout(**plotly_layout(
        title  = "Inflación Anual (%) — Tres Sexenios Presidenciales",
        height = 340,
        yaxis_title = "Inflación Anual (%)",
    ))
    st.plotly_chart(fig_home, use_container_width=True)

    render_info_box(
        "¿Qué es la inflación anual?",
        "Imagina que en enero de 2021 hiciste el mandado y pagaste $1,000 pesos. "
        "Si la inflación anual fue del 7%, ese mismo mandado un año después cuesta $1,070. "
        "Cuando la línea de la gráfica sube, tu dinero alcanza cada vez menos. "
        "La línea punteada es la meta del Banco de México: si la inflación se mantiene en 4%, "
        "la economía se considera 'estable'. Todo lo que está por encima significa que los "
        "precios corrieron más rápido de lo que los organismos esperaban."
    )


# =============================================================================
# SECCIÓN 2 ─ DASHBOARD 1: EL COSTO DE LA VIDA
# =============================================================================
elif seccion == SECCIONES[1]:

    st.markdown("""
        <h1 style="font-size:2rem; font-weight:800; margin:0 0 6px;">
            📈 El Costo de la Vida
        </h1>
        <p style="color:#475569; font-size:0.95rem; margin:0;">
            ¿En qué sexenio subieron más los precios?
        </p>
    """, unsafe_allow_html=True)

    html_divider()

    # ── Filtro por sexenio ────────────────────────────────────────────────────
    col_f, col_sp = st.columns([1, 3])
    with col_f:
        df_d1, sel1 = filtro_sexenio(df_all, key="d1_sx")

    html_divider()

    # ── KPIs ──────────────────────────────────────────────────────────────────
    st.markdown(
        "<h2 style='font-size:1.1rem; margin-bottom:16px;'>📌 Indicadores del Periodo</h2>",
        unsafe_allow_html=True,
    )

    df_d1_v = df_d1.dropna(subset=["inflacion_anual_porc", "inpc_general"])

    max_inf  = df_d1_v["inflacion_anual_porc"].max() if not df_d1_v.empty else 0
    min_inf  = df_d1_v["inflacion_anual_porc"].min() if not df_d1_v.empty else 0
    avg_inf  = df_d1_v["inflacion_anual_porc"].mean() if not df_d1_v.empty else 0
    inpc_max = df_d1_v["inpc_general"].max() if not df_d1_v.empty else 0
    inpc_min = df_d1_v["inpc_general"].min() if not df_d1_v.empty else 1
    var_inpc = pct_variacion(inpc_max, inpc_min)
    f_pico   = fecha_de_max(df_d1_v, "inflacion_anual_porc")

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("🔥 Pico de Inflación Anual",  f"{max_inf:.2f}%",  delta=f"en {f_pico}")
    with k2:
        st.metric("📉 Mínimo de Inflación",       f"{min_inf:.2f}%",
                  delta="Deflación parcial" if min_inf < 0 else "Punto más bajo del periodo")
    with k3:
        st.metric("📊 Inflación Promedio",        f"{avg_inf:.2f}%",  delta=f"Sexenio: {sel1}")
    with k4:
        st.metric("📈 Variación INPC Total",
                  f"{var_inpc:.1f}%",
                  delta=f"De {inpc_min:.0f} a {inpc_max:.0f} pts")

    html_divider()

    # ── Fila 1 de gráficas ────────────────────────────────────────────────────
    st.markdown(
        "<h2 style='font-size:1.1rem; margin-bottom:14px;'>📊 Análisis de Precios</h2>",
        unsafe_allow_html=True,
    )
    gc1, gc2 = st.columns(2, gap="medium")

    # Gráfica 1 ── Serie temporal de inflación anual con pico marcado
    with gc1:
        df_g1 = df_d1.dropna(subset=["inflacion_anual_porc"]).copy()
        color_sx = COLOR_SEXENIO.get(sel1, C_TEAL)

        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(
            x             = df_g1["fecha_registro"],
            y             = df_g1["inflacion_anual_porc"],
            fill          = "tozeroy",
            fillcolor     = "rgba(34,211,238,0.07)",
            line          = dict(color=color_sx, width=2.5),
            name          = "Inflación Anual",
            hovertemplate = "<b>%{x|%b %Y}</b><br>%{y:.2f}%<extra></extra>",
        ))
        # Marcador del pico máximo
        if not df_g1.empty:
            i_max = df_g1["inflacion_anual_porc"].idxmax()
            fig1.add_trace(go.Scatter(
                x             = [df_g1.loc[i_max, "fecha_registro"]],
                y             = [df_g1.loc[i_max, "inflacion_anual_porc"]],
                mode          = "markers+text",
                marker        = dict(color=C_RED, size=11, symbol="diamond"),
                text          = [f"Pico: {df_g1.loc[i_max, 'inflacion_anual_porc']:.1f}%"],
                textposition  = "top center",
                textfont      = dict(color=C_RED, size=10, family="DM Sans"),
                name          = "Pico",
                showlegend    = False,
            ))
        fig1.add_hline(
            y=4, line_dash="dot", line_color="#334155",
            annotation_text="Meta 4%",
            annotation_font_size=10, annotation_font_color="#475569",
        )
        fig1.update_layout(**plotly_layout(
            title       = "Inflación Anual (%) en el Tiempo",
            height      = 310,
            yaxis_title = "Inflación Anual (%)",
        ))
        st.plotly_chart(fig1, use_container_width=True)

    # Gráfica 2 ── Inflación mensual (barras rojo/verde)
    with gc2:
        df_g2 = df_d1.dropna(subset=["inflacion_mensual_porc"]).copy()
        bar_colors = df_g2["inflacion_mensual_porc"].apply(
            lambda x: C_RED if x > 0.5 else (C_GREEN if x <= 0 else C_YELLOW)
        )
        fig2 = go.Figure(go.Bar(
            x             = df_g2["fecha_registro"],
            y             = df_g2["inflacion_mensual_porc"],
            marker_color  = bar_colors,
            hovertemplate = "<b>%{x|%b %Y}</b><br>Mensual: %{y:.2f}%<extra></extra>",
        ))
        fig2.update_layout(**plotly_layout(
            title       = "Inflación Mensual (%) — cada barra = 1 mes",
            height      = 310,
            yaxis_title = "Inflación Mensual (%)",
        ))
        st.plotly_chart(fig2, use_container_width=True)

    # ── Fila 2 de gráficas ────────────────────────────────────────────────────
    gc3, gc4 = st.columns(2, gap="medium")

    # Gráfica 3 ── INPC máximo/mínimo por año (barras agrupadas)
    with gc3:
        df_anual = df_d1.copy()
        df_anual["año"] = df_anual["fecha_registro"].dt.year
        agg = df_anual.groupby("año").agg(
            inpc_max=("inpc_general", "max"),
            inpc_min=("inpc_general", "min"),
        ).reset_index()

        fig3 = go.Figure()
        fig3.add_trace(go.Bar(
            x             = agg["año"].astype(str),
            y             = agg["inpc_max"],
            name          = "INPC Máx. anual",
            marker_color  = C_BLUE,
            opacity       = 0.85,
            hovertemplate = "<b>%{x}</b><br>INPC máx: %{y:.2f}<extra></extra>",
        ))
        fig3.add_trace(go.Bar(
            x             = agg["año"].astype(str),
            y             = agg["inpc_min"],
            name          = "INPC Mín. anual",
            marker_color  = C_TEAL,
            opacity       = 0.70,
            hovertemplate = "<b>%{x}</b><br>INPC mín: %{y:.2f}<extra></extra>",
        ))
        fig3.update_layout(**plotly_layout(
            title       = "INPC Máximo y Mínimo por Año",
            barmode     = "group",
            height      = 310,
            yaxis_title = "INPC (puntos)",
        ))
        st.plotly_chart(fig3, use_container_width=True)

    # Gráfica 4 ── Dispersión INPC vs Inflación Anual con tamaño = magnitud
    with gc4:
        df_g4 = df_d1.dropna(subset=["inflacion_anual_porc", "inpc_general"]).copy()
        df_g4["mes_str"] = df_g4["fecha_registro"].dt.strftime("%b %Y")

        # Usamos colores por sexenio si el filtro es "Todos"
        dot_colors = (
            df_g4["sexenio"].map(COLOR_SEXENIO)
            if sel1 == "Todos"
            else [color_sx] * len(df_g4)
        )
        dot_sizes = np.clip(
            np.abs(df_g4["inflacion_anual_porc"]) * 2.5, 5, 20
        )

        fig4 = go.Figure(go.Scatter(
            x             = df_g4["inpc_general"],
            y             = df_g4["inflacion_anual_porc"],
            mode          = "markers",
            marker        = dict(
                color   = dot_colors,
                size    = dot_sizes,
                opacity = 0.80,
                line    = dict(width=0),
            ),
            text          = df_g4["mes_str"],
            hovertemplate = (
                "<b>%{text}</b><br>"
                "INPC: %{x:.1f} pts<br>"
                "Inflación anual: %{y:.2f}%<extra></extra>"
            ),
        ))
        fig4.update_layout(**plotly_layout(
            title       = "Dispersión: INPC vs Inflación Anual",
            height      = 310,
            xaxis_title = "INPC (puntos)",
            yaxis_title = "Inflación Anual (%)",
        ))
        st.plotly_chart(fig4, use_container_width=True)

    html_divider()
    render_info_box(
        "¿Qué significa esto para tu mandado?",
        "El INPC mide el precio promedio de una 'canasta' de productos que una familia "
        "típica compra: tortillas, leche, transporte, renta, medicinas… Si el INPC era "
        "100 en 2012 y hoy está en 160, necesitas 60% MÁS de dinero para comprar "
        "exactamente lo mismo. Las barras rojas en la gráfica mensual son los meses "
        "'caros': cuando la familia fue al súper, todo subió de golpe. Las barras verdes "
        "son raros meses de alivio. El 'pico' marcado con diamante rojo es el peor "
        "momento del periodo: el mes en que el dinero alcanzó menos."
    )


# =============================================================================
# SECCIÓN 3 ─ DASHBOARD 2: SALARIO VS REALIDAD
# =============================================================================
elif seccion == SECCIONES[2]:

    st.markdown("""
        <h1 style="font-size:2rem; font-weight:800; margin:0 0 6px;">
            💰 Salario vs Realidad
        </h1>
        <p style="color:#475569; font-size:0.95rem; margin:0;">
            ¿El aumento salarial le ganó a la inflación?
        </p>
    """, unsafe_allow_html=True)

    html_divider()

    # ── Filtro ────────────────────────────────────────────────────────────────
    col_f2, _ = st.columns([1, 3])
    with col_f2:
        df_d2, sel2 = filtro_sexenio(df_all, key="d2_sx")

    html_divider()

    # ── KPIs ──────────────────────────────────────────────────────────────────
    st.markdown(
        "<h2 style='font-size:1.1rem; margin-bottom:16px;'>📌 Indicadores de Poder Adquisitivo</h2>",
        unsafe_allow_html=True,
    )

    df_d2_v = df_d2.dropna(subset=["salario_minimo_diario", "salario_real_base2012"])

    sal_nom_fin = safe_last(df_d2_v["salario_minimo_diario"])
    sal_nom_ini = safe_first(df_d2_v["salario_minimo_diario"])
    sal_real_fin = safe_last(df_d2_v["salario_real_base2012"])
    sal_real_ini = safe_first(df_d2_v["salario_real_base2012"])
    poder_fin    = safe_last(df_d2_v["poder_adquisitivo_relativo"], decimals=4) \
                   if "poder_adquisitivo_relativo" in df_d2_v.columns else 0.0
    var_nom  = pct_variacion(sal_nom_fin, sal_nom_ini)
    var_real = pct_variacion(sal_real_fin, sal_real_ini)

    # Contar meses donde el aumento de salario superó la inflación mensual
    df_d2_m = df_d2.dropna(subset=["salario_minimo_diario", "inflacion_mensual_porc"]).copy()
    df_d2_m["delta_sal_m"] = df_d2_m["salario_minimo_diario"].pct_change() * 100
    meses_ganando = int((df_d2_m["delta_sal_m"] >= df_d2_m["inflacion_mensual_porc"]).sum())
    total_meses   = len(df_d2_m)
    pct_ganando   = (meses_ganando / total_meses * 100) if total_meses > 0 else 0

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("💵 Salario Nominal Final",
                  f"${sal_nom_fin:.2f}/día",
                  delta=f"{var_nom:+.1f}% vs inicio del periodo")
    with k2:
        st.metric("📊 Salario Real (Base 2012)",
                  f"${sal_real_fin:.2f}/día",
                  delta=f"{var_real:+.1f}% poder real",
                  delta_color="normal" if var_real >= 0 else "inverse")
    with k3:
        st.metric("🏦 Poder Adquisitivo",
                  f"{poder_fin:.4f}",
                  delta="1.0000 = igual que dic 2012",
                  delta_color="off")
    with k4:
        st.metric("✅ Meses Ganando a la Inflación",
                  f"{meses_ganando} / {total_meses}",
                  delta=f"{pct_ganando:.0f}% del tiempo")

    html_divider()
    st.markdown(
        "<h2 style='font-size:1.1rem; margin-bottom:14px;'>📊 Análisis Salarial</h2>",
        unsafe_allow_html=True,
    )

    # ── Fila 1 de gráficas ────────────────────────────────────────────────────
    gs1, gs2 = st.columns(2, gap="medium")

    # Gráfica 1 ── Salario Nominal vs Salario Real (líneas cruzadas)
    with gs1:
        df_gs1 = df_d2.dropna(subset=["salario_minimo_diario", "salario_real_base2012"]).copy()
        fig_s1 = go.Figure()
        fig_s1.add_trace(go.Scatter(
            x             = df_gs1["fecha_registro"],
            y             = df_gs1["salario_minimo_diario"],
            name          = "Salario Nominal",
            line          = dict(color=C_YELLOW, width=2.5),
            mode          = "lines",
            hovertemplate = "<b>%{x|%b %Y}</b><br>Nominal: $%{y:.2f}<extra></extra>",
        ))
        fig_s1.add_trace(go.Scatter(
            x             = df_gs1["fecha_registro"],
            y             = df_gs1["salario_real_base2012"],
            name          = "Salario Real (Base 2012)",
            line          = dict(color=C_TEAL, width=2.5, dash="dash"),
            mode          = "lines",
            hovertemplate = "<b>%{x|%b %Y}</b><br>Real: $%{y:.2f}<extra></extra>",
        ))
        fig_s1.update_layout(**plotly_layout(
            title       = "Salario Nominal vs Salario Real",
            height      = 310,
            yaxis_title = "Pesos diarios ($MXN)",
        ))
        st.plotly_chart(fig_s1, use_container_width=True)

    # Gráfica 2 ── Poder adquisitivo relativo en el tiempo
    with gs2:
        df_gs2 = df_d2.dropna(subset=["poder_adquisitivo_relativo"]).copy()
        fig_s2 = go.Figure()
        # Área de degradado bajo la curva
        fig_s2.add_trace(go.Scatter(
            x             = df_gs2["fecha_registro"],
            y             = df_gs2["poder_adquisitivo_relativo"],
            fill          = "tozeroy",
            fillcolor     = "rgba(248,113,113,0.08)",
            line          = dict(color=C_RED, width=2.5),
            mode          = "lines",
            name          = "Poder Adquisitivo",
            hovertemplate = "<b>%{x|%b %Y}</b><br>Índice: %{y:.4f}<extra></extra>",
        ))
        fig_s2.add_hline(
            y=1, line_dash="dot", line_color="#334155",
            annotation_text="Base 2012 (1.0)",
            annotation_font_size=10, annotation_font_color="#475569",
        )
        fig_s2.update_layout(**plotly_layout(
            title       = "Poder Adquisitivo Relativo (1.0 = diciembre 2012)",
            height      = 310,
            yaxis_title = "Índice de poder de compra",
        ))
        st.plotly_chart(fig_s2, use_container_width=True)

    # ── Fila 2 de gráficas ────────────────────────────────────────────────────
    gs3, gs4 = st.columns(2, gap="medium")

    # Gráfica 3 ── Dona: meses ganando vs perdiendo
    with gs3:
        fig_s3 = go.Figure(go.Pie(
            labels       = ["Salario ganó a la inflación", "Inflación superó al salario"],
            values       = [meses_ganando, max(total_meses - meses_ganando, 0)],
            hole         = 0.60,
            marker_colors= [C_TEAL, C_RED],
            textfont     = dict(size=12, color="#E2E8F0"),
            hovertemplate= (
                "<b>%{label}</b><br>"
                "Meses: %{value}<br>"
                "%{percent}<extra></extra>"
            ),
        ))
        fig_s3.update_layout(**plotly_layout(
            title      = "¿Cuántos meses ganó el salario?",
            height     = 310,
            showlegend = True,
            legend     = dict(
                orientation = "h",
                yanchor     = "bottom",
                y           = -0.2,
                xanchor     = "center",
                x           = 0.5,
                font        = dict(size=10),
                bgcolor     = "rgba(0,0,0,0)",
            ),
        ))
        st.plotly_chart(fig_s3, use_container_width=True)

    # Gráfica 4 ── Índice acumulado: salario vs precios (base 100 del inicio del periodo)
    with gs4:
        df_gs4 = df_d2.dropna(subset=["salario_minimo_diario", "inpc_general"]).copy()
        if not df_gs4.empty:
            base_s = df_gs4["salario_minimo_diario"].iloc[0]
            base_p = df_gs4["inpc_general"].iloc[0]
            df_gs4["idx_sal"]  = (df_gs4["salario_minimo_diario"] / base_s) * 100
            df_gs4["idx_inpc"] = (df_gs4["inpc_general"] / base_p) * 100

            fig_s4 = go.Figure()
            fig_s4.add_trace(go.Scatter(
                x             = df_gs4["fecha_registro"],
                y             = df_gs4["idx_sal"],
                name          = "Salario (índice)",
                line          = dict(color=C_YELLOW, width=2.5),
                hovertemplate = "<b>%{x|%b %Y}</b><br>Índice salario: %{y:.1f}<extra></extra>",
            ))
            fig_s4.add_trace(go.Scatter(
                x             = df_gs4["fecha_registro"],
                y             = df_gs4["idx_inpc"],
                name          = "Precios/INPC (índice)",
                line          = dict(color=C_RED, width=2.5, dash="dot"),
                hovertemplate = "<b>%{x|%b %Y}</b><br>Índice INPC: %{y:.1f}<extra></extra>",
            ))
            # Área de brecha entre ambas curvas
            fig_s4.add_trace(go.Scatter(
                x         = pd.concat([
                    df_gs4["fecha_registro"],
                    df_gs4["fecha_registro"].iloc[::-1]
                ]).reset_index(drop=True),
                y         = pd.concat([
                    df_gs4["idx_sal"],
                    df_gs4["idx_inpc"].iloc[::-1]
                ]).reset_index(drop=True),
                fill      = "toself",
                fillcolor = "rgba(251,191,36,0.05)",
                line      = dict(color="rgba(0,0,0,0)"),
                name      = "Brecha",
                showlegend= False,
            ))
            fig_s4.add_hline(
                y=100, line_dash="dot", line_color="#334155",
                annotation_text="Base 100",
                annotation_font_size=10, annotation_font_color="#475569",
            )
            fig_s4.update_layout(**plotly_layout(
                title       = "Crecimiento Acumulado: Salario vs Precios (Base 100)",
                height      = 310,
                yaxis_title = "Índice (Base 100 al inicio del periodo)",
            ))
            st.plotly_chart(fig_s4, use_container_width=True)

    html_divider()
    render_info_box(
        "¿Cuánto compras realmente con tu sueldo?",
        "El salario NOMINAL es el número que aparece en tu recibo de nómina: "
        "el mínimo pasó de $62 en 2012 a más de $278 en 2025. Parece mucho, ¿verdad? "
        "El truco está en el salario REAL: cuántas tortillas, litros de gasolina o "
        "pastillas de medicina puedes comprar con ese dinero. Si los precios subieron "
        "más rápido que tu sueldo, aunque tengas MÁS pesos en el bolsillo, en realidad "
        "puedes comprar MENOS. La gráfica de índice base 100 lo muestra claro: cuando "
        "la línea amarilla (salario) está por encima de la roja (precios), los "
        "trabajadores ganaron la batalla. Cuando la roja supera a la amarilla, "
        "la inflación se comió el aumento."
    )


# =============================================================================
# SECCIÓN 4 ─ DASHBOARD 3: EL FACTOR DÓLAR
# =============================================================================
elif seccion == SECCIONES[3]:

    st.markdown("""
        <h1 style="font-size:2rem; font-weight:800; margin:0 0 6px;">
            💵 El Factor Dólar
        </h1>
        <p style="color:#475569; font-size:0.95rem; margin:0;">
            ¿Cómo nos afecta el tipo de cambio?
        </p>
    """, unsafe_allow_html=True)

    html_divider()

    # ── Filtro ────────────────────────────────────────────────────────────────
    col_f3, _ = st.columns([1, 3])
    with col_f3:
        df_d3, sel3 = filtro_sexenio(df_all, key="d3_sx")

    html_divider()

    # ── KPIs ──────────────────────────────────────────────────────────────────
    st.markdown(
        "<h2 style='font-size:1.1rem; margin-bottom:16px;'>📌 Indicadores del Tipo de Cambio</h2>",
        unsafe_allow_html=True,
    )

    df_d3_tc = df_d3.dropna(subset=["tipo_cambio_dolar"])

    tc_max   = df_d3_tc["tipo_cambio_dolar"].max() if not df_d3_tc.empty else 0
    tc_min   = df_d3_tc["tipo_cambio_dolar"].min() if not df_d3_tc.empty else 0
    tc_prom  = df_d3_tc["tipo_cambio_dolar"].mean() if not df_d3_tc.empty else 0
    tc_ini   = safe_first(df_d3_tc["tipo_cambio_dolar"])
    tc_fin   = safe_last(df_d3_tc["tipo_cambio_dolar"])
    var_tc   = pct_variacion(tc_fin, tc_ini)
    vol_tc   = df_d3_tc["tipo_cambio_dolar"].std() if not df_d3_tc.empty else 0
    f_tc_max = fecha_de_max(df_d3_tc, "tipo_cambio_dolar")

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("📈 Dólar Más Caro (Pico)",
                  f"${tc_max:.2f} MXN",
                  delta=f"en {f_tc_max}")
    with k2:
        st.metric("📊 Tipo de Cambio Promedio",
                  f"${tc_prom:.2f} MXN",
                  delta=f"Periodo: {sel3}")
    with k3:
        st.metric("📉 Variación Total del Periodo",
                  f"{var_tc:+.1f}%",
                  delta=f"De ${tc_ini:.2f} a ${tc_fin:.2f}",
                  delta_color="inverse")
    with k4:
        st.metric("📐 Volatilidad (σ)",
                  f"±{vol_tc:.2f}",
                  delta="Desviación estándar",
                  delta_color="off")

    html_divider()
    st.markdown(
        "<h2 style='font-size:1.1rem; margin-bottom:14px;'>📊 Análisis del Tipo de Cambio</h2>",
        unsafe_allow_html=True,
    )

    # ── Fila 1 de gráficas ────────────────────────────────────────────────────
    gt1, gt2 = st.columns(2, gap="medium")

    # Gráfica 1 ── Serie temporal del tipo de cambio
    with gt1:
        df_gt1 = df_d3.dropna(subset=["tipo_cambio_dolar"]).copy()
        fig_t1 = go.Figure()
        fig_t1.add_trace(go.Scatter(
            x             = df_gt1["fecha_registro"],
            y             = df_gt1["tipo_cambio_dolar"],
            fill          = "tozeroy",
            fillcolor     = "rgba(96,165,250,0.06)",
            line          = dict(color=C_BLUE, width=2.5),
            name          = "USD/MXN",
            hovertemplate = "<b>%{x|%b %Y}</b><br>$%{y:.2f} MXN<extra></extra>",
        ))
        # Línea de promedio del periodo
        if not df_gt1.empty:
            fig_t1.add_hline(
                y=tc_prom, line_dash="dot", line_color=C_YELLOW,
                annotation_text=f"Promedio ${tc_prom:.2f}",
                annotation_font_size=10, annotation_font_color=C_YELLOW,
            )
        fig_t1.update_layout(**plotly_layout(
            title       = "Tipo de Cambio USD/MXN en el Tiempo",
            height      = 310,
            yaxis_title = "Pesos por dólar ($MXN)",
        ))
        st.plotly_chart(fig_t1, use_container_width=True)

    # Gráfica 2 ── Dispersión: Dólar vs Inflación con línea de tendencia manual
    with gt2:
        df_gt2 = df_d3.dropna(subset=["tipo_cambio_dolar", "inflacion_anual_porc"]).copy()
        corr_val = df_gt2["tipo_cambio_dolar"].corr(
            df_gt2["inflacion_anual_porc"]
        ) if not df_gt2.empty else 0

        dot_colors_t2 = (
            df_gt2["sexenio"].map(COLOR_SEXENIO)
            if sel3 == "Todos"
            else [C_BLUE] * len(df_gt2)
        )
        fig_t2 = go.Figure()
        fig_t2.add_trace(go.Scatter(
            x             = df_gt2["tipo_cambio_dolar"],
            y             = df_gt2["inflacion_anual_porc"],
            mode          = "markers",
            marker        = dict(
                color   = dot_colors_t2,
                size    = 8,
                opacity = 0.80,
                line    = dict(width=0),
            ),
            text          = df_gt2["fecha_registro"].dt.strftime("%b %Y"),
            hovertemplate = (
                "<b>%{text}</b><br>"
                "USD/MXN: $%{x:.2f}<br>"
                "Inflación: %{y:.2f}%<extra></extra>"
            ),
        ))
        # Línea de tendencia con numpy (no necesita statsmodels)
        if len(df_gt2) >= 4:
            z    = np.polyfit(df_gt2["tipo_cambio_dolar"], df_gt2["inflacion_anual_porc"], 1)
            p    = np.poly1d(z)
            x_lr = np.linspace(df_gt2["tipo_cambio_dolar"].min(),
                               df_gt2["tipo_cambio_dolar"].max(), 120)
            fig_t2.add_trace(go.Scatter(
                x             = x_lr,
                y             = p(x_lr),
                mode          = "lines",
                line          = dict(color=C_YELLOW, width=2, dash="dash"),
                name          = "Tendencia (OLS)",
                hovertemplate = "Tendencia: %{y:.2f}%<extra></extra>",
            ))
        fig_t2.update_layout(**plotly_layout(
            title       = f"Dispersión: Dólar vs Inflación Anual  (r = {corr_val:.2f})",
            height      = 310,
            xaxis_title = "Tipo de Cambio (MXN/USD)",
            yaxis_title = "Inflación Anual (%)",
        ))
        st.plotly_chart(fig_t2, use_container_width=True)

    # ── Fila 2 de gráficas ────────────────────────────────────────────────────
    gt3, gt4 = st.columns(2, gap="medium")

    # Gráfica 3 ── Dólar e INPC normalizados: tendencias superpuestas
    with gt3:
        df_gt3 = df_d3.dropna(subset=["tipo_cambio_dolar", "inpc_general"]).copy()
        if not df_gt3.empty:
            b_tc   = df_gt3["tipo_cambio_dolar"].iloc[0]
            b_inpc = df_gt3["inpc_general"].iloc[0]
            df_gt3["idx_tc"]   = (df_gt3["tipo_cambio_dolar"] / b_tc) * 100
            df_gt3["idx_inpc"] = (df_gt3["inpc_general"] / b_inpc) * 100

            fig_t3 = go.Figure()
            fig_t3.add_trace(go.Scatter(
                x             = df_gt3["fecha_registro"],
                y             = df_gt3["idx_tc"],
                name          = "Tipo de Cambio (índice)",
                line          = dict(color=C_BLUE, width=2.5),
                hovertemplate = "<b>%{x|%b %Y}</b><br>TC índice: %{y:.1f}<extra></extra>",
            ))
            fig_t3.add_trace(go.Scatter(
                x             = df_gt3["fecha_registro"],
                y             = df_gt3["idx_inpc"],
                name          = "INPC (índice)",
                line          = dict(color=C_RED, width=2.5, dash="dot"),
                hovertemplate = "<b>%{x|%b %Y}</b><br>INPC índice: %{y:.1f}<extra></extra>",
            ))
            fig_t3.add_hline(
                y=100, line_dash="dot", line_color="#334155",
                annotation_text="Base 100", annotation_font_size=10,
                annotation_font_color="#475569",
            )
            fig_t3.update_layout(**plotly_layout(
                title       = "Dólar vs INPC — Tendencias Superpuestas (Base 100)",
                height      = 310,
                yaxis_title = "Índice (Base 100 al inicio del periodo)",
            ))
            st.plotly_chart(fig_t3, use_container_width=True)

    # Gráfica 4 ── Variación mensual del tipo de cambio (barras)
    with gt4:
        df_gt4 = df_d3.dropna(subset=["tipo_cambio_dolar"]).copy()
        df_gt4["var_tc_m"] = df_gt4["tipo_cambio_dolar"].pct_change() * 100
        df_gt4 = df_gt4.dropna(subset=["var_tc_m"])

        bar_col_t = df_gt4["var_tc_m"].apply(
            lambda x: C_RED if x > 0 else C_GREEN
        )
        fig_t4 = go.Figure(go.Bar(
            x             = df_gt4["fecha_registro"],
            y             = df_gt4["var_tc_m"],
            marker_color  = bar_col_t,
            hovertemplate = (
                "<b>%{x|%b %Y}</b><br>"
                "Variación mensual: %{y:.2f}%<extra></extra>"
            ),
        ))
        fig_t4.update_layout(**plotly_layout(
            title       = "Variación Mensual del Tipo de Cambio (%)",
            height      = 310,
            yaxis_title = "Variación mensual (%)",
        ))
        st.plotly_chart(fig_t4, use_container_width=True)

    html_divider()
    render_info_box(
        "¿Por qué cuando sube el dólar, sube todo?",
        "México importa muchísimos productos: teléfonos, computadoras, medicamentos, "
        "gasolina, maquinaria industrial. Todos se pagan en dólares. Cuando el peso "
        "se deprecia, las empresas pagan MÁS pesos para comprar esos productos en el "
        "extranjero y, para no perder dinero, suben sus precios. Eso te llega a ti "
        "en el súper, la farmacia y la gasolinera. Además, materias primas como el "
        "maíz para las tortillas o el trigo para el pan tienen precio internacional "
        "en dólares. Por eso la correlación entre el dólar y la inflación suele ser "
        "alta: cuando la línea azul sube fuerte, la roja casi siempre la sigue. "
        "La línea de tendencia amarilla en la gráfica de dispersión confirma esa relación."
    )
