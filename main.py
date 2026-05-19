import streamlit as st  # <--- ESTA LÍNEA ES CRÍTICA PARA REPARAR EL ERROR DE LA IMAGEN 1
import sqlite3
from ventas import render_modulo_ventas
from inventario import render_modulo_inventario
from personal import render_modulo_personal

# Configuración inicial de la página (Debe ser el primer comando de Streamlit)
st.set_page_config(page_title="MYU Luxury Gold", page_icon="⚜️", layout="wide")

# ... (El resto de tu código de navegación de menús)
# 2. IMPORTACIONES DE MÓDULOS DEL SISTEMA
# Guardián de seguridad criptográfica y autenticación
from login import mostrar_pantalla_login

# Frentes operativos locales independientes
from inventario import render_modulo_inventario
from ventas import render_modulo_ventas
from personal import render_modulo_personal
from contabilidad import render_modulo_contabilidad

# 3. CONTROLADOR DE ESTADO DE SESIÓN (Garantiza estabilidad ante F5/Refrescos)
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
if 'usuario_actual' not in st.session_state:
    st.session_state.usuario_actual = None
if 'rol_actual' not in st.session_state:
    st.session_state.rol_actual = None

# 4. ENRUTADOR MAESTRO Y VALIDACIÓN DE ACCESO
# La función 'mostrar_pantalla_login' dibuja el login o la pantalla de cambio obligatorio.
# Retorna True únicamente si el usuario está validado, libre de bloqueos y listo para operar.
if mostrar_pantalla_login():
    
    usuario = st.session_state.usuario_actual
    rol = st.session_state.rol_actual

    # ==========================================
    # BARRA LATERAL (SIDEBAR) - ESTÉTICA LUXURY
    # ==========================================
    st.sidebar.markdown("<h1 style='text-align:center; font-size: 24px; color:#D4AF37; margin-bottom:0;'>⚜️ PREMIUM SYSTEM ⚜️</h1>", unsafe_allow_html=True)
    st.sidebar.markdown(f"<p style='text-align:center; color:#55FF55; font-size:13px; margin-top:5px;'>👤 OPERADOR: {usuario.upper()}<br><span style='color:#aaa; font-size:11px;'>Cargo: {rol}</span></p>", unsafe_allow_html=True)
    st.sidebar.write("---")

    # Matriz estricta de segmentación de menús por Roles de Trabajo
    opciones_menu = []
    if rol == "Administrador":
        opciones_menu = [
            "📦 1. Almacén e Inventarios", 
            "💵 2. Caja y Punto de Venta (POS)", 
            "👥 3. Control de Personal y Nómina",
            "📊 4. Balance General y Contabilidad"
        ]
    elif rol == "Cajero":
        opciones_menu = ["💵 2. Caja y Punto de Venta (POS)"]
        st.sidebar.info("🔒 Menú restringido exclusivamente al área de Ventas y Facturación.")
    elif rol == "Bodeguero":
        opciones_menu = ["📦 1. Almacén e Inventarios"]
        st.sidebar.info("🔒 Menú restringido exclusivamente a la Gestión de Almacén.")

    # Selector de Entorno Operativo
    modulo_maestro = st.sidebar.selectbox("Seleccione el Frente Operativo:", opciones_menu)
    st.sidebar.write("---")
    
    # Interruptor seguro de Cierre de Sesión (Destruye variables de entorno)
    if st.sidebar.button("🔒 Cerrar Sesión Segura", use_container_width=True):
        st.session_state.autenticado = False
        st.session_state.usuario_actual = None
        st.session_state.rol_actual = None
        st.session_state.bloqueo_primer_ingreso = False
        st.rerun()

    # ==========================================
    # ENRUTAMIENTO LOGÍSITICO DE PANTALLAS
    # ==========================================
    if modulo_maestro == "📦 1. Almacén e Inventarios":
        render_modulo_inventario()
        
    elif modulo_maestro == "💵 2. Caja y Punto de Venta (POS)":
        render_modulo_ventas()
        
    elif modulo_maestro == "👥 3. Control de Personal y Nómina":
        render_modulo_personal()
        
    elif modulo_maestro == "📊 4. Balance General y Contabilidad":
        render_modulo_contabilidad()