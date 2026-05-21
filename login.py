import streamlit as st
import sqlite3

def mostrar_pantalla_login():
    # Si ya está autenticado en la sesión actual, saltar login
    if st.session_state.get('autenticado', False):
        return True

    # Estilo Premium para la interfaz de Acceso
    st.markdown("""
        <style>
        .login-box {
            background-color: #111111;
            padding: 35px;
            border-radius: 10px;
            border: 2px solid #D4AF37;
            max-width: 450px;
            margin: 50px auto;
            text-align: center;
            box-shadow: 0px 4px 20px rgba(212, 175, 55, 0.15);
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="login-box"><h1 style="color:#D4AF37; margin:0;">⚜️ MYU LUXURY GOLD ⚜️</h1><p style="color:#888;">Control de Acceso Local Sólido</p></div>', unsafe_allow_html=True)

    pestana_login, pestana_recuperar = st.tabs(["🔑 Iniciar Sesión", "🔄 Olvidé mi Contraseña"])

    with pestana_login:
        input_usuario = st.text_input("Usuario Operador:", key="login_user").strip()
        input_pass = st.text_input("Contraseña Criptográfica:", type="password", key="login_pass")
        
        if st.button("🚀 Ingresar al Sistema", use_container_width=True):
            conn = sqlite3.connect('sistema_negocio.db')
            cursor = conn.cursor()
            cursor.execute("SELECT rol FROM usuarios_sistema WHERE usuario = ? AND contrasena = ?", (input_usuario, input_pass))
            resultado = cursor.fetchone()
            conn.close()

            if resultado:
                st.session_state.autenticado = True
                st.session_state.usuario_actual = input_usuario
                st.session_state.rol_actual = resultado[0]
                st.success("Acceso concedido.")
                st.rerun()
            else:
                st.error("❌ Credenciales incorrectas o usuario inexistente localmente.")

    with pestana_recuperar:
        st.subheader("Auto-Recuperación de Seguridad")
        user_recuperar = st.text_input("Ingresa tu nombre de Usuario:", key="rec_user").strip()
        
        if user_recuperar:
            conn = sqlite3.connect('sistema_negocio.db')
            cursor = conn.cursor()
            cursor.execute("SELECT pregunta_secreta, respuesta_secreta FROM usuarios_sistema WHERE usuario = ?", (user_recuperar,))
            datos_usuario = cursor.fetchone()
            conn.close()
            
            if datos_usuario:
                pregunta, respuesta_correcta = datos_usuario
                st.info(f"**Pregunta de Seguridad:** {pregunta}")
                respuesta_usuario = st.text_input("Tu Respuesta Secreta:", key="rec_resp").strip().lower()
                
                nueva_pass_temporal = st.text_input("Establece tu Nueva Contraseña:", type="password", key="rec_new_pass")
                
                if st.button("🛠️ Reestablecer Acceso Local", use_container_width=True):
                    if respuesta_usuario == respuesta_correcta:
                        if nueva_pass_temporal:
                            conn = sqlite3.connect('sistema_negocio.db')
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
                
    return False