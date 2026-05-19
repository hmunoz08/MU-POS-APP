import streamlit as st
import sqlite3
import hashlib

def aplicar_estilo_luxury():
    st.markdown("""
        <style>
        .stApp { background-color: #0D0D0D; color: #E0E0E0; }
        h1, h2, h3, h4 { color: #D4AF37 !important; font-family: 'Playfair Display', serif; font-weight: 700; }
        .stButton>button {
            background-color: #D4AF37 !important; color: #000000 !important;
            font-weight: bold !important; border: 1px solid #D4AF37 !important;
            border-radius: 4px !important; width: 100% !important;
            padding: 10px !important;
        }
        .login-box {
            background-color: #161616; padding: 30px; border-radius: 8px;
            border: 1px solid #2A2415; max-width: 450px; margin: 0 auto;
        }
        </style>
    """, unsafe_allow_html=True)

def conectar_db():
    return sqlite3.connect('sistema_negocio.db')

def inicializar_tabla_usuarios():
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            rol TEXT NOT NULL,
            requiere_cambio INTEGER DEFAULT 0
        )
    """)
    try:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN requiere_cambio INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        usuarios_iniciales = [
            ('admin', hashlib.sha256('admin123'.encode()).hexdigest(), 'Administrador', 1),
            ('cajero', hashlib.sha256('caja123'.encode()).hexdigest(), 'Cajero', 1),
            ('bodega', hashlib.sha256('bodega123'.encode()).hexdigest(), 'Bodeguero', 1)
        ]
        cursor.executemany("INSERT INTO usuarios (username, password_hash, rol, requiere_cambio) VALUES (?, ?, ?, ?)", usuarios_iniciales)
        conn.commit()
    conn.close()

def actualizar_contrasena_usuario(username, nueva_pass):
    conn = conectar_db()
    cursor = conn.cursor()
    nuevo_hash = hashlib.sha256(nueva_pass.encode()).hexdigest()
    cursor.execute("UPDATE usuarios SET password_hash = ?, requiere_cambio = 0 WHERE username = ?", (nuevo_hash, username))
    conn.commit()
    conn.close()

def mostrar_pantalla_login():
    aplicar_estilo_luxury()
    inicializar_tabla_usuarios()
    
    if 'bloqueo_primer_ingreso' not in st.session_state:
        st.session_state.bloqueo_primer_ingreso = False

    if st.session_state.bloqueo_primer_ingreso:
        st.markdown("<h1 style='text-align:center; margin-top:50px;'>🔑 CAMBIO DE CONTRASEÑA OBLIGATORIO 🔑</h1>", unsafe_allow_html=True)
        with st.container():
            st.markdown("<div class='login-box'>", unsafe_allow_html=True)
            st.info(f"Usuario activo: {st.session_state.usuario_actual.upper()}")
            nueva_clave = st.text_input("Defina su nueva contraseña:", type="password").strip()
            confirmar_clave = st.text_input("Confirme su contraseña:", type="password").strip()
            
            if st.button("Guardar Nueva Clave Privada"):
                if not nueva_clave:
                    st.error("No puede estar vacía.")
                elif nueva_clave in ["admin123", "caja123", "bodega123"]:
                    st.error("No puede utilizar claves genéricas de fábrica.")
                elif nueva_clave != confirmar_clave:
                    st.error("Las contraseñas no coinciden.")
                else:
                    actualizar_contrasena_usuario(st.session_state.usuario_actual, nueva_clave)
                    st.session_state.bloqueo_primer_ingreso = False
                    st.session_state.autenticado = True
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        return False

    if not st.session_state.autenticado:
        st.markdown("<h1 style='text-align:center; margin-top:50px;'>⚜️ ACCESO AL SISTEMA PREMIUM ⚜️</h1>", unsafe_allow_html=True)
        with st.container():
            st.markdown("<div class='login-box'>", unsafe_allow_html=True)
            user_input = st.text_input("Usuario Corporativo:").strip()
            pass_input = st.text_input("Contraseña de Seguridad:", type="password").strip()
            
            if st.button("Validar Firma Digital"):
                if user_input and pass_input:
                    hash_comparar = hashlib.sha256(pass_input.encode()).hexdigest()
                    conn = conectar_db()
                    cursor = conn.cursor()
                    cursor.execute("SELECT rol, requiere_cambio FROM usuarios WHERE username = ? AND password_hash = ?", (user_input, hash_comparar))
                    resultado = cursor.fetchone()
                    conn.close()
                    
                    if resultado:
                        st.session_state.usuario_actual = user_input
                        st.session_state.rol_actual = resultado[0]
                        if resultado[1] == 1:
                            st.session_state.bloqueo_primer_ingreso = True
                        else:
                            st.session_state.autenticado = True
                        st.rerun()
                    else:
                        st.error("❌ Credenciales inválidas.")
            st.markdown("</div>", unsafe_allow_html=True)
        return False
    return True