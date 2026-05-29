import os
import sys
import streamlit.web.cli as stcli

def resolver_ruta(ruta_relativa):
    """ Obtiene la ruta absoluta para los recursos incluidos en el ejecutable """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, ruta_relativa)
    return os.path.join(os.path.abspath("."), ruta_relativa)

if __name__ == "__main__":
    # Apunta directamente al archivo principal de tu aplicación
    archivo_main = resolver_ruta("main.py")
    
    # Configura los argumentos para emular el comando 'streamlit run main.py'
    sys.argv = ["streamlit", "run", archivo_main, "--global.developmentMode=false"]
    
    # Lanza el servidor de Streamlit
    sys.exit(stcli.main())