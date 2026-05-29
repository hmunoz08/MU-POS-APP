import streamlit as st
import sqlite3
import pandas as pd
import os
from datetime import datetime

def aplicar_estilo_luxury():
    st.markdown("""
        <style>
        .stApp { background-color: #0D0D0D; color: #E0E0E0; }
        h1, h2, h3, h4 { color: #D4AF37 !important; font-family: 'Playfair Display', serif; }
        .stButton>button { background-color: #161616 !important; color: #D4AF37 !important; border: 1px solid #2A2415 !important; font-weight: bold !important; height: 50px; width: 100%; }
        .stButton>button:hover { background-color: #D4AF37 !important; color: #000000 !important; }
        .calc-display { background-color: #161616; padding: 15px; border-radius: 8px; border: 1px solid #2A2415; text-align: right; font-size: 24px; color: #D4AF37; font-family: 'Courier New', monospace; margin-bottom: 10px; min-height: 65px; }
        </style>
    """, unsafe_allow_html=True)

def conectar_db():
    ruta_db = os.path.join(os.path.abspath("."), 'syscafecopia.db')
    return sqlite3.connect(ruta_db)

def inicializar_tabla_notas():
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notas_rapidas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            titulo TEXT NOT NULL,
            contenido TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def render_modulo_herramientas():
    aplicar_estilo_luxury()
    inicializar_tabla_notas()
    
    st.title("🛠️ PANEL DE HERRAMIENTAS AUXILIARES 🛠️")
    st.write("---")
    
    col_izq, col_der = st.columns([1.2, 0.8])
    
    # =========================================================================
    # COLUMNA IZQUIERDA: BLOC DE NOTAS CON LÁPIZ Y BOTÓN DE BASURA
    # =========================================================================
    with col_izq:
        st.subheader("📝 Bloc de Notas e Información Crítica")
        
        # Inicialización segura de estados búfer para el formulario de notas
        if "nota_titulo" not in st.session_state: st.session_state.nota_titulo = ""
        if "nota_contenido" not in st.session_state: st.session_state.nota_contenido = ""
        
        # Inputs para agregar nota nueva
        with st.expander("➕ Crear Nueva Nota / Guardar Código", expanded=False):
            tit = st.text_input("Título / Referencia:", value=st.session_state.nota_titulo, key="w_ntit_inp").strip()
            cont = st.text_area("Contenido de la nota (Códigos, RUT, Cuentas...):", value=st.session_state.nota_contenido, key="w_ncont_inp")
            
            if st.button("💾 Almacenar Nota", use_container_width=True):
                if not tit or not cont:
                    st.error("🚨 Complete el título y el cuerpo de la nota.")
                else:
                    conn = conectar_db()
                    fecha_h = datetime.now().strftime("%Y-%m-%d %H:%M")
                    conn.cursor().execute("INSERT INTO notas_rapidas (fecha, titulo, contenido) VALUES (?, ?, ?)", (fecha_h, tit, cont))
                    conn.commit()
                    conn.close()
                    st.success("📝 Nota guardada en el sistema.")
                    
                    # Limpieza segura de variables de estado sin romper la mutabilidad del widget
                    st.session_state.nota_titulo = ""
                    st.session_state.nota_contenido = ""
                    st.rerun()

        st.write(" ")
        st.caption("✏️ Edita directamente sobre la tabla. Marca 🗑️ y presiona el botón inferior para borrar.")
        
        # Visualización Interactiva de Notas existentes
        conn = conectar_db()
        df_notas = pd.read_sql_query("SELECT id, fecha AS 'Fecha', titulo AS 'Título', contenido AS 'Contenido / Código' FROM notas_rapidas ORDER BY id DESC", conn)
        conn.close()
        
        if not df_notas.empty:
            df_notas.insert(0, "🗑️", False)
            
            df_edit_notas = st.data_editor(
                df_notas,
                hide_index=True,
                use_container_width=True,
                disabled=["id", "Fecha"],
                column_config={
                    "🗑️": st.column_config.CheckboxColumn("🗑️", default=False),
                    "Título": st.column_config.TextColumn("Título", width="medium"),
                    "Contenido / Código": st.column_config.TextColumn("Contenido / Código", width="large")
                },
                key="editor_notas_inline"
            )
            
            if st.button("🔄 Aplicar Cambios ✏️ / Borrados 🗑️ en Notas", use_container_width=True):
                conn = conectar_db()
                cursor = conn.cursor()
                
                # 1. Bote de basura dinámico
                for _, fila in df_edit_notas[df_edit_notas["🗑️"] == True].iterrows():
                    cursor.execute("DELETE FROM notas_rapidas WHERE id = ?", (int(fila["id"]),))
                
                # 2. Lápiz de edición interactivo
                for _, fila in df_edit_notas[df_edit_notas["🗑️"] == False].iterrows():
                    cursor.execute("UPDATE notas_rapidas SET titulo = ?, contenido = ? WHERE id = ?", (fila["Título"], fila["Contenido / Código"], int(fila["id"])))
                
                conn.commit()
                conn.close()
                st.success("🔄 Notas actualizadas.")
                st.rerun()
        else:
            st.info("No tienes notas ni códigos guardados.")

    # =========================================================================
    # COLUMNA DERECHA: CALCULADORA COMPLETA E INTERACTIVA
    # =========================================================================
    with col_der:
        st.subheader("🧮 Calculadora de Caja")
        
        # Estado de la pantalla de la calculadora
        if "calc_input" not in st.session_state:
            st.session_state.calc_input = ""
            
        # Display de resultados
        st.markdown(f'<div class="calc-display">{st.session_state.calc_input if st.session_state.calc_input else "0"}</div>', unsafe_allow_html=True)
        
        # Mapeo y renderizado de los botones táctiles en Grid
        botones = [
            ["7", "8", "9", "/"],
            ["4", "5", "6", "*"],
            ["1", "2", "3", "-"],
            ["C", "0", ".", "+"],
            ["="]
        ]
        
        for fila in botones:
            if len(fila) == 4:
                c1, c2, c3, c4 = st.columns(4)
                with c1: 
                    if st.button(fila[0], key=f"btn_{fila[0]}"):
                        if fila[0] == "C": st.session_state.calc_input = ""
                        else: st.session_state.calc_input += fila[0]
                        st.rerun()
                with c2: 
                    if st.button(fila[1], key=f"btn_{fila[1]}"):
                        st.session_state.calc_input += fila[1]
                        st.rerun()
                with c3: 
                    if st.button(fila[2], key=f"btn_{fila[2]}"):
                        st.session_state.calc_input += fila[2]
                        st.rerun()
                with c4: 
                    if st.button(fila[3], key=f"btn_{fila[3]}"):
                        st.session_state.calc_input += fila[3]
                        st.rerun()
            else:
                # Botón de Igual que ocupa toda la fila inferior
                if st.button(fila[0], key="btn_igual"):
                    try:
                        # Evalúa la operación de forma matemática segura
                        resultado = eval(st.session_state.calc_input)
                        # Formatear si es flotante largo o entero
                        if isinstance(resultado, float) and resultado.is_integer():
                            resultado = int(resultado)
                        st.session_state.calc_input = str(resultado)
                    except Exception:
                        st.session_state.calc_input = "Error"
                    st.rerun()