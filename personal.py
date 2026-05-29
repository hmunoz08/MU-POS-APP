import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import os

def aplicar_estilo_luxury():
    st.markdown("""
        <style>
        .stApp { background-color: #0D0D0D; color: #E0E0E0; }
        h1, h2, h3, h4 { color: #D4AF37 !important; font-family: 'Playfair Display', serif; }
        .stButton>button { background-color: #D4AF37 !important; color: #000000 !important; font-weight: bold !important; }
        .panel-confirmacion {
            background-color: #161616; padding: 15px; border-radius: 6px;
            border: 1px solid #2A2415; margin-top: 10px; margin-bottom: 15px;
        }
        </style>
    """, unsafe_allow_html=True)

def conectar_db():
    ruta_db = os.path.join(os.path.abspath("."), 'syscafecopia.db')
    return sqlite3.connect(ruta_db, timeout=10)

def inicializar_tabla_personal():
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS registro_jornales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_registro TEXT NOT NULL,
            empleado TEXT NOT NULL,
            jornales_trabajados REAL NOT NULL,
            valor_jornal REAL NOT NULL,
            valor_pagado REAL NOT NULL,
            estado_pago TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def registrar_jornal_local(empleado, jornadas, precio_dia, estado):
    conn = conectar_db()
    cursor = conn.cursor()
    total_liquidacion = int(round(jornadas * precio_dia))
    fecha_h = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO registro_jornales (fecha_registro, empleado, jornales_trabajados, valor_jornal, valor_pagado, estado_pago)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (fecha_h, empleado, jornadas, precio_dia, total_liquidacion, estado))
    conn.commit()
    conn.close()

def pagar_cuentas_seleccionadas_empleado(lista_ids):
    conn = conectar_db()
    cursor = conn.cursor()
    for id_jornal in lista_ids:
        cursor.execute("UPDATE registro_jornales SET estado_pago = 'PAGADO' WHERE id = ?", (id_jornal,))
    conn.commit()
    conn.close()

def obtener_libro_jornales():
    conn = conectar_db()
    try:
        df = pd.read_sql_query("""
            SELECT id, fecha_registro AS 'Fecha', empleado AS 'Colaborador', jornales_trabajados AS 'Días', 
                   CAST(ROUND(valor_jornal) AS INTEGER) AS 'Costo Día ($)', CAST(ROUND(valor_pagado) AS INTEGER) AS 'Total ($)', estado_pago AS 'Estado'
            FROM registro_jornales ORDER BY id DESC
        """, conn)
    except Exception:
        df = pd.DataFrame()
    conn.close()
    return df

def render_modulo_personal():
    aplicar_estilo_luxury()
    inicializar_tabla_personal()
    
    if "per_emp" not in st.session_state: st.session_state.per_emp = ""
    if "per_dias" not in st.session_state: st.session_state.per_dias = 0.0
    if "per_vdia" not in st.session_state: st.session_state.per_vdia = 0
    if "per_conf" not in st.session_state: st.session_state.per_conf = False
    
    st.markdown("# 👥 CONTROL DE PERSONAL Y NÓMINA 👥")
    
    t_p1, t_p2 = st.tabs(["✍️ Cargar Jornadas del Día", "💰 Desembolsos de Salarios"])
    
    with t_p1:
        emp = st.text_input("1. Nombre Completo del Trabajador:", value=st.session_state.per_emp, key="w_per_emp_inp").strip()
        col_izq, col_der = st.columns(2)
        with col_izq:
            dias = st.number_input("2. Número de jornadas:", min_value=0.0, step=0.5, value=st.session_state.per_dias, key="w_per_dias_inp")
            v_dia = st.number_input("3. Estipendio por Día ($):", min_value=0, step=5000, value=st.session_state.per_vdia, key="w_per_vdia_inp")
        with col_der:
            est_pago = st.selectbox("4. Condición de Entrega:", ["PENDIENTE POR PAGAR", "PAGADO"], key="per_estado")
        
        total_proyectado = int(round(dias * v_dia))
        st.markdown(f"**Liquidación Proyectada:** `${total_proyectado:,.0f} COP`")
        
        confirmar_planilla = st.checkbox("Certifico que las jornadas asignadas son correctas.", value=st.session_state.per_conf, key="w_per_conf_inp")
        
        if st.button("👥 Liquidar Planilla", use_container_width=True):
            if not emp or dias <= 0 or v_dia <= 0 or not confirmar_planilla:
                st.error("❌ Verifique nombre, cantidades y la casilla de confirmación.")
            else:
                registrar_jornal_local(emp, dias, v_dia, est_pago)
                st.success(f"✔️ Planilla de '{emp}' guardada exitosamente.")
                st.toast(f"⚜️ REGISTRO EXITOSO | Planilla de {emp} asentada.", icon="✅")
                # Limpieza de estados sin recargar toda la página
                st.session_state.per_emp = ""
                st.session_state.per_dias = 0.0
                st.session_state.per_vdia = 0
                st.session_state.per_conf = False

    with t_p2:
        st.subheader("💳 Egresos y Saldos Pendientes")
        df_j = obtener_libro_jornales()
        
        conn = conectar_db()
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(valor_pagado) FROM registro_jornales WHERE estado_pago = 'PENDIENTE POR PAGAR'")
        total_p = cursor.fetchone()[0] or 0
        conn.close()
        
        st.metric("Deuda Total de Nómina", f"${total_p:,.0f} COP")
        
        if not df_j.empty:
            st.dataframe(df_j, use_container_width=True)
            # Aquí incluirías la lógica de selección de IDs para pagar