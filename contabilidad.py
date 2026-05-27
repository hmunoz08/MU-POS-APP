import streamlit as st
import sqlite3
import pandas as pd
import datetime  # Importación sanada para evitar el error de colisión de tipos
import os

def aplicar_estilo_luxury():
    st.markdown("""
        <style>
        .stApp { background-color: #0D0D0D; color: #E0E0E0; }
        h1, h2, h3, h4 { color: #D4AF37 !important; font-family: 'Playfair Display', serif; }
        .kpi-box { background-color: #161616; padding: 20px; border-radius: 8px; border: 1px solid #2A2415; text-align: center; margin-bottom: 15px; }
        .stButton>button { background-color: #D4AF37 !important; color: #000000 !important; font-weight: bold !important; }
        .ticket-box { background-color: #FFFFFF; color: #000000; padding: 15px; font-family: monospace; border-radius: 4px; border: 1px dashed #000000; }
        </style>
    """, unsafe_allow_html=True)

def conectar_db():
    # REPARACIÓN: Sincronizado para conectar con la base de datos unificada del sistema
    return sqlite3.connect('syscafecopia.db')

def inicializar_tablas_preventivo():
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gastos_varios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            concepto TEXT NOT NULL,
            categoria TEXT NOT NULL,
            monto REAL NOT NULL,
            metodo_pago TEXT DEFAULT 'Efectivo'
        )
    """)
    try:
        cursor.execute("ALTER TABLE gastos_varios ADD COLUMN metodo_pago TEXT DEFAULT 'Efectivo'")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE ventas ADD COLUMN metodo_pago TEXT DEFAULT 'Efectivo'")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE registro_jornales ADD COLUMN metodo_pago TEXT DEFAULT 'Efectivo'")
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()

def obtener_movimientos_globales():
    conn = conectar_db()
    cursor = conn.cursor()
    lista_dfs = []
    
    try:
        cursor.execute("PRAGMA table_info(ventas)")
        cols = [c[1] for c in cursor.fetchall()]
        if cols:
            c_fecha = 'fecha_venta' if 'fecha_venta' in cols else ('fecha' if 'fecha' in cols else 'CURRENT_TIMESTAMP')
            c_total = 'total_venta' if 'total_venta' in cols else ('total' if 'total' in cols else '0')
            c_metodo = 'metodo_pago' if 'metodo_pago' in cols else "'Efectivo'"
            c_id = 'id' if 'id' in cols else 'rowid'
            query = f"SELECT {c_fecha} AS Fecha, '💵 VENTA POS' AS Modulo, ('Factura #' || {c_id}) AS Detalle, {c_metodo} AS Metodo, 'INGRESO' AS Tipo, CAST({c_total} AS INT) AS Monto FROM ventas"
            df_v = pd.read_sql_query(query, conn)
            lista_dfs.append(df_v)
    except Exception:
        pass

    try:
        cursor.execute("PRAGMA table_info(registro_jornales)")
        cols = [c[1] for c in cursor.fetchall()]
        if cols:
            c_fecha = 'fecha_registro' if 'fecha_registro' in cols else ('fecha' if 'fecha' in cols else 'CURRENT_TIMESTAMP')
            c_pago = 'valor_pagado' if 'valor_pagado' in cols else ('pago' if 'pago' in cols else '0')
            c_colab = 'colaborador' if 'colaborador' in cols else "'Colaborador'"
            c_estado = 'estado_pago' if 'estado_pago' in cols else "'PAGADO'"
            c_metodo = 'metodo_pago' if 'metodo_pago' in cols else "'Efectivo'"
            query = f"SELECT {c_fecha} AS Fecha, '👥 NÓMINA JORNALES' AS Modulo, ({c_colab} || ' (' || {c_estado} || ')') AS Detalle, {c_metodo} AS Metodo, 'EGRESO' AS Tipo, CAST({c_pago} AS INT) AS Monto FROM registro_jornales"
            df_n = pd.read_sql_query(query, conn)
            lista_dfs.append(df_n)
    except Exception:
        pass

    try:
        cursor.execute("PRAGMA table_info(gastos_varios)")
        cols = [c[1] for c in cursor.fetchall()]
        if cols:
            c_fecha = 'fecha' if 'fecha' in cols else 'CURRENT_TIMESTAMP'
            c_monto = 'monto' if 'monto' in cols else '0'
            c_concepto = 'concepto' if 'concepto' in cols else "'Gasto General'"
            c_cat = 'categoria' if 'categoria' in cols else "'General'"
            c_metodo = 'metodo_pago' if 'metodo_pago' in cols else "'Efectivo'"
            query = f"SELECT {c_fecha} AS Fecha, ('💸 GASTO - ' || {c_cat}) AS Modulo, {c_concepto} AS Detalle, {c_metodo} AS Metodo, 'EGRESO' AS Tipo, CAST({c_monto} AS INT) AS Monto FROM gastos_varios"
            df_g = pd.read_sql_query(query, conn)
            lista_dfs.append(df_g)
    except Exception:
        pass

    conn.close()

    if lista_dfs:
        df_final = pd.concat(lista_dfs, ignore_index=True)
        df_final['Fecha'] = df_final['Fecha'].fillna(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        df_final = df_final.sort_values(by='Fecha', ascending=False)
        df_final.columns = ['Fecha y Hora', 'Módulo Origen', 'Descripción Detallada', 'Medio de Pago', 'Flujo Caja', 'Monto ($)']
        return df_final
    else:
        return pd.DataFrame(columns=['Fecha y Hora', 'Módulo Origen', 'Descripción Detallada', 'Medio de Pago', 'Flujo Caja', 'Monto ($)'])

def ejecutar_respaldo_seguridad():
    """Genera un backup local de la base de datos sin alterar nada."""
    # REPARACIÓN: Ajustado también aquí para respaldar la base de datos correcta
    if os.path.exists('syscafecopia.db'):
        if not os.path.exists('backups_contables'):
            os.makedirs('backups_contables')
        nombre_bak = f"backups_contables/syscafecopia_BAK_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        with open('syscafecopia.db', 'rb') as f_src:
            with open(nombre_bak, 'wb') as f_dst:
                f_dst.write(f_src.read())
        return True
    return False

def render_modulo_contabilidad():
    aplicar_estilo_luxury()
    inicializar_tablas_preventivo()
    
    # ADICIÓN SOLICITADA: Encabezado principal estandarizado con los otros módulos
    st.markdown("# 📊 MÓDULO DE CONTABILIDAD Y TRAZABILIDAD GLOBAL 📊")
    st.write("---")
    
    df_movimientos = obtener_movimientos_globales()
    
    # =========================================================
    # BARRA LATERAL - FILTROS COMPLETO CON CONTROL TEMPORAL
    # =========================================================
    st.sidebar.markdown("<h3 style='color:#D4AF37;'>🎯 Filtros de Trazabilidad Global</h3>", unsafe_allow_html=True)
    
    st.sidebar.markdown("**Rango Cronológico:**")
    fecha_inicio = st.sidebar.date_input("Fecha Inicial:", datetime.date(2026, 1, 1))
    fecha_fin = st.sidebar.date_input("Fecha Final:", datetime.datetime.now().date())
    
    modulos_disponibles = ["Todos los Módulos"] + list(df_movimientos['Módulo Origen'].unique()) if not df_movimientos.empty else ["Todos los Módulos"]
    filtro_modulo = st.sidebar.selectbox("Ecosistema / Sección:", modulos_disponibles)
    
    medios_disponibles = ["Todos los Medios"] + list(df_movimientos['Medio de Pago'].unique()) if not df_movimientos.empty else ["Todos los Medios"]
    filtro_medio = st.sidebar.selectbox("Método / Canal de Pago:", medios_disponibles)
    
    filtro_flujo = st.sidebar.radio("Dirección del Capital:", ["Todos", "INGRESO", "EGRESO"], horizontal=True)
    busqueda_texto = st.sidebar.text_input("🔍 Buscar término (Detalle):").strip().lower()
    
    # Proceso de filtrado seguro
    df_filtrado = df_movimientos.copy()
    
    if not df_filtrado.empty:
        df_filtrado['Fecha_Clean'] = pd.to_datetime(df_filtrado['Fecha y Hora']).dt.date
        df_filtrado = df_filtrado[(df_filtrado['Fecha_Clean'] >= fecha_inicio) & (df_filtrado['Fecha_Clean'] <= fecha_fin)]
        df_filtrado = df_filtrado.drop(columns=['Fecha_Clean'])

    if filtro_modulo != "Todos los Módulos":
        df_filtrado = df_filtrado[df_filtrado['Módulo Origen'] == filtro_modulo]
    if filtro_medio != "Todos los Medios":
        df_filtrado = df_filtrado[df_filtrado['Medio de Pago'] == filtro_medio]
    if filtro_flujo != "Todos":
        df_filtrado = df_filtrado[df_filtrado['Flujo Caja'] == filtro_flujo]
    if busqueda_texto:
        df_filtrado = df_filtrado[df_filtrado['Descripción Detallada'].str.lower().str.contains(busqueda_texto)]
        
    # Totales Matemáticos Vivos
    total_ingresos_vivos = df_filtrado[df_filtrado['Flujo Caja'] == 'INGRESO']['Monto ($)'].sum()
    total_egresos_vivos = df_filtrado[df_filtrado['Flujo Caja'] == 'EGRESO']['Monto ($)'].sum()
    caja_neta_viva = total_ingresos_vivos - total_egresos_vivos

    # Pestañas de Interfaz
    tab_dashboard, tab_libro_mayor, tab_asiento_gasto, tab_utilidades = st.tabs([
        "📊 Dashboard Dinámico Vivo", 
        "🔍 Libro Mayor Detallado (Trazabilidad Total)", 
        "💸 Asentar Gasto Administrativo / Operativo",
        "⚙️ Herramientas de Cierre y Respaldo"
    ])
    
    # =========================================================
    # PESTAÑA 1: DASHBOARD DINÁMICO VIVO
    # =========================================================
    with tab_dashboard:
        st.subheader("🎯 Estado Financiero Consolidado (Según Filtros)")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"<div class='kpi-box'><span style='color:#888;'>📥 TOTAL INGRESOS FILTRADOS</span><br><b style='color:#55FF55; font-size:24px;'>${total_ingresos_vivos:,.0f} COP</b></div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div class='kpi-box'><span style='color:#888;'>📤 TOTAL EGRESOS FILTRADOS</span><br><b style='color:#FF5555; font-size:24px;'>${total_egresos_vivos:,.0f} COP</b></div>", unsafe_allow_html=True)
        with col3:
            color_caja = "#55FF55" if caja_neta_viva >= 0 else "#FF5555"
            st.markdown(f"<div class='kpi-box' style='border: 1px solid #D4AF37;'><span style='color:#D4AF37;'>💵 CAJA NETA REAL EN PANTALLA</span><br><b style='color:{color_caja}; font-size:24px;'>${caja_neta_viva:,.0f} COP</b></div>", unsafe_allow_html=True)
            
        if total_ingresos_vivos > 0:
            porcentaje_gasto = (total_egresos_vivos / total_ingresos_vivos) * 100
            if porcentaje_gasto < 40:
                st.success("⚜️ OPERACIÓN EN ZONA DE EXCELENTE RENTABILIDAD: Los costos representan una proporción óptima del ingreso.")
            elif porcentaje_gasto <= 80:
                st.warning("⚠️ ALERTA DE SEGUIMIENTO: Flujo operativo balanceado. Vigilar el crecimiento de pasivos y jornales.")
            else:
                st.error("🚨 ALERTA DE EQUILIBRIO FINANCIERO: Los egresos operativos están absorbiendo la mayor parte de la caja.")

        st.write("---")
        st.subheader("📈 Proporción del Capital Operativo")
        
        if total_ingresos_vivos > 0 or total_egresos_vivos > 0:
            df_barras = pd.DataFrame({
                "Métrica Contable": ["Ingresos de Caja", "Egresos Consolidados", "Balance Neto"],
                "Monto ($)": [total_ingresos_vivos, total_egresos_vivos, caja_neta_viva]
            })
            st.bar_chart(data=df_barras, x="Métrica Contable", y="Monto ($)", use_container_width=True)
        else:
            st.info("No hay transacciones registradas que coincidan con los filtros seleccionados.")

    # =========================================================
    # PESTAÑA 2: LIBRO MAYOR (TRAZABILIDAD Y DESCARGAS)
    # =========================================================
    with tab_libro_mayor:
        st.subheader("📋 Libro de Registro de Movimientos Unitarios")
        
        if not df_filtrado.empty:
            st.dataframe(df_filtrado.style.format({"Monto ($)": "${:,.0f}"}), use_container_width=True, hide_index=True)
            st.write("---")
            st.subheader("📥 Central de Descargas Multi-Formato Oficial")
            
            csv_bytes = df_filtrado.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📊 Descargar Reporte Completo en Excel (.CSV)",
                data=csv_bytes,
                file_name=f"libro_mayor_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.warning("No hay filas que mostrar. Ajusta los criterios de búsqueda de la barra lateral.")

    # =========================================================
    # PESTAÑA 3: ASENTAMIENTO DE GASTOS
    # =========================================================
    with tab_asiento_gasto:
        st.subheader("💸 Formulario de Salida de Caja Homologado")
        with st.form("form_gastos_premium", clear_on_submit=True):
            col_in1, col_in2 = st.columns(2)
            with col_in1:
                concepto = st.text_input("Concepto / Descripción del Gasto:").strip()
                categoria = st.selectbox("Estructura de Gasto:", ["Servicios Públicos", "Transporte y Fletes", "Mantenimiento", "Insumos Locales", "Otros Egresos"])
            with col_in2:
                monto_g = st.number_input("Monto Pagado ($):", min_value=100, step=500, value=5000)
                metodo = st.selectbox("Medio Utilizado para el Pago:", ["Efectivo", "Tarjeta de Crédito", "Tarjeta de Débito", "Transferencia Bancaria", "Nequi/Daviplata"])
                
            certificado = st.checkbox("Certifico la salida conforme de caja para este egreso administrativo.")
            enviar_formulario = st.form_submit_button("Asentar Egreso en Libro Mayor")
            
            if enviar_formulario:
                if not concepto:
                    st.error("🚨 Por favor, especifique el concepto del egreso.")
                elif not certificado:
                    st.error("🚨 Debes marcar la casilla de certificación para validar la salida de caja.")
                else:
                    conn = conectar_db()
                    cursor = conn.cursor()
                    fecha_h = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    cursor.execute("INSERT INTO gastos_varios (fecha, concepto, categoria, monto, metodo_pago) VALUES (?, ?, ?, ?, ?)",
                                   (fecha_h, concepto, categoria, int(round(monto_g)), metodo))
                    conn.commit()
                    conn.close()
                    st.success("✅ Asiento de egreso incorporado al balance global con éxito.")
                    st.rerun()

    # =========================================================
    # PESTAÑA 4: HERRAMIENTAS DE CIERRE Y RESPALDO
    # =========================================================
    with tab_utilidades:
        st.subheader("⚙️ Operaciones de Cierre y Mantenimiento de Datos")
        
        col_ut1, col_ut2 = st.columns(2)
        
        with col_ut1:
            st.markdown("### 🖨️ Vista Previa Ticket de Cierre")
            st.write("Formato plano optimizado para imprimir directo en tiqueteras de 80mm:")
            
            texto_ticket = f"""========================================
      MYU LUXURY GOLD - CIERRE DE CAJA
      Fecha Arqueo: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}
========================================
INGRESOS FILTRADOS:  ${total_ingresos_vivos:,.0f}
EGRESOS FILTRADOS:   ${total_egresos_vivos:,.0f}
----------------------------------------
SALDO NETO EN CAJA:  ${caja_neta_viva:,.0f}

* Verificado localmente 100% Offline
========================================
"""
            st.text_area("Copia este texto para tu impresora térmica:", value=texto_ticket, height=180)
            
        with col_ut2:
            st.markdown("### 🗄️ Copias de Seguridad Locales")
            st.write("Resguarda tu historial contable completo en tu almacenamiento físico local:")
            
            if st.button("💾 Crear Copia Espejo de Base de Datos (.DB)"):
                if ejecutar_respaldo_seguridad():
                    st.success("✅ Respaldo de seguridad creado exitosamente en la carpeta '/backups_contables'")
                else:
                    st.error("🚨 Error al acceder al archivo de base de datos local.")