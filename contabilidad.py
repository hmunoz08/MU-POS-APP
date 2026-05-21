import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

def aplicar_estilo_luxury():
    st.markdown("""
        <style>
        .stApp { background-color: #0D0D0D; color: #E0E0E0; }
        h1, h2, h3, h4 { color: #D4AF37 !important; font-family: 'Playfair Display', serif; }
        .kpi-box { background-color: #161616; padding: 20px; border-radius: 8px; border: 1px solid #2A2415; text-align: center; margin-bottom: 15px; }
        .stButton>button { background-color: #D4AF37 !important; color: #000000 !important; font-weight: bold !important; }
        </style>
    """, unsafe_allow_html=True)

def conectar_db():
    return sqlite3.connect('sistema_negocio.db')

def inicializar_tabla_gastos():
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gastos_varios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            concepto TEXT NOT NULL,
            categoria TEXT NOT NULL,
            monto REAL NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def registrar_gasto_general(concepto, categoria, monto):
    conn = conectar_db()
    cursor = conn.cursor()
    fecha_h = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO gastos_varios (fecha, concepto, categoria, monto) VALUES (?, ?, ?, ?)", (fecha_h, concepto, categoria, int(round(monto))))
    conn.commit()
    conn.close()

def obtener_totales_contables():
    conn = conectar_db()
    cursor = conn.cursor()
    
    # Tolerancia analítica y control ante base de datos antigua o vacía
    try:
        cursor.execute("SELECT TOTAL(total_venta), TOTAL(utilidad_generada) FROM ventas")
        ingresos, utilidad_ventas = cursor.fetchone()
        costo_de_ventas = ingresos - utilidad_ventas
    except sqlite3.OperationalError:
        ingresos, utilidad_ventas, costo_de_ventas = 0, 0, 0
    
    try:
        cursor.execute("SELECT TOTAL(valor_pagado) FROM registro_jornales WHERE estado_pago = 'PAGADO'")
        egreso_nomina = cursor.fetchone()[0]
        cursor.execute("SELECT TOTAL(valor_pagado) FROM registro_jornales WHERE estado_pago = 'PENDIENTE POR PAGAR'")
        pasivo_nomina = cursor.fetchone()[0]
    except sqlite3.OperationalError:
        egreso_nomina, pasivo_nomina = 0, 0
        
    try:
        cursor.execute("SELECT TOTAL(monto) FROM gastos_varios")
        gastos_operativos_varios = cursor.fetchone()[0]
    except sqlite3.OperationalError:
        gastos_operativos_varios = 0
    
    conn.close()
    return int(round(ingresos)), int(round(costo_de_ventas)), int(round(egreso_nomina)), int(round(pasivo_nomina)), int(round(gastos_operativos_varios))

def render_modulo_contabilidad():
    aplicar_estilo_luxury()
    inicializar_tabla_gastos()
    
    st.title("📊 BALANCES, REPORTE P&G Y GASTOS OPERATIVOS 📊")
    st.write("---")
    
    tab1, tab2 = st.tabs(["📈 Balance y P&G", "💸 Registrar Gastos Menores / Fijos"])
    
    ingresos, costo_ventas, nomina, pasivos, gastos_varios = obtener_totales_contables()
    gastos_totales = nomina + gastos_varios
    utilidad_neta = (ingresos - costo_ventas) - gastos_totales
    margen = (utilidad_neta / ingresos) * 100 if ingresos > 0 else 0.0

    with tab1:
        col1, col2, col3 = st.columns(3)
        with col1: st.markdown(f"<div class='kpi-box'><span style='color:#888;'>INGRESOS BRUTOS COMERCIALES</span><br><b style='color:#55FF55; font-size:24px;'>${ingresos:,.0f}</b></div>", unsafe_allow_html=True)
        with col2: st.markdown(f"<div class='kpi-box'><span style='color:#888;'>COSTO MERCANCÍA VENDIDA</span><br><b style='color:#FF5555; font-size:24px;'>${costo_ventas:,.0f}</b></div>", unsafe_allow_html=True)
        with col3: st.markdown(f"<div class='kpi-box'><span style='color:#888;'>GASTOS OPERATIVOS (TOTAL)</span><br><b style='color:#FF5555; font-size:24px;'>${gastos_totales:,.0f}</b></div>", unsafe_allow_html=True)
        
        col4, col5 = st.columns(2)
        with col4: st.markdown(f"<div class='kpi-box' style='border: 1px solid #D4AF37;'><span style='color:#D4AF37;'>💵 CAJA NETAL REAL (P&G)</span><br><b style='color:{'#55FF55' if utilidad_neta>=0 else '#FF5555'}; font-size:26px;'>${utilidad_neta:,.0f} COP</b></div>", unsafe_allow_html=True)
        with col5: st.markdown(f"<div class='kpi-box'><span style='color:#888;'>📊 RENDIMIENTO OPERATIVO</span><br><b style='color:#FFF; font-size:26px;'>{margen:.1f}%</b></div>", unsafe_allow_html=True)
        
        st.write("---")
        st.subheader("🎯 Cómputo del Punto de Equilibrio")
        p_prom = st.number_input("Precio Venta Promedio Estimado ($):", min_value=1000, value=25000)
        c_prom = st.number_input("Costo Base Ponderado Estimado ($):", min_value=0, value=10000)
        
        if p_prom > c_prom:
            costos_fijos = gastos_totales + pasivos
            if costos_fijos > 0:
                req_unidades = int(round(costos_fijos / (p_prom - c_prom))) + 1
                st.success(f"🎯 Para mitigar tus costos y pasivos fijos acumulados (${costos_fijos:,.0f}), necesitas colocar un mínimo de **{req_unidades} unidades** en el mercado.")
        
        st.write("---")
        st.subheader("🏛️ Pasivos Laborales por Entregar")
        st.warning(f"Monto acumulado retenido por pagar a jornaleros/colaboradores: **${pasivos:,.0f} COP**")

    with tab2:
        with st.form("form_gastos", clear_on_submit=True):
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                concepto = st.text_input("Concepto / Descripción del Gasto:").strip()
                categoria = st.selectbox("Estructura de Gasto:", ["Servicios Públicos", "Transporte y Fletes", "Mantenimiento", "Insumos Locales", "Otros Egresos"])
            with col_g2:
                monto_g = st.number_input("Monto Pagado ($):", min_value=100, step=500, value=5000)
                
            # Renderizamos la casilla de verificación normal dentro del formulario
            certificado = st.checkbox("Certifico la salida conforme de caja para este egreso.")
            
            # El botón de envío exclusivo que controla el procesamiento
            enviar_formulario = st.form_submit_button("Asentar Egreso en Libro")
            
            if enviar_formulario:
                if not concepto:
                    st.error("🚨 Por favor, especifique el concepto del egreso.")
                elif not certificado:
                    st.error("🚨 Debes marcar la casilla de certificación para validar la salida de caja.")
                else:
                    registrar_gasto_general(concepto, categoria, monto_g)
                    st.success("✅ Asiento de egreso incorporado al balance diario exitosamente.")
                    st.rerun()