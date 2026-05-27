import streamlit as st
import sqlite3
import pandas as pd

def aplicar_estilo_luxury():
    st.markdown("""
        <style>
        .stApp { background-color: #0D0D0D; color: #E0E0E0; }
        h1, h2, h3, h4 { color: #D4AF37 !important; font-family: 'Playfair Display', serif; }
        .stButton>button { background-color: #D4AF37 !important; color: #000000 !important; font-weight: bold !important; }
        </style>
    """, unsafe_allow_html=True)

def conectar_db():
    # REPARACIÓN: Unificación al archivo de base de datos centralizado del sistema
    return sqlite3.connect('syscafecopia.db')

def inicializar_tabla_inventario():
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            cantidad INTEGER NOT NULL,
            costo_unitario REAL NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def registrar_o_actualizar_producto(codigo, nombre, cantidad, costo_unitario):
    conn = conectar_db()
    cursor = conn.cursor()
    cantidad = int(cantidad)
    costo_unitario = int(round(costo_unitario))
    
    cursor.execute("SELECT id, cantidad, costo_unitario FROM inventario WHERE codigo = ?", (codigo,))
    existe = cursor.fetchone()
    
    if existe:
        id_existente, cant_vieja, costo_viejo = existe
        nueva_cantidad = cant_vieja + cantidad
        if nueva_cantidad > 0:
            nuevo_costo = int(round(((cant_vieja * costo_viejo) + (cantidad * costo_unitario)) / nueva_cantidad))
        else:
            nuevo_costo = costo_unitario
        cursor.execute("UPDATE inventario SET cantidad = ?, costo_unitario = ? WHERE id = ?", (nueva_cantidad, nuevo_costo, id_existente))
        mensaje = f"Stock actualizado. Se sumaron {cantidad} unidades."
    else:
        cursor.execute("INSERT INTO inventario (codigo, nombre, cantidad, costo_unitario) VALUES (?, ?, ?, ?)", (codigo, nombre, cantidad, costo_unitario))
        mensaje = f"Nuevo artículo en almacén: '{nombre}' registrado."
        
    conn.commit()
    conn.close()
    return mensaje

def procesar_ajuste_stock(codigo, cantidad_baja):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, cantidad FROM inventario WHERE codigo = ?", (codigo,))
    res = cursor.fetchone()
    if res:
        id_p, nombre, cant_act = res
        if cant_act >= cantidad_baja:
            cursor.execute("UPDATE inventario SET cantidad = ? WHERE id = ?", (cant_act - cantidad_baja, id_p))
            conn.commit()
            conn.close()
            return True, f"Se dieron de baja {cantidad_baja} unidades de '{nombre}' por merma."
        else:
            conn.close()
            return False, f"Stock insuficiente en bodega. Disponibles: {cant_act}."
    conn.close()
    return False, "El código ingresado no existe."

def obtener_inventario_local():
    conn = conectar_db()
    try:
        df = pd.read_sql_query("SELECT codigo, nombre, cantidad, CAST(ROUND(costo_unitario) AS INTEGER) AS costo_unitario FROM inventario", conn)
    except Exception:
        df = pd.DataFrame(columns=['codigo', 'nombre', 'cantidad', 'costo_unitario'])
    conn.close()
    return df

def render_modulo_inventario():
    aplicar_estilo_luxury()
    inicializar_tabla_inventario()
    
    st.title("📦 GESTIÓN DE ALMACÉN E INVENTARIOS 📦")
    st.write("---")
    
    tab1, tab2 = st.tabs(["📥 Entrada de Mercancía", "🚨 Ajustes e Inventario Físico"])
    
    with tab1:
        with st.form("form_ingreso_inventario", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                codigo = st.text_input("Código de Producto / SKU:").strip()
                nombre = st.text_input("Nombre / Descripción del Artículo:").strip()
            with col2:
                cantidad = st.number_input("Cantidad Entrante:", min_value=1, step=1)
                costo = st.number_input("Costo Unitario de Adquisición ($):", min_value=0, step=500, value=0)
                
            confirmar_ingreso = st.checkbox("Confirmo el conteo físico y estado óptimo de la mercancía.")
            
            # EL BOTÓN DE ENVÍO REQUERIDO POR STREAMLIT FORM NATIVO:
            enviar_formulario = st.form_submit_button("Cargar Inventario a Bodega")
            
            if enviar_formulario:
                if not codigo or not nombre:
                    st.error("Campos obligatorios incompletos.")
                elif not confirmar_ingreso:
                    st.error("Debe certificar el conteo físico.")
                else:
                    st.success(registrar_o_actualizar_producto(codigo, nombre, cantidad, costo))
                    
        st.write("---")
        st.subheader("📋 Buscador General de Existencias")
        df_inv = obtener_inventario_local()
        if not df_inv.empty:
            busqueda = st.text_input("🔍 Filtrar por Nombre o SKU:").strip().lower()
            if busqueda:
                df_inv = df_inv[df_inv['codigo'].str.lower().str.contains(busqueda) | df_inv['nombre'].str.lower().str.contains(busqueda)]
            st.dataframe(df_inv.rename(columns={'codigo': 'Código/SKU', 'nombre': 'Producto', 'cantidad': 'Unidades', 'costo_unitario': 'Costo Ponderado ($)'}), use_container_width=True, hide_index=True)
        else:
            st.info("Bodega actualmente vacía.")

    with tab2:
        st.subheader("🚨 Registrar Bajas / Mermas de Almacén")
        with st.form("form_ajuste_inventario", clear_on_submit=True):
            cod_ajuste = st.text_input("Código de Producto a penalizar:").strip()
            cant_baja = st.number_input("Cantidad a retirar de existencias:", min_value=1, step=1)
            confirmar_ajuste = st.checkbox("CONFIESO BAJO AUDITORÍA: Esta merma fue corroborada en físico.")
            
            aplicar_baja = st.form_submit_button("Aplicar Ajuste Manual")
            
            if aplicar_baja:
                if not cod_ajuste or not confirmar_ajuste:
                    st.error("Verifique el código y marque la confirmación obligatoria.")
                else:
                    exito, msg = procesar_ajuste_stock(cod_ajuste, cant_baja)
                    if exito: st.success(msg)
                    else: st.error(msg)