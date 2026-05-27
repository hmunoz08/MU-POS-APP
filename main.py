import streamlit as st
import sqlite3
import os
import shutil
import pandas as pd
from datetime import datetime

# 1. Configuración inicial de la página (Primer comando obligatorio)
st.set_page_config(page_title="MYU Luxury Gold", page_icon="⚜️", layout="wide")

# ==========================================
# RESPALDO AUTOMÁTICO DE SEGURIDAD (OFFLINE)
# ==========================================
def realizar_backup_local():
    # CORRECCIÓN: Apuntar al archivo centralizado correcto del sistema para los backups
    origen = 'syscafecopia.db'
    if not os.path.exists('backups_seguridad'):
        # REPARACIÓN: exist_ok=True evita que la app colapse en Streamlit Cloud si la carpeta ya existe
        os.makedirs('backups_seguridad', exist_ok=True)
    if os.path.exists(origen):
        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
        destino = f'backups_seguridad/backup_{fecha_hoy}.db'
        if not os.path.exists(destino):
            shutil.copy2(origen, destino)

# Ejecutar respaldo automático al iniciar
realizar_backup_local()

# 2. IMPORTACIONES DE MÓDULOS DEL SISTEMA
from login import mostrar_pantalla_login
from inventario import render_modulo_inventario
from ventas import render_modulo_ventas
from contabilidad import render_modulo_contabilidad
from personal import render_modulo_personal

# 3. CONTROLADOR DE ESTADO DE SESIÓN
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
if 'usuario_actual' not in st.session_state:
    st.session_state.usuario_actual = None
if 'rol_actual' not in st.session_state:
    st.session_state.rol_actual = None

# 4. ENRUTADOR MAESTRO Y VALIDACIÓN DE ACCESO
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
    options_menu = []
    if rol == "Administrador":
        opciones_menu = [
            "📦 1. Almacén e Inventarios", 
            "💵 2. Caja y Punto de Venta (POS)", 
            "👥 3. Control de Personal y Nómina",
            "📊 4. Balance General y Contabilidad"
        ]
    elif rol == "Cajero":
        opciones_menu = ["💵 2. Caja y Punto de Venta (POS)"]
    elif rol == "Bodeguero":
        opciones_menu = ["📦 1. Almacén e Inventarios"]

    # Selector de Entorno Operativo
    modulo_maestro = st.sidebar.selectbox("Seleccione el Frente Operativo:", opciones_menu)
    st.sidebar.write("---")
    
    if st.sidebar.button("🔒 Cerrar Sesión Segura", use_container_width=True):
        st.session_state.autenticado = False
        st.session_state.usuario_actual = None
        st.session_state.rol_actual = None
        st.rerun()

    # ==========================================
    # ENRUTAMIENTO DIRECTO SIN COMPONENTES DUPLICADOS
    # ==========================================
    if "1. Almacén e Inventarios" in modulo_maestro:
        render_modulo_inventario()
        
    elif "2. Caja y Punto de Venta (POS)" in modulo_maestro:
        render_modulo_ventas()
        
    elif "3. Control de Personal y Nómina" in modulo_maestro:
        render_modulo_personal()
        
    elif "4. Balance General y Contabilidad" in modulo_maestro:
        render_modulo_contabilidad()