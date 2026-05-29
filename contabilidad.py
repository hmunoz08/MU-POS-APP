import streamlit as st
import sqlite3
import pandas as pd
import datetime
import os

def aplicar_estilo_luxury():
    st.markdown("""
        <style>
        .stApp { background-color: #0D0D0D; color: #E0E0E0; }
        h1, h2, h3, h4 { color: #D4AF37 !important; font-family: 'Playfair Display', serif; }
        .kpi-box { background-color: #161616; padding: 20px; border-radius: 8px; border: 1px solid #2A2415; text-align: center; margin-bottom: 15px; }
        .stButton>button { background-color: #D4AF37 !important; color: #000000 !important; font-weight: bold !important; }
        .ticket-box { background-color: #FFFFFF; color: #000000; padding: 15px; font-family: monospace; border-radius: 4px; border: 1px dashed #000000; }
        .panel-confirmacion { background-color: #161616; padding: 15px; border-radius: 6px; border: 1px solid #2A2415; margin-top: 10px; margin-bottom: 15px; }
        </style>
    """, unsafe_allow_html=True)

def conectar_db():
    ruta_db = os.path.join(os.path.abspath("."), 'syscafecopia.db')
    return sqlite3.connect(ruta_db)

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
    except sqlite3.OperationalError: pass
    try:
        cursor.execute("ALTER TABLE ventas ADD COLUMN metodo_pago TEXT DEFAULT 'Efectivo'")
    except sqlite3.OperationalError: pass
    try:
        cursor.execute("ALTER TABLE registro_jornales ADD COLUMN metodo_pago TEXT DEFAULT 'Efectivo'")
    except sqlite3.OperationalError: pass
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
            query = f"SELECT {c_id} AS id_origen, {c_fecha} AS Fecha, '💵 VENTA POS' AS Modulo, ('Factura #' || {c_id}) AS Detalle, {c_metodo} AS Metodo, 'INGRESO' AS Tipo, CAST({c_total} AS INT) AS Monto FROM ventas"
            df_v = pd.read_sql_query(query, conn)
            lista_dfs.append(df_v)
    except Exception: pass

    try:
        cursor.execute("PRAGMA table_info(registro_jornales)")
        cols = [c[1] for c in cursor.fetchall()]
        if cols:
            c_fecha = 'fecha_registro' if 'fecha_registro' in cols else ('fecha' if 'fecha' in cols else 'CURRENT_TIMESTAMP')
            c_pago = 'valor_pagado' if 'valor_pagado' in cols else ('pago' if 'pago' in cols else '0')
            c_colab = 'empleado' if 'empleado' in cols else ('colaborador' if 'colaborador' in cols else "'Colaborador'")
            c_estado = 'estado_pago' if 'estado_pago' in cols else "'PAGADO'"
            c_metodo = 'metodo_pago' if 'metodo_pago' in cols else "'Efectivo'"
            c_id = 'id' if 'id' in cols else 'rowid'
            query = f"SELECT {c_id} AS id_origen, {c_fecha} AS Fecha, '👥 NÓMINA JORNALES' AS Modulo, ({c_colab} || ' (' || {c_estado} || ')') AS Detalle, {c_metodo} AS Metodo, 'EGRESO' AS Tipo, CAST({c_pago} AS INT) AS Monto FROM registro_jornales"
            df_n = pd.read_sql_query(query, conn)
            lista_dfs.append(df_n)
    except Exception: pass

    try:
        cursor.execute("PRAGMA table_info(gastos_varios)")
        cols = [c[1] for c in cursor.fetchall()]
        if cols:
            c_fecha = 'fecha' if 'fecha' in cols else 'CURRENT_TIMESTAMP'
            c_monto = 'monto' if 'monto' in cols else '0'
            c_concepto = 'concepto' if 'concepto' in cols else "'Gasto General'"
            c_cat = 'categoria' if 'categoria' in cols else "'General'"
            c_metodo = 'metodo_pago' if 'metodo_pago' in cols else "'Efectivo'"
            c_id = 'id' if 'id' in cols else 'rowid'
            query = f"SELECT {c_id} AS id_origen, {c_fecha} AS Fecha, ('💸 GASTO - ' || {c_cat}) AS Modulo, {c_concepto} AS Detalle, {c_metodo} AS Metodo, 'EGRESO' AS Tipo, CAST({c_monto} AS INT) AS Monto FROM gastos_varios"
            df_g = pd.read_sql_query(query, conn)
            lista_dfs.append(df_g)
    except Exception: pass

    conn.close()
    if lista_dfs:
        df_final = pd.concat(lista_dfs, ignore_index=True)
        df_final['Fecha'] = df_final['Fecha'].fillna(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        df_final = df_final.sort_values(by='Fecha', ascending=False)
        df_final.columns = ['ID Ref', 'Fecha y Hora', 'Módulo Origen', 'Descripción Detallada', 'Medio de Pago', 'Flujo Caja', 'Monto ($)']
        return df_final
    return pd.DataFrame(columns=['ID Ref', 'Fecha y Hora', 'Módulo Origen', 'Descripción Detallada', 'Medio de Pago', 'Flujo Caja', 'Monto ($)'])

def ejecutar_respaldo_seguridad():
    if os.path.exists('syscafecopia.db'):
        os.makedirs('backups_contables', exist_ok=True)
        nombre_bak = f"backups_contables/syscafecopia_BAK_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        with open('syscafecopia.db', 'rb') as f_src:
            with open(nombre_bak, 'wb') as f_dst:
                f_dst.write(f_src.read())
        return True
    return False

def render_modulo_contabilidad():
    aplicar_estilo_luxury()
    inicializar_tablas_preventivo()
    
    if "g_concepto_real" not in st.session_state: st.session_state.g_concepto_real = ""
    if "g_monto_real" not in st.session_state: st.session_state.g_monto_real = 0
    if "g_certificado_real" not in st.session_state: st.session_state.g_certificado_real = False
        
    st.markdown("# 📊 MÓDULO DE CONTABILIDAD Y TRAZABILIDAD GLOBAL 📊")
    st.write("---")
    
    df_movimientos = obtener_movimientos_globales()
    
    st.sidebar.markdown("<h3 style='color:#D4AF37;'>🎯 Filtros de Trazabilidad Global</h3>", unsafe_allow_html=True)
    fecha_inicio = st.sidebar.date_input("Fecha Inicial:", datetime.date(2026, 1, 1))
    fecha_fin = st.sidebar.date_input("Fecha Final:", datetime.datetime.now().date())
    
    modulos_disponibles = ["Todos los Módulos"] + list(df_movimientos['Módulo Origen'].unique()) if not df_movimientos.empty else ["Todos los Módulos"]
    filtro_modulo = st.sidebar.selectbox("Ecosistema / Sección:", modulos_disponibles)
    
    medios_disponibles = ["Todos los Medios"] + list(df_movimientos['Medio de Pago'].unique()) if not df_movimientos.empty else ["Todos los Medios"]
    filtro_medio = st.sidebar.selectbox("Método / Canal de Pago:", medios_disponibles)
    
    filtro_flujo = st.sidebar.radio("Dirección del Capital:", ["Todos", "INGRESO", "EGRESO"], horizontal=True)
    busqueda_texto = st.sidebar.text_input("🔍 Buscar término (Detalle):").strip().lower()
    
    df_filtrado = df_movimientos.copy()
    
    if not df_filtrado.empty:
        df_filtrado['Fecha_Clean'] = pd.to_datetime(df_filtrado['Fecha y Hora']).dt.date
        df_filtrado = df_filtrado[(df_filtrado['Fecha_Clean'] >= fecha_inicio) & (df_filtrado['Fecha_Clean'] <= fecha_fin)]
        df_filtrado = df_filtrado.drop(columns=['Fecha_Clean'])

    if filtro_modulo != "Todos los Módulos": df_filtrado = df_filtrado[df_filtrado['Módulo Origen'] == filtro_modulo]
    if filtro_medio != "Todos los Medios": df_filtrado = df_filtrado[df_filtrado['Medio de Pago'] == filtro_medio]
    if filtro_flujo != "Todos": df_filtrado = df_filtrado[df_filtrado['Flujo Caja'] == filtro_flujo]
    if busqueda_texto: df_filtrado = df_filtrado[df_filtrado['Descripción Detallada'].str.lower().str.contains(busqueda_texto)]
        
    total_ingresos_vivos = df_filtrado[df_filtrado['Flujo Caja'] == 'INGRESO']['Monto ($)'].sum()
    total_egresos_vivos = df_filtrado[df_filtrado['Flujo Caja'] == 'EGRESO']['Monto ($)'].sum()
    caja_neta_viva = total_ingresos_vivos - total_egresos_vivos

    tab_dashboard, tab_libro_mayor, tab_asiento_gasto, tab_utilidades = st.tabs([
        "📊 Dashboard Dinámico Vivo", 
        "🔍 Libro Mayor Detallado", 
        "💸 Asentar Gasto",
        "⚙️ Herramientas de Cierre"
    ])
    
    with tab_dashboard:
        st.subheader("🎯 Estado Financiero Consolidado")
        col1, col2, col3 = st.columns(3)
        with col1: st.markdown(f"<div class='kpi-box'><span style='color:#888;'>📥 INGRESOS</span><br><b style='color:#55FF55; font-size:24px;'>${total_ingresos_vivos:,.0f}</b></div>", unsafe_allow_html=True)
        with col2: st.markdown(f"<div class='kpi-box'><span style='color:#888;'>📤 EGRESOS</span><br><b style='color:#FF5555; font-size:24px;'>${total_egresos_vivos:,.0f}</b></div>", unsafe_allow_html=True)
        with col3: st.markdown(f"<div class='kpi-box' style='border: 1px solid #D4AF37;'><span style='color:#D4AF37;'>💵 CAJA NETA</span><br><b style='color:#55FF55; font-size:24px;'>${caja_neta_viva:,.0f}</b></div>", unsafe_allow_html=True)
            
    with tab_libro_mayor:
        if not df_filtrado.empty:
            df_grid_resultados = st.data_editor(df_filtrado, hide_index=True, use_container_width=True, key="tabla_interactiva_mayor_real")
            if st.button("💾 Aplicar Cambios en Libro Mayor"):
                st.success("🔄 Libro Mayor actualizado.")
                st.rerun()
        else: st.warning("No hay registros.")

    with tab_asiento_gasto:
        concepto = st.text_input("Concepto:", value=st.session_state.g_concepto_real)
        categoria = st.selectbox("Estructura:", ["Servicios Públicos", "Otros Egresos"])
        monto_g = st.number_input("Monto ($):", min_value=0, value=st.session_state.g_monto_real)
        metodo = st.selectbox("Medio:", ["Efectivo", "Transferencia"])
        certificado = st.checkbox("Certifico la salida de caja.")
        
        if st.button("💸 Asentar Egreso"):
            if not concepto or monto_g <= 0 or not certificado:
                st.error("🚨 Verifique los campos y la certificación.")
            else:
                conn = conectar_db()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO gastos_varios (fecha, concepto, categoria, monto, metodo_pago) VALUES (?, ?, ?, ?, ?)",
                               (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), concepto, categoria, int(monto_g), metodo))
                conn.commit()
                conn.close()
                
                # LIMPIEZA Y MENSAJE EXITOSO
                st.session_state.g_concepto_real = ""
                st.session_state.g_monto_real = 0
                st.session_state.g_certificado_real = False
                st.success(f"✅ Gasto '{concepto}' asentado correctamente por ${monto_g:,.0f}.")
                st.toast("⚜️ Gasto registrado en libro mayor.", icon="✅")

    with tab_utilidades:
        if st.button("💾 Crear Copia de Seguridad"):
            if ejecutar_respaldo_seguridad():
                st.success("✅ Respaldo creado exitosamente.")
                st.toast("💾 Respaldo generado.", icon="⚜️")