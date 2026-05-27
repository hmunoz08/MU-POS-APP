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
    return sqlite3.connect('sistema_negocio.db', timeout=10)

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
    # Título estilizado de la sección
    st.markdown("# 👥 CONTROL DE PERSONAL Y NÓMINA 👥")
    
    t_p1, t_p2 = st.tabs(["✍️ Cargar Jornadas del Día", "💰 Desembolsos de Salarios"])
    
    with t_p1:
        with st.form("form_nomina", clear_on_submit=True):
            emp = st.text_input("1. Nombre Completo del Trabajador:", placeholder="Ej: Juan Pérez").strip()
            
            col_izq, col_der = st.columns(2)
            with col_izq:
                dias = st.number_input("2. Número de jornadas cumplidas:", min_value=0.5, max_value=31.0, step=0.5, value=1.0)
                v_dia = st.number_input("3. Estipendio por Día ($):", min_value=0, step=5000, value=50000)
            with col_der:
                est_pago = st.selectbox("4. Condición de Entrega:", ["PENDIENTE POR PAGAR", "PAGADO"])
                st.write("")
            
            st.markdown("<div class='panel-confirmacion'>", unsafe_allow_html=True)
            confirmar_planilla = st.checkbox("CONVENIO DE SEGURIDAD: Certifico bajo responsabilidad laboral que las jornadas asignadas son correctas.")
            st.markdown("</div>", unsafe_allow_html=True)
            
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
        
        conn = conectar_db()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(valor_pagado) FROM registro_jornales WHERE estado_pago = 'PENDIENTE POR PAGAR'")
            total_pendiente = cursor.fetchone()[0] or 0
            
            cursor.execute("SELECT COUNT(DISTINCT empleado) FROM registro_jornales WHERE estado_pago = 'PENDIENTE POR PAGAR'")
            total_empleados_deuda = cursor.fetchone()[0] or 0
        except Exception:
            total_pendiente = 0
            total_empleados_deuda = 0
        conn.close()

        kpi1, kpi2 = st.columns(2)
        with kpi1:
            st.markdown(f"""
                <div style='background-color: #161616; padding: 15px; border-radius: 6px; border-top: 3px solid #D4AF37; text-align: center;'>
                    <p style='margin: 0; font-size: 13px; color: #aaa; text-transform: uppercase; font-weight: bold;'>Deuda Total de Nómina</p>
                    <h2 style='margin: 5px 0 0 0; color: #FF5555;'>${total_pendiente:,.0f} COP</h2>
                </div>
            """, unsafe_allow_html=True)
        with kpi2:
            st.markdown(f"""
                <div style='background-color: #161616; padding: 15px; border-radius: 6px; border-top: 3px solid #D4AF37; text-align: center;'>
                    <p style='margin: 0; font-size: 13px; color: #aaa; text-transform: uppercase; font-weight: bold;'>Trabajadores con Saldo</p>
                    <h2 style='margin: 5px 0 0 0; color: #D4AF37;'>{total_empleados_deuda} Persona(s)</h2>
                </div>
            """, unsafe_allow_html=True)
        st.write("")
        
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
            
            conn = conectar_db()
            df_cuentas = pd.read_sql_query("""
                SELECT id, fecha_registro AS 'Fecha', jornales_trabajados AS 'Días', 
                       CAST(ROUND(valor_pagado) AS INTEGER) AS 'Monto ($)'
                FROM registro_jornales 
                WHERE empleado = ? AND estado_pago = 'PENDIENTE POR PAGAR'
            """, conn, params=(emp_pago,))
            conn.close()
            
            if not df_cuentas.empty:
                st.write("### 📋 Selección de Cuentas a Liquidar")
                st.caption("Marque la casilla de la columna **Pagar** para los registros específicos que desea procesar:")
                
                df_cuentas.insert(0, 'Pagar', True)
                
                df_editado = st.data_editor(
                    df_cuentas,
                    hide_index=True,
                    use_container_width=True,
                    disabled=['id', 'Fecha', 'Días', 'Monto ($)'],
                    column_config={
                        "Pagar": st.column_config.CheckboxColumn(
                            "Pagar",
                            help="Seleccionar para pagar esta jornada",
                            default=True
                        ),
                        "Monto ($)": st.column_config.NumberColumn(
                            "Monto ($)",
                            format="$%,.0f"
                        )
                    }
                )
                
                cuentas_filtradas = df_editado[df_editado['Pagar'] == True]
                
                if not cuentas_filtradas.empty:
                    total_desembolso = cuentas_filtradas['Monto ($)'].sum()
                    ids_a_pagar = cuentas_filtradas['id'].tolist()
                    
                    st.markdown(f"""
                        <div class='panel-confirmacion' style='border-left: 4px solid #D4AF37;'>
                            <p style='margin:2px; color:#aaa;'>Jornadas seleccionadas: <b>{len(ids_a_pagar)} registro(s)</b></p>
                            <h3 style='color:#55FF55; margin:5px 0;'>TOTAL NETO A PAGAR: ${total_desembolso:,.0f} COP</h3>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("<div class='panel-confirmacion'>", unsafe_allow_html=True)
                    confirmar_desembolso = st.checkbox(f"CONVENIO DE SEGURIDAD: Autorizo la salida física de efectivo para saldar las cuentas marcadas de {emp_pago}.")
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    if st.button("💰 Registrar Pago de Salario"):
                        if confirmar_desembolso:
                            pagar_cuentas_seleccionadas_empleado(ids_a_pagar)
                            st.success(f"✔️ Se registraron como pagadas las cuentas seleccionadas de {emp_pago}.")
                            st.rerun()
                        else:
                            st.error("🚨 Debe marcar la casilla de confirmación obligatoria para procesar el desembolso financiero.")
                else:
                    st.warning("⚠️ Debe seleccionar al menos una jornada en la tabla superior para poder liquidar.")
        else: 
            st.info("🎉 Ecosistema al día. No hay pasivos ni cuentas pendientes de pago.")
        
        st.write("---")
        st.subheader("📋 Historial General de Novedades de Nómina")
        if not df_j.empty:
            filtro_nombre = st.text_input("🔍 Buscar en el historial por nombre del colaborador:", "").strip().lower()
            if filtro_nombre:
                df_filtrado = df_j[df_j['Colaborador'].str.lower().str.contains(filtro_nombre)]
            else:
                df_filtrado = df_j
                
            st.dataframe(df_filtrado, use_container_width=True, hide_index=True)
            
            st.write("")
            csv_data = df_j.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Exportar Historial de Nómina (CSV)",
                data=csv_data,
                file_name=f"REPORTE_NOMINA_MYU_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.info("No hay registros de jornadas en el sistema local.")