import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import urllib.parse

def aplicar_estilo_luxury():
    st.markdown("""
        <style>
        /* Fondo general de la aplicación */
        .stApp { background-color: #0D0D0D; color: #E0E0E0; }
        
        /* REPARACIÓN DE TÍTULOS: Solo afecta a los encabezados de contenido, no a las pestañas ni módulos */
        .stApp h1, .stApp h2, .stApp h3, .stApp h4 { 
            color: #D4AF37 !important; 
            font-family: 'Playfair Display', serif; 
        }
        
        /* Botones dorados premium */
        .stButton>button {
            background-color: #D4AF37 !important; color: #000000 !important;
            font-weight: bold !important; border-radius: 4px !important;
            border: 1px solid #D4AF37 !important;
            transition: all 0.3s ease;
            width: 100%;
        }
        .stButton>button:hover {
            background-color: #000000 !important; color: #D4AF37 !important;
            border: 1px solid #D4AF37 !important;
        }

        /* Tarjetas de información y resumen */
        .pos-card {
            background-color: #161616; padding: 20px; border-radius: 6px;
            border: 1px solid #2A2415; margin-bottom: 15px;
        }

        /* DISEÑO DE LA FACTURA HERMOSA TIPO SIIGO (LUXURY GOLD & NOIR) */
        .factura-premium {
            background: linear-gradient(135deg, #111111 0%, #161616 100%) !important;
            color: #E0E0E0 !important;
            padding: 30px !important; 
            border-radius: 8px !important; 
            font-family: 'Courier New', Courier, monospace !important;
            border: 2px solid #D4AF37 !important;
            box-shadow: 0px 4px 20px rgba(212, 175, 55, 0.15) !important;
            margin-bottom: 25px !important;
            max-width: 500px !important;
            margin: 0 auto 25px auto !important;
        }
        .factura-header {
            text-align: center !important;
            border-bottom: 1px dashed #D4AF37 !important;
            padding-bottom: 15px !important;
            margin-bottom: 15px !important;
        }
        .factura-logo {
            font-size: 24px !important;
            font-weight: bold !important;
            color: #D4AF37 !important;
            letter-spacing: 2px !important;
            margin: 0 !important;
        }
        .factura-sub {
            font-size: 11px !important;
            color: #888 !important;
            text-transform: uppercase !important;
            letter-spacing: 1px !important;
            margin: 2px 0 !important;
        }
        .factura-meta {
            font-size: 13px !important;
            line-height: 1.6 !important;
            margin: 15px 0 !important;
            color: #E0E0E0 !important;
        }
        .factura-tabla-header {
            border-bottom: 1px solid #D4AF37 !important;
            font-weight: bold !important;
            color: #D4AF37 !important;
            padding-bottom: 5px !important;
            font-size: 12px !important;
            letter-spacing: 1px;
            white-space: pre !important;
        }
        .factura-items {
            font-size: 12px !important;
            line-height: 1.5 !important;
            white-space: pre !important;
            border-bottom: 1px dashed #D4AF37 !important;
            padding: 12px 0 !important;
            margin-bottom: 15px !important;
            color: #E0E0E0 !important;
        }
        .factura-totales {
            font-size: 13px !important;
            text-align: right !important;
            line-height: 1.8 !important;
            color: #E0E0E0 !important;
        }
        .factura-total-destacado {
            font-size: 17px !important;
            color: #55FF55 !important;
            font-weight: bold !important;
            margin-top: 8px !important;
            padding-top: 4px;
            border-top: 1px solid #2A2415;
        }
        .factura-footer {
            text-align: center !important;
            font-size: 11px !important;
            color: #666 !important;
            margin-top: 20px !important;
            border-top: 1px solid #222 !important;
            padding-top: 10px !important;
        }
        </style>
    """, unsafe_allow_html=True)

def conectar_db():
    # Sincronización absoluta de ruta local para evitar el error "no existe tal tabla" en PC
    import os
    ruta_db = os.path.join(os.path.abspath("."), 'syscafecopia.db')
    return sqlite3.connect(ruta_db)

def inicializar_tabla_ventas():
    conn = conectar_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT cliente FROM ventas LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("DROP TABLE IF EXISTS ventas")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            cliente TEXT NOT NULL,
            subtotal REAL NOT NULL,
            impuesto REAL NOT NULL,
            descuento REAL NOT NULL,
            total_venta REAL NOT NULL,
            metodo_pago TEXT NOT NULL,
            productos_detalles TEXT NOT NULL,
            utilidad_generada REAL NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def seguro_int(val):
    """Convierte de forma segura valores a entero evitando errores de bytes/caracteres raros"""
    try:
        if isinstance(val, bytes):
            val = val.decode('utf-8', errors='ignore')
        return int(float(val))
    except Exception:
        return 0

def obtener_productos_disponibles():
    conn = conectar_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT codigo, nombre, cantidad, costo_unitario FROM inventario WHERE cantidad > 0")
        productos = cursor.fetchall()
    except sqlite3.OperationalError:
        productos = []
    conn.close()
    return productos

def procesar_factura_completa(cliente, metodo, carrito, subtotal, imp_total, desc_total, total_neto):
    conn = conectar_db()
    cursor = conn.cursor()
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_utilidad = 0
    string_detalles = ""
    
    try:
        string_detalles += f"{'CANT':<5} {'DESCRIPCIÓN':<20} {'VALOR TOT':>12}\n"
        string_detalles += "-" * 39 + "\n"
        
        for item in carrito:
            codigo = item['codigo']
            cant = int(item['cantidad'])
            precio_v = seguro_int(item['precio_v'])
            
            cursor.execute("SELECT id, cantidad, costo_unitario, nombre FROM inventario WHERE codigo = ?", (codigo,))
            prod = cursor.fetchone()
            id_p, stock_act, costo_u, nombre_prod = prod
            
            utilidad_item = (precio_v * cant) - (seguro_int(costo_u) * cant)
            total_utilidad += utilidad_item
            
            nombre_recortado = nombre_prod[:19]
            val_tot_item = cant * precio_v
            string_detalles += f"{cant:<5} {nombre_recortado:<20} ${val_tot_item:>11,.0f}\n"
            
            cursor.execute("UPDATE inventario SET cantidad = ? WHERE id = ?", (stock_act - cant, id_p))
            
        total_utilidad -= desc_total
        cursor.execute("""
            INSERT INTO ventas (fecha, cliente, subtotal, impuesto, descuento, total_venta, metodo_pago, productos_detalles, utilidad_generada)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (fecha_actual, cliente, subtotal, imp_total, desc_total, total_neto, metodo, string_detalles.strip(), total_utilidad))
        
        conn.commit()
        return True, "Transacción finalizada con éxito."
    except Exception as e:
        conn.rollback()
        return False, f"Error: {str(e)}"
    finally:
        conn.close()

def render_modulo_ventas():
    aplicar_estilo_luxury()
    inicializar_tabla_ventas()
    
    st.markdown("# 🛒 MÓDULO DE VENTAS Y FACTURACIÓN POS 🛒")
    
    if 'pos_cliente' not in st.session_state:
        st.session_state.pos_cliente = "Consumidor Final"
    if 'carrito' not in st.session_state: 
        st.session_state.carrito = []
    
    t1, t2, t3 = st.tabs(["🛒 Facturación POS", "🖨️ Historial u Homologación", "📊 Cierre de Caja"])
    
    lista_productos = obtener_productos_disponibles()
    
    with t1:
        if not lista_productos:
            st.warning("⚠️ Almacén sin existencias comercializables. Cargue stock en el módulo de Inventarios.")
        else:
            st.subheader("1. Datos Generales de Venta")
            
            st.session_state.pos_cliente = st.text_input("1. Nombre del Cliente:", value=st.session_state.pos_cliente, key="input_cliente_pos").strip()
            metodo_pago = st.selectbox("2. Método de Recaudo Asignado:", ["Efectivo", "Tarjeta de Débito", "Tarjeta de Crédito", "Transferencia Bancaria", "Nequi / Daviplata"], key="input_metodo_pos")
                
            st.write("---")
            st.subheader("2. Selección de Productos")
            
            opciones_prod = {p[0]: f"{p[1]} (Disponibles: {p[2]} | Costo Base: ${seguro_int(p[3]):,.0f})" for p in lista_productos}
            prod_seleccionado = st.selectbox("3. Seleccione el artículo:", options=list(opciones_prod.keys()), format_func=lambda x: opciones_prod[x], key="input_prod_pos")
            
            sku, nombre_p, stock_p, costo_p = [p for p in lista_productos if p[0] == prod_seleccionado][0]
            
            col_ca, col_pr = st.columns(2)
            with col_ca: 
                cant_v = st.number_input("4. Unidades a vender:", min_value=1, max_value=int(stock_p), step=1, value=1, key="input_cant_pos")
            with col_pr: 
                precio_v = st.number_input("5. Precio Venta Comercial ($):", min_value=0, step=500, value=seguro_int(costo_p * 1.3), key="input_precio_pos")
                
            if st.button("➕ Agregar al Carrito POS"):
                encontrado = False
                for item in st.session_state.carrito:
                    if item['codigo'] == sku:
                        if (item['cantidad'] + cant_v) <= stock_p:
                            item['cantidad'] += cant_v
                            item['subtotal'] = item['cantidad'] * item['precio_v']
                            encontrado = True
                        else:
                            st.error("Error: Excede las existencias físicas en bodega.")
                            encontrado = True
                
                if not encontrado:
                    st.session_state.carrito.append({
                        'codigo': sku, 'nombre': nombre_p, 'cantidad': cant_v, 'precio_v': precio_v, 'subtotal': cant_v * precio_v
                    })
                st.toast(f"¡{nombre_p} añadido al carrito!")
                
            if st.session_state.carrito:
                st.write("---")
                st.subheader("🛒 Resumen Analítico de Compra")
                df_cart = pd.DataFrame(st.session_state.carrito)
                st.dataframe(df_cart[['nombre', 'cantidad', 'precio_v', 'subtotal']], use_container_width=True, hide_index=True)
                
                st.write("### ⚙️ Modificadores Comerciales")
                col_desc, col_imp = st.columns(2)
                with col_desc: 
                    tipo_desc = st.radio("Tipo Descuento:", ["Sin Descuento", "Porcentaje (%)", "Valor Fijo ($)"], horizontal=True)
                    val_desc = st.number_input("Monto / Escala:", min_value=0.0, value=0.0)
                with col_imp:
                    tipo_iva = st.selectbox("Tasa Impositiva (IVA):", ["Exento (0%)", "IVA General (19%)", "IVA Reducido (8%)"])

                subtotal_neto = df_cart['subtotal'].sum()
                
                if tipo_desc == "Porcentaje (%)": desc_total = (subtotal_neto * val_desc) / 100
                elif tipo_desc == "Valor Fijo ($)": desc_total = val_desc
                else: desc_total = 0.0
                
                if tipo_iva == "IVA General (19%)": imp_total = (subtotal_neto - desc_total) * 0.19
                elif tipo_iva == "IVA Reducido (8%)": imp_total = (subtotal_neto - desc_total) * 0.08
                else: imp_total = 0.0
                
                total_final = (subtotal_neto - desc_total) + imp_total
                
                st.markdown(f"""
                    <div class='pos-card'>
                        <p style='margin:2px;'><b>Subtotal Neto:</b> ${seguro_int(subtotal_neto):,.0f} COP</p>
                        <p style='margin:2px; color:#FF5555;'><b>Descuentos Consolidado:</b> -${seguro_int(desc_total):,.0f} COP</p>
                        <p style='margin:2px; color:#D4AF37;'><b>Gravamen Liquidado:</b> +${seguro_int(imp_total):,.0f} COP</p>
                        <h2 style='color:#55FF55; margin:5px 0;'>TOTAL GENERAL: ${seguro_int(total_final):,.0f} COP</h2>
                    </div>
                """, unsafe_allow_html=True)
                
                pago_recibido = st.number_input("Dinero Recibido en Caja ($):", min_value=0, value=seguro_int(total_final))
                if pago_recibido >= total_final:
                    st.success(f"💵 Vueltos / Cambio Técnico: **${seguro_int(pago_recibido - total_final):,.0f} COP**")
                else:
                    st.warning("⚠️ Monto insuficiente para cerrar la transacción.")

                st.write("---")
                st.subheader("🔒 Panel de Confirmación Obligatorio")
                confirmar_accion = st.checkbox("CONVENIO DE SEGURIDAD: Certifico que los datos de facturación son correctos y deseo guardar la venta.")

                col_accion1, col_accion2 = st.columns(2)
                with col_accion1:
                    if pago_recibido >= total_final:
                        if st.button("🚀 CERRAR VENTA Y GUARDAR COMPROBANTE"):
                            if confirmar_accion:
                                string_factura_instantanea = f"{'CANT':<5} {'DESCRIPCIÓN':<20} {'VALOR TOT':>12}\n"
                                string_factura_instantanea += "-" * 39 + "\n"
                                for item in st.session_state.carrito:
                                    nom_rec = item['nombre'][:19]
                                    v_tot = item['subtotal']
                                    string_factura_instantanea += f"{item['cantidad']:<5} {nom_rec:<20} ${v_tot:>11,.0f}\n"
                                
                                fecha_instantanea = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                
                                exito, msg = procesar_factura_completa(st.session_state.pos_cliente, metodo_pago, st.session_state.carrito, subtotal_neto, imp_total, desc_total, total_final)
                                if exito:
                                    st.success(msg)
                                    
                                    # REPARACIÓN EFECTUADA: Se eliminó el parámetro key que causaba el fallo crítico en PC
                                    st.markdown(f"""
                                    <div class="factura-premium">
                                        <div class="factura-header">
                                            <div class="factura-logo">⚜️ MYU LUXURY GOLD ⚜️</div>
                                            <div class="factura-sub">Servicio Exclusivo & Alta Gama</div>
                                        </div>
                                        
                                        <div class="factura-meta">
                                            <b>COMPROBANTE N°:</b> (Guardado Exitosamente)<br>
                                            <b>FECHA EMISIÓN:</b> {fecha_instantanea}<br>
                                            <b>CLIENTE:</b> {str(st.session_state.pos_cliente).upper()}<br>
                                            <b>MÉTODO PAGO:</b> {metodo_pago}<br>
                                        </div>
                                        
                                        <div class="factura-tabla-header">---------------------------------------</div>
                                        <div class="factura-items">{string_factura_instantanea}</div>
                                        
                                        <div class="factura-totales">
                                            Subtotal Bruto: ${seguro_int(subtotal_neto):,.0f} COP<br>
                                            Descuentos: -${seguro_int(desc_total):,.0f} COP<br>
                                            Impuestos Retenidos: +${seguro_int(imp_total):,.0f} COP<br>
                                            <div class="factura-total-destacado">TOTAL NETO: ${seguro_int(total_final):,.0f} COP</div>
                                        </div>
                                        
                                        <div class="factura-footer">
                                            Soporte de Operación Interna Offline Local.<br>
                                            ¡Gracias por su preferencia Premium!
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    st.session_state.carrito = []
                                    st.session_state.pos_cliente = "Consumidor Final"
                                    
                                    if st.button("🔄 Comenzar Nueva Facturación"):
                                        st.rerun()
                                else: st.error(msg)
                            else:
                                st.error("🚨 Debes marcar la casilla de confirmation obligatoria para procesar la venta.")
                with col_accion2:
                    if st.button("🧹 Descartar / Vaciar Carrito"):
                        if confirmar_accion:
                            st.session_state.carrito = []
                            st.session_state.pos_cliente = "Consumidor Final"
                            st.rerun()
                        else:
                            st.error("🚨 Marcar la casilla de confirmación para autorizar el vaciado del carrito.")

    with t2:
        st.subheader("Despacho Multi-canal de Comprobantes")
        tiene_internet = st.toggle("🌐 Estado de Conexión de Red (Simular Online)", value=True)
        
        conn = conectar_db()
        try:
            df_ventas = pd.read_sql_query("SELECT id, fecha, cliente, total_venta, metodo_pago, productos_detalles, impuesto, descuento, subtotal FROM ventas ORDER BY id DESC LIMIT 15", conn)
        except Exception:
            df_ventas = pd.DataFrame()
        conn.close()
        
        if not df_ventas.empty:
            opciones_historial = {row['id']: f"Factura #{row['id']} - {row['cliente']} (${seguro_int(row['total_venta']):,.0f})" for _, row in df_ventas.iterrows()}
            id_sel = st.selectbox("Seleccione tiquete a despachar u homologar:", options=list(opciones_historial.keys()), format_func=lambda x: opciones_historial[x])
            
            factura_act = df_ventas[df_ventas['id'] == id_sel].iloc[0]
            
            subtotal_bruto_historial = seguro_int(factura_act['subtotal'])
            if subtotal_bruto_historial == 0:
                subtotal_bruto_historial = seguro_int(factura_act['total_venta']) - seguro_int(factura_act['impuesto']) + seguro_int(factura_act['descuento'])

            with st.container():
                # REPARACIÓN EFECTUADA: Se eliminó el parámetro key que causaba el fallo crítico en PC
                st.markdown(f"""
                <div class="factura-premium">
                    <div class="factura-header">
                        <div class="factura-logo">⚜️ MYU LUXURY GOLD ⚜️</div>
                        <div class="factura-sub">Servicio Exclusivo & Alta Gama</div>
                    </div>
                    
                    <div class="factura-meta">
                        <b>COMPROBANTE N°:</b> #000{factura_act['id']}<br>
                        <b>FECHA EMISIÓN:</b> {factura_act['fecha']}<br>
                        <b>CLIENTE:</b> {str(factura_act['cliente']).upper()}<br>
                        <b>MÉTODO PAGO:</b> {factura_act['metodo_pago']}<br>
                    </div>
                    
                    <div class="factura-tabla-header">---------------------------------------</div>
                    <div class="factura-items">{factura_act['productos_detalles']}</div>
                    
                    <div class="factura-totales">
                        Subtotal Bruto: ${subtotal_bruto_historial:,.0f} COP<br>
                        Descuentos: -${seguro_int(factura_act['descuento']):,.0f} COP<br>
                        Impuestos Retenidos: +${seguro_int(factura_act['impuesto']):,.0f} COP<br>
                        <div class="factura-total-destacado">TOTAL NETO: ${seguro_int(factura_act['total_venta']):,.0f} COP</div>
                    </div>
                    
                    <div class="factura-footer">
                        Soporte de Operación Interna Offline Local.<br>
                        ¡Gracias por su preferencia Premium!
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            col_en1, col_en2 = st.columns(2)
            with col_en1: c_celular = st.text_input("Celular del Destinatario:", value="57")
            with col_en2: c_correo = st.text_input("Correo del Destinatario:", value="cliente@luxury.com")
            
            cuerpo_texto = f"⚜️ MYU LUXURY GOLD ⚜️\nFactura: #{factura_act['id']}\nCliente: {factura_act['cliente']}\nTotal Pagado: ${seguro_int(factura_act['total_venta']):,.0f} COP."
            texto_url = urllib.parse.quote(cuerpo_texto)
            
            col_b1, col_b2, col_b3, col_b4 = st.columns(4)
            with col_b1: st.markdown('<button onclick="window.print()" style="width:100%; padding:10px; background-color:#D4AF37; border:none; font-weight:bold; color:black; cursor:pointer; border-radius:4px;">🖨️ Imprimir</button>', unsafe_allow_html=True)
            with col_b2:
                if tiene_internet: st.markdown(f'<a href="https://wa.me/{c_celular}?text={texto_url}" target="_blank"><button style="width:100%; padding:10px; background-color:#25D366; border:none; font-weight:bold; color:white; border-radius:4px; cursor:pointer;">💬 WhatsApp</button></a>', unsafe_allow_html=True)
                else: st.button("💬 WhatsApp", disabled=True)
            with col_b3:
                if tiene_internet: st.markdown(f'<a href="mailto:{c_correo}?subject=Factura%20{factura_act["id"]}&body={texto_url}"><button style="width:100%; padding:10px; background-color:#0078D4; border:none; font-weight:bold; color:white; border-radius:4px; cursor:pointer;">📧 Correo</button></a>', unsafe_allow_html=True)
                else: st.button("📧 Correo", disabled=True)
            with col_b4:
                if tiene_internet: st.markdown(f'<a href="sms:{c_celular}?body={texto_url}"><button style="width:100%; padding:10px; background-color:#E119B1; border:none; font-weight:bold; color:white; border-radius:4px; cursor:pointer;">📱 SMS</button></a>', unsafe_allow_html=True)
                else: st.button("📱 SMS", disabled=True)
        else:
            st.info("Sin registros en el libro fiscal.")

    with t3:
        st.subheader("📊 Auditoría de Arqueo y Caja Diaria")
        conn = conectar_db()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*), TOTAL(total_venta), TOTAL(impuesto), TOTAL(descuento) FROM ventas")
            cant_v, sum_tot, sum_imp, sum_desc = cursor.fetchone()
            cursor.execute("SELECT metodo_pago, TOTAL(total_venta) FROM ventas GROUP BY metodo_pago")
            medios_data = cursor.fetchall()
        except Exception:
            cant_v, sum_tot, sum_imp, sum_desc = 0, 0, 0, 0
            medios_data = []
        conn.close()
        
        st.markdown(f"""
            <div class='pos-card' style='border-left: 4px solid #D4AF37;'>
                <p style='margin:3px; font-size:14px; color:#aaa;'>TIQUETES EXPEDIDOS EN TURNO</p>
                <h3 style='margin:2px; color:#FFF;'>{seguro_int(cant_v)} Operaciones</h3>
                <p style='margin:15px 0 3px 0; font-size:14px; color:#aaa;'>RECAUDO BRUTO EN ENTORNO LOCAL</p>
                <h2 style='margin:2px; color:#55FF55;'>${seguro_int(sum_tot):,.0f} COP</h2>
                <small style='color:#888;'>Impuestos retenidos: ${seguro_int(sum_imp):,.0f} | Concesiones por descuento: ${seguro_int(sum_desc):,.0f}</small>
            </div>
        """, unsafe_allow_html=True)
        
        st.write("#### 💳 Validation Cruzada por Medios de Pago")
        if medios_data:
            df_medios = pd.DataFrame(medios_data, columns=["Medio de Recaudo", "Monto Consolidado ($)"])
            st.table(df_medios)
        else:
            st.info("No se registran arqueos parciales.")