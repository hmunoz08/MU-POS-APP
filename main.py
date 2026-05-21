import streamlit as st
import sqlite3

# 1. Configuración inicial de la página (Primer comando obligatorio)
st.set_page_config(page_title="MYU Luxury Gold", page_icon="⚜️", layout="wide")

# 2. IMPORTACIONES DE MÓDULOS DEL SISTEMA
from login import mostrar_pantalla_login

# Frentes operativos locales independientes
from inventario import render_modulo_inventario
from ventas import render_modulo_ventas
from personal import render_modulo_personal
from contabilidad import render_modulo_contabilidad

# 3. BASE DE DATOS LOCAL CON MIGRACIÓN INTEGRAL (Evita el error de columna faltante)
def inicializar_base_seguridad():
    conn = sqlite3.connect('sistema_negocio.db')
    cursor = conn.cursor()
    
    # Validamos si la tabla vieja existe y tiene la estructura correcta. 
    # Si no tiene la columna 'usuario', la reiniciamos de forma segura.
    try:
        cursor.execute("SELECT usuario FROM usuarios_sistema LIMIT 1")
    except sqlite3.OperationalError:
        # Si da error porque la tabla no existe o es vieja, la borramos para crearla limpia
        cursor.execute("DROP TABLE IF EXISTS usuarios_sistema")
    
    # Crear tabla de usuarios definitiva
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios_sistema (
            usuario TEXT PRIMARY KEY,
            contrasena TEXT NOT NULL,
            rol TEXT NOT NULL,
            pregunta_secreta TEXT,
            respuesta_secreta TEXT
        )
    """)
    
    # Insertar usuario administrador por defecto si la tabla está vacía
    cursor.execute("SELECT COUNT(*) FROM usuarios_sistema")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO usuarios_sistema (usuario, contrasena, rol, pregunta_secreta, respuesta_secreta)
            VALUES ('admin', 'admin123', 'Administrador', '¿Nombre de tu primera mascota?', 'lucas')
        """)
    
    # Tabla para persistencia del Carrito de Ventas (Resistente a F5)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS carrito_recuperable (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT NOT NULL,
            codigo TEXT NOT NULL,
            nombre TEXT NOT NULL,
            cantidad INTEGER NOT NULL,
            precio_v REAL NOT NULL,
            subtotal REAL NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# Ejecutar inicialización local al arrancar
inicializar_base_seguridad()

# 4. CONTROLADOR DE ESTADO DE SESIÓN
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
if 'usuario_actual' not in st.session_state:
    st.session_state.usuario_actual = None
if 'rol_actual' not in st.session_state:
    st.session_state.rol_actual = None

# 5. ENRUTADOR MAESTRO Y VALIDACIÓN DE ACCESO
def ejecutar_aplicacion():
    if mostrar_pantalla_login():
        usuario = st.session_state.usuario_actual
        rol = st.session_state.rol_actual

        # ==========================================
        # BARRA LATERAL (SIDEBAR) - ESTÉTICA LUXURY
        # ==========================================
        st.sidebar.markdown("<h1 style='text-align:center; font-size: 24px; color:#D4AF37; margin-bottom:0;'>⚜️ PREMIUM SYSTEM ⚜️</h1>", unsafe_allow_html=True)
        st.sidebar.markdown(f"<p style='text-align:center; color:#55FF55; font-size:13px; margin-top:5px;'>👤 OPERADOR: {usuario.upper()}<br><span style='color:#aaa; font-size:11px;'>Cargo: {rol}</span></p>", unsafe_allow_html=True)
        st.sidebar.write("---")

        # Matriz de menús por Roles de Trabajo
        opciones_menu = []
        if rol == "Administrador":
            opciones_menu = [
                "📦 1. Almacén e Inventarios", 
                "💵 2. Caja y Punto de Venta (POS)", 
                "👥 3. Control de Personal y Nómina",
                "📊 4. Balance General y Contabilidad",
                "⚙️ 5. Configuración de Seguridad"
            ]
        elif rol == "Cajero":
            opciones_menu = ["💵 2. Caja y Punto de Venta (POS)", "⚙️ 5. Configuración de Seguridad"]
            st.sidebar.info("🔒 Menú restringido al área de Ventas.")
        elif rol == "Bodeguero":
            opciones_menu = ["📦 1. Almacén e Inventarios", "⚙️ 5. Configuración de Seguridad"]
            st.sidebar.info("🔒 Menú restringido a la Gestión de Almacén.")

        # Selector de Entorno Operativo
        modulo_maestro = st.sidebar.selectbox("Seleccione el Frente Operativo:", opciones_menu)
        st.sidebar.write("---")
        
        # Interruptor de Cierre de Sesión
        if st.sidebar.button("🔒 Cerrar Sesión Segura", use_container_width=True):
            st.session_state.autenticado = False
            st.session_state.usuario_actual = None
            st.session_state.rol_actual = None
            st.rerun()

        # ==========================================
        # ENRUTAMIENTO LOGÍSTICO DE PANTALLAS
        # ==========================================
        if modulo_maestro == "📦 1. Almacén e Inventarios":
            render_modulo_inventario()
            
        elif modulo_maestro == "💵 2. Caja y Punto de Venta (POS)":
            render_modulo_ventas()
            
        elif modulo_maestro == "👥 3. Control de Personal y Nómina":
            render_modulo_personal()
            
        elif modulo_maestro == "📊 4. Balance General y Contabilidad":
            render_modulo_contabilidad()
            
        elif modulo_maestro == "⚙️ 5. Configuración de Seguridad":
            st.title("⚙️ CONFIGURACIÓN DE CREDENCIALES")
            st.write("---")
            st.subheader("Modificar Pregunta Secreta y Contraseña")
            
            nueva_pass = st.text_input("Nueva Contraseña:", type="password")
            nueva_preg = st.selectbox("Selecciona tu Pregunta Secreta:", [
                "¿Nombre de tu primera mascota?",
                "¿Ciudad donde nacieron tus padres?",
                "¿Nombre de tu escuela primaria?",
                "¿Marca de tu primer carro / moto?"
            ])
            nueva_resp = st.text_input("Respuesta Secreta (En minúsculas):").strip().lower()
            
            if st.button("💾 Actualizar mis Datos de Seguridad"):
                if nueva_pass and nueva_resp:
                    conn = sqlite3.connect('sistema_negocio.db')
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE usuarios_sistema 
                        SET contrasena = ?, pregunta_secreta = ?, respuesta_secreta = ? 
                        WHERE usuario = ?
                    """, (nueva_pass, nueva_preg, nueva_resp, usuario))
                    conn.commit()
                    conn.close()
                    st.success("¡Credenciales locales actualizadas con éxito!")
                else:
                    st.error("Por favor completa la contraseña y la respuesta secreta.")

if __name__ == '__main__':
    ejecutar_application = ejecutar_aplicacion()