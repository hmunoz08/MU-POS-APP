import streamlit as st
import sqlite3
import time
from datetime import datetime

def inicializar_tabla_usuarios():
    """Crea la tabla de usuarios con todos sus campos necesarios si no existe en la base de datos"""
    conn = sqlite3.connect('syscafecopia.db')
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios_sistema (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT NOT NULL UNIQUE,
            contrasena TEXT NOT NULL,
            rol TEXT NOT NULL,
            pregunta_secreta TEXT,
            respuesta_secreta TEXT
        )
    """)
    # Si la tabla está vacía, creamos el usuario administrador inicial con sus preguntas base
    cursor.execute("SELECT COUNT(*) FROM usuarios_sistema")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO usuarios_sistema (usuario, contrasena, rol, pregunta_secreta, respuesta_secreta) 
            VALUES (?, ?, ?, ?, ?)
        """, ("admin", "admin123", "Administrador", "¿nombre de tu primera mascota?", "firu"))
    conn.commit()
    conn.close()

def mostrar_pantalla_login():
    # Garantiza que la tabla exista antes de que ocurra cualquier interacción o consulta
    inicializar_tabla_usuarios()

    # Si ya está autenticado en la sesión actual, saltar login
    if st.session_state.get('autenticado', False):
        return True

    # Saludo dinámico según la hora local de la máquina
    hora_actual = datetime.now().hour
    if hora_actual < 12:
        saludo = "✨ BUENOS DÍAS • BIENVENIDO"
    elif hora_actual < 18:
        saludo = "⚜️ BUENAS TARDES • BIENVENIDO"
    else:
        saludo = "🌌 BUENAS NOCHES • BIENVENIDO"

    # Indicador de Estado de Servidor Local
    st.markdown(f"""
        <div style="display: flex; justify-content: space-between; background-color: #161616; padding: 6px 15px; border-radius: 4px; border-left: 3px solid #D4AF37; margin-bottom: 20px;">
            <span style="color: #D4AF37; font-size: 11px; font-family: monospace; font-weight: bold;">{saludo}</span>
            <span style="color: #55FF55; font-size: 11px; font-family: monospace;">● NÚCLEO OFFLINE ACTIVO</span>
        </div>
    """, unsafe_allow_html=True)

    # Estilo Premium para la interfaz de Acceso
    st.markdown("""
        <style>
        .login-box {
            background-color: #111111;
            padding: 35px;
            border-radius: 10px;
            border: 2px solid #D4AF37;
            max-width: 450px;
            margin: 20px auto 40px auto;
            text-align: center;
            box-shadow: 0px 4px 20px rgba(212, 175, 55, 0.15);
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="login-box"><h1 style="color:#D4AF37; margin:0;">⚜️ MYU LUXURY GOLD ⚜️</h1><p style="color:#888;">Control de Acceso Local Sólido</p></div>', unsafe_allow_html=True)

    pestana_login, pestana_recuperar = st.tabs(["🔑 Iniciar Sesión", "🔄 Olvidé mi Contraseña"])

    with pestana_login:
        # REPARACIÓN: Dejar el toggle externo alineado correctamente con el formulario nativo
        revelar_password = st.toggle("👁️ Mostrar caracteres de contraseña", value=False, key="toggle_show_pass")

        with st.form("formulario_login_premium", clear_on_submit=False):
            input_usuario = st.text_input("Usuario Operador [Enter]:", key="login_user").strip()
            
            # REPARACIÓN: Enrutamiento seguro del tipo de input sin romper la estructura del form
            tipo_input = "default" if revelar_password else "password"
            input_pass = st.text_input("Contraseña Criptográfica [Enter]:", type=tipo_input, key="login_pass_input")
            
            boton_ingresar = st.form_submit_button("🚀 Ingresar al Sistema", use_container_width=True)
            
            if boton_ingresar:
                # Efecto de carga premium antes de validar
                with st.spinner("Verificando firma criptográfica local..."):
                    time.sleep(0.4) 
                    
                    conn = sqlite3.connect('syscafecopia.db')
                    cursor = conn.cursor()
                    cursor.execute("SELECT rol FROM usuarios_sistema WHERE usuario = ? AND contrasena = ?", (input_usuario, input_pass))
                    resultado = cursor.fetchone()
                    conn.close()

                if resultado:
                    st.session_state.autenticado = True
                    st.session_state.usuario_actual = input_usuario
                    st.session_state.rol_actual = resultado[0]
                    st.success(f"Acceso concedido. Rol: {resultado[0]}")
                    st.rerun()
                else:
                    st.error("❌ Credenciales incorrectas o usuario inexistente localmente.")

    with pestana_recuperar:
        st.subheader("Auto-Recuperación de Seguridad")
        user_recuperar = st.text_input("Ingresa tu nombre de Usuario:", key="rec_user").strip()
        
        if user_recuperar:
            conn = sqlite3.connect('syscafecopia.db')
            cursor = conn.cursor()
            cursor.execute("SELECT pregunta_secreta, respuesta_secreta FROM usuarios_sistema WHERE usuario = ?", (user_recuperar,))
            datos_usuario = cursor.fetchone()
            conn.close()
            
            if datos_usuario:
                pregunta, respuesta_correcta = datos_usuario
                st.info(f"**Pregunta de Seguridad:** {pregunta}")
                
                with st.form("formulario_recuperacion_premium"):
                    respuesta_usuario = st.text_input("Tu Respuesta Secreta [Enter]:", key="rec_resp").strip().lower()
                    nueva_pass_temporal = st.text_input("Establece tu Nueva Contraseña [Enter]:", type="password", key="rec_new_pass")
                    
                    boton_restablecer = st.form_submit_button("🛠️ Reestablecer Acceso Local", use_container_width=True)
                    
                    if boton_restablecer:
                        if respuesta_usuario == str(respuesta_correcta).strip().lower():
                            if nueva_pass_temporal:
                                conn = sqlite3.connect('syscafecopia.db')
                                cursor = conn.cursor()
                                cursor.execute("UPDATE usuarios_sistema SET contrasena = ? WHERE usuario = ?", (nueva_pass_temporal, user_recuperar))
                                conn.commit()
                                conn.close()
                                st.success("🔑 ¡Contraseña cambiada con éxito! Ya puedes iniciar sesión en la pestaña anterior.")
                            else:
                                st.error("Escribe la nueva contraseña que deseas asignar.")
                        else:
                            st.error("❌ La respuesta secreta no coincide.")
            else:
                st.error("El usuario ingresado no existe en esta máquina.")

    # Pie de página legal informativo
    st.markdown("""
        <div style="text-align: center; margin-top: 50px; padding-top: 15px; border-top: 1px solid #1A1A1A;">
            <small style="color: #444; font-size: 11px;">
                MYU Luxury Gold Terminal POS • Sistema Autónomo Protegido sin Conexión Externa.
            </small>
        </div>
    """, unsafe_allow_html=True)
                
    return False