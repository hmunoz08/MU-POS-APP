import streamlit as st
import sqlite3
import pandas as pd
import os
import datetime

def aplicar_estilo_luxury():
    st.markdown("""
        <style>
        .stApp { background-color: #0D0D0D; color: #E0E0E0; }
        h1, h2, h3, h4 { color: #D4AF37 !important; font-family: 'Playfair Display', serif; }
        .stButton>button { background-color: #D4AF37 !important; color: #000000 !important; font-weight: bold !important; }
        .panel-confirmacion { background-color: #161616; padding: 15px; border-radius: 6px; border: 1px solid #2A2415; margin-top: 10px; margin-bottom: 15px; }
        </style>
    """, unsafe_allow_html=True)

def conectar_db():
    ruta_db = os.path.join(os.path.abspath("."), 'syscafecopia.db')
    return sqlite3.connect(ruta_db)

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
    # Inicialización preventiva de gastos_varios por si se ejecuta primero este módulo
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
        mensaje = f"Stock actualizado. Se sumaron {cantidad} unidades de '{nombre}'."
    else:
        cursor.execute("INSERT INTO inventario (codigo, nombre, cantidad, costo_unitario) VALUES (?, ?, ?, ?)", (codigo, nombre, cantidad, costo_unitario))
        mensaje = f"Nuevo artículo en almacén: '{nombre}' registrado."
        
    # AUTOMATIZACIÓN DE CONTABILIDAD: Registro automático del egreso por la compra del insumo
    fecha_actual = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    monto_total_gasto = cantidad * costo_unitario
    concepto_gasto = f"Compra automática de insumo: {nombre} (x{cantidad})"
    
    cursor.execute("""
        INSERT INTO gastos_varios (fecha, concepto, categoria, monto, metodo_pago) 
        VALUES (?, ?, 'Insumos Locales', ?, 'Efectivo')
    """, (fecha_actual, concepto_gasto, monto_total_gasto))
        
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
        df = pd.read_sql_query("SELECT id, codigo, nombre, cantidad, CAST(ROUND(costo_unitario) AS INTEGER) AS costo_unitario FROM inventario", conn)
    except Exception:
        df = pd.DataFrame(columns=['id', 'codigo', 'nombre', 'cantidad', 'costo_unitario'])
    conn.close()
    return df

def render_modulo_inventario():
    aplicar_estilo_luxury()
    inicializar_tabla_inventario()
    
    if "inv_sku_real" not in st.session_state: st.session_state.inv_sku_real = ""
    if "inv_nombre_real" not in st.session_state: st.session_state.inv_nombre_real = ""
    if "inv_cant_real" not in st.session_state: st.session_state.inv_cant_real = 0
    if "inv_costo_real" not in st.session_state: st.session_state.inv_costo_real = 0
    if "inv_conf_real" not in st.session_state: st.session_state.inv_conf_real = False
    
    st.title("📦 GESTIÓN DE ALMACÉN E INVENTARIOS 📦")
    st.write("---")
    
    tab1, tab2 = st.tabs(["📥 Entrada de Mercancía", "📋 Stock de Bodega (Editar ✏️ / Eliminar 🗑️)"])
    
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            codigo = st.text_input("Código de Producto / SKU:", value=st.session_state.inv_sku_real, key="w_sku_inp").strip()
            nombre = st.text_input("Nombre / Descripción del Artículo:", value=st.session_state.inv_nombre_real, key="w_name_inp").strip()
        with col2:
            cantidad = st.number_input("Cantidad Entrante:", min_value=0, step=1, value=st.session_state.inv_cant_real, key="w_cant_inp")
            costo = st.number_input("Costo Unitario de Adquisición ($):", min_value=0, step=500, value=st.session_state.inv_costo_real, key="w_cost_inp")
            
        confirmar_ingreso = st.checkbox("Confirmo el conteo físico y estado óptimo de la mercancía.", value=st.session_state.inv_conf_real, key="w_conf_inp")
        
        if st.button("📥 Cargar Inventario a Bodega", use_container_width=True):
            if not codigo or not nombre:
                st.error("🚨 Campos obligatorios incompletos.")
            elif cantidad <= 0:
                st.error("🚨 La cantidad entrante debe ser mayor a cero.")
            elif not confirmar_ingreso:
                st.error("🚨 Debe certificar el conteo físico antes de procesar.")
            else:
                msg_exito = registrar_o_actualizar_producto(codigo, nombre, cantidad, costo)
                
                # 1. SE LIMPIAN LOS CAMPOS DEL FORMULARIO INMEDIATAMENTE
                st.session_state.inv_sku_real = ""
                st.session_state.inv_nombre_real = ""
                st.session_state.inv_cant_real = 0
                st.session_state.inv_costo_real = 0
                st.session_state.inv_conf_real = False
                
                # 2. SE MUESTRAN LOS MENSAJES (Permanecen visibles porque quitamos el rerun directo)
                st.success(f"⚜️ ¡INGRESO CORRECTO! | {msg_exito} El egreso ha sido asentado.")
                st.toast("📥 Inventario y Contabilidad Sincronizados.", icon="✅")

    with tab2:
        st.subheader("🚨 Registrar Bajas / Mermas Rápidas")
        col_aj1, col_aj2 = st.columns(2)
        with col_aj1:
            cod_ajuste = st.text_input("Código de Producto a penalizar:", key="ajuste_sku_real").strip()
        with col_aj2:
            cant_baja = st.number_input("Cantidad a retirar de existencias:", min_value=0, step=1, key="ajuste_cant_real")
        confirmar_ajuste = st.checkbox("CONFIESO BAJO AUDITORÍA: Esta merma fue corroborada en físico.", key="ajuste_conf_real")
        
        if st.button("🚨 Aplicar Ajuste Manual", use_container_width=True):
            if not cod_ajuste or cant_baja <= 0 or not confirmar_ajuste:
                st.error("🚨 Verifique el SKU, que la cantidad sea mayor a 0 y marque la auditoría.")
            else:
                exito, msg = procesar_ajuste_stock(cod_ajuste, cant_baja)
                if exito:
                    # 1. SE LIMPIAN LOS CAMPOS DE LA MERMA INMEDIATAMENTE
                    st.session_state.ajuste_sku_real = ""
                    st.session_state.ajuste_cant_real = 0
                    st.session_state.ajuste_conf_real = False
                    
                    # 2. SE MUESTRAN LOS MENSAJES DE MERMA
                    st.success(msg)
                    st.toast(f"⚠️ **MERMA REGISTRADA** | {msg}", icon="🗑️")
                else:
                    st.error(msg)
                    
        st.write("---")
        st.subheader("📋 Inventario Maestro Interactivo")
        st.caption("✏️ Edita haciendo doble clic sobre cualquier celda. 🗑️ Selecciona la fila y presiona la tecla 'Supr' o usa el icono de basurera lateral para eliminar al instante.")
        
        df_inv = obtener_inventario_local()
        if not df_inv.empty:
            busqueda = st.text_input("🔍 Filtrar visualización por Nombre o SKU:", key="filtro_buscador_inv").strip().lower()
            if busqueda:
                df_inv = df_inv[df_inv['codigo'].str.lower().str.contains(busqueda) | df_inv['nombre'].str.lower().str.contains(busqueda)]
            
            df_editado_inv = st.data_editor(
                df_inv,
                hide_index=True,
                use_container_width=True,
                num_rows="dynamic",
                disabled=["id"],
                column_config={
                    "codigo": st.column_config.TextColumn("Código SKU"),
                    "nombre": st.column_config.TextColumn("Producto / Descripción"),
                    "cantidad": st.column_config.NumberColumn("Unidades Stock", step=1),
                    "costo_unitario": st.column_config.NumberColumn("Costo Ponderado ($)", format="$%,.0f")
                },
                key="editor_inventario_inline_real"
            )
            
            if st.session_state.editor_inventario_inline_real.get("edited_rows") or st.session_state.editor_inventario_inline_real.get("deleted_rows"):
                conn = conectar_db()
                cursor = conn.cursor()
                
                indices_eliminados = st.session_state.editor_inventario_inline_real.get("deleted_rows", [])
                for idx in indices_eliminados:
                    fila_original = df_inv.iloc[idx]
                    id_db = int(fila_original["id"])
                    cursor.execute("DELETE FROM inventario WHERE id = ?", (id_db,))
                    
                    # ALERTA PREMIUM AL ELIMINAR FILA DIRECTA DEL MAESTRO
                    st.toast(f"⚠️ **ARTÍCULO ELIMINADO** | SKU {fila_original['codigo']} removido de bodega.", icon="🗑️")
                
                filas_editadas = st.session_state.editor_inventario_inline_real.get("edited_rows", {})
                for idx_str, cambios in filas_editadas.items():
                    idx = int(idx_str)
                    id_db = int(df_inv.iloc[idx]["id"])
                    
                    sku_act = cambios.get("codigo", df_inv.iloc[idx]["codigo"])
                    nom_act = cambios.get("nombre", df_inv.iloc[idx]["nombre"])
                    cant_act = cambios.get("cantidad", df_inv.iloc[idx]["cantidad"])
                    costo_act = cambios.get("costo_unitario", df_inv.iloc[idx]["costo_unitario"])
                    
                    cursor.execute("""
                        UPDATE inventario 
                        SET codigo = ?, nombre = ?, cantidad = ?, costo_unitario = ? 
                        WHERE id = ?
                    """, (sku_act, nom_act, int(cant_act), float(costo_act), id_db))
                    
                    # ALERTA PREMIUM AL MODIFICAR DIRECTAMENTE LA CELDA
                    st.toast(f"📝 **PRODUCTO ACTUALIZADO** | SKU {sku_act} guardado en maestro.", icon="🔄")
                
                conn.commit()
                conn.close()
                st.rerun()
        else:
            st.info("Bodega actualmente vacía.")