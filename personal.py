import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

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
    return sqlite3.connect('sistema_negocio.db')

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

def pagar_todo_pendiente_empleado(nombre_empleado):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE registro_jornales SET estado_pago = 'PAGADO' WHERE empleado = ? AND estado_pago = 'PENDIENTE POR PAGAR'", (nombre_empleado,))
    conn.commit()
    conn.close()

def obtener_libro_jornales():
    conn = conectar_db()
    try:
        df = pd.read_sql_query("""
            SELECT fecha_registro AS 'Fecha', empleado AS 'Colaborador', jornales_trabajados AS 'Días', 
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
    
    st.title("👥 CONTROL DE PERSONAL Y NÓMINA 👥")
    st.write("---")
    
    t_p1, t_p2 = st.tabs(["✍️ Cargar Jornadas del Día", "💰 Desembolsos de Salarios"])
    
    with t_p1:
        with st.form("form_nomina", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                emp = st.text_input("Nombre Completo del Trabajador:").strip()
                dias = st.number_input("Número de jornadas cumplidas:", min_value=0.5, max_value=31.0, step=0.5, value=1.0)
            with col2:
                v_dia = st.number_input("Estipendio por Día ($):", min_value=0, step=5000, value=50000)
                est_pago = st.selectbox("Condición de Entrega:", ["PENDIENTE POR PAGAR", "PAGADO"])
            
            st.markdown("<div class='panel-confirmacion'>", unsafe_allow_html=True)
            confirmar_planilla = st.checkbox("CONVENIO DE SEGURIDAD: Certifico bajo responsabilidad laboral que las jornadas asignadas son correctas.")
            st.markdown("</div>", unsafe_allow_html=True)
            
            # El botón de envío nativo del formulario de Streamlit
            enviar_planilla = st.form_submit_button("Liquidar Planilla")
            
            if enviar_planilla:
                if not emp:
                    st.error("❌ Por favor, escriba el nombre del colaborador.")
                elif not confirmar_planilla:
                    st.error("🚨 Debe marcar la casilla de confirmación obligatoria para procesar la planilla.")
                else:
                    registrar_jornal_local(emp, dias, v_dia, est_pago)
                    st.success(f"✔️ Planilla de {emp} guardada con éxito en el historial laboral.")
                    st.toast("¡Jornada registrada correctamente!")

    with t_p2:
        st.subheader("💳 Egresos y Saldos Pendientes de Nómina")
        df_j = obtener_libro_jornales()
        
        conn = conectar_db()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT DISTINCT empleado FROM registro_jornales WHERE estado_pago = 'PENDIENTE POR PAGAR'")
            con_deuda = [r[0] for r in cursor.fetchall()]
        except Exception:
            con_deuda = []
        conn.close()
        
        if con_deuda:
            emp_pago = st.selectbox("Colaborador a saldar cuentas:", con_deuda)
            
            st.markdown("<div class='panel-confirmacion'>", unsafe_allow_html=True)
            confirmar_desembolso = st.checkbox(f"CONVENIO DE SEGURIDAD: Autorizo la salida física de efectivo para saldar todos los pasivos de {emp_pago}.")
            st.markdown("</div>", unsafe_allow_html=True)
            
            if st.button("💰 Registrar Pago de Salario"):
                if confirmar_desembolso:
                    pagar_todo_pendiente_empleado(emp_pago)
                    st.success(f"✔️ Cuentas del colaborador {emp_pago} saldadas con éxito.")
                    st.rerun()
                else:
                    st.error("🚨 Debe marcar la casilla de confirmación obligatoria para procesar el desembolso financiero.")
        else: 
            st.info("🎉 Ecosistema al día. No hay pasivos ni cuentas pendientes de pago.")
        
        st.write("---")
        st.subheader("📋 Historial General de Novedades de Nómina")
        if not df_j.empty:
            st.dataframe(df_j, use_container_width=True, hide_index=True)
        else:
            st.info("No hay registros de jornadas en el sistema local.")