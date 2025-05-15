# app.py - Versión para Streamlit Cloud
import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime

# Configuración de la página
st.set_page_config(
    page_title="Streamlit Cloud ↔ Colab",
    page_icon="🔄",
    layout="wide"
)

st.title("Conexión Streamlit Cloud ↔ Google Colab")
st.subheader("Integración completamente en la nube")

# Configuración de la URL de la API
# Esta URL se obtiene al ejecutar el código de la API en Colab
if "api_url" not in st.session_state:
    st.session_state.api_url = ""

# Almacenar resultados de las solicitudes
if "solicitudes" not in st.session_state:
    st.session_state.solicitudes = []

# Función para verificar la conexión a la API
def verificar_conexion(url):
    try:
        # Intentar conectar a la URL base
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            # Intentar la ruta específica de status
            status_response = requests.get(f"{url}/status", timeout=5)
            if status_response.status_code == 200:
                return True, "Conexión exitosa a la API de Colab", status_response.json()
            else:
                return False, f"Error en la ruta /status: {status_response.status_code}", None
        else:
            return False, f"Error al conectar: Código {response.status_code}", None
    except Exception as e:
        return False, f"Error de conexión: {str(e)}", None

# Función para enviar un número a la API de Colab
def procesar_en_colab(url, numero):
    try:
        # Preparar datos para enviar
        datos = {
            "numero": numero
        }
        
        # Realizar la solicitud POST a la API
        response = requests.post(
            f"{url}/procesar", 
            json=datos,
            timeout=10
        )
        
        # Verificar respuesta
        if response.status_code == 200:
            resultado = response.json()
            return True, resultado
        else:
            return False, f"Error: Código {response.status_code} - {response.text}"
            
    except Exception as e:
        return False, f"Error al procesar: {str(e)}"

# Sección para configurar la URL de la API
st.header("1. Configurar conexión con Colab")

with st.form("config_form"):
    api_url = st.text_input(
        "URL de la API de Colab (generada por ngrok)", 
        value=st.session_state.api_url,
        placeholder="https://xxxx-xx-xx-xxx-xx.ngrok.io"
    )
    
    submitted = st.form_submit_button("Guardar y verificar conexión")
    
    if submitted:
        if not api_url:
            st.error("Por favor, ingresa la URL de la API")
        else:
            # Verificar que la URL es válida
            if not api_url.startswith("http"):
                api_url = "https://" + api_url
            
            # Eliminar barra al final si existe
            if api_url.endswith("/"):
                api_url = api_url[:-1]
                
            # Intentar conectar a la API
            exito, mensaje, status_info = verificar_conexion(api_url)
            
            if exito:
                st.session_state.api_url = api_url
                st.success(mensaje)
                if status_info:
                    st.info(f"Servidor Colab activo desde: {status_info.get('timestamp', 'desconocido')}")
            else:
                st.error(mensaje)

# Sección para enviar solicitudes a Colab
st.header("2. Enviar número para procesar en Colab")

if st.session_state.api_url:
    with st.form("procesar_form"):
        numero = st.number_input("Número a procesar", min_value=1, max_value=1000, value=42)
        procesar_submitted = st.form_submit_button("Procesar en Colab")
        
        if procesar_submitted:
            with st.spinner("Conectando con Colab..."):
                exito, resultado = procesar_en_colab(st.session_state.api_url, numero)
                
                if exito:
                    # Guardar resultado en el historial
                    st.session_state.solicitudes.append({
                        "id": len(st.session_state.solicitudes) + 1,
                        "numero": numero,
                        "timestamp": datetime.now(),
                        "resultado": resultado
                    })
                    st.success("¡Procesamiento exitoso!")
                else:
                    st.error(f"Error al procesar: {resultado}")
else:
    st.info("Primero configura la URL de la API de Colab en el paso 1.")

# Mostrar resultados de las solicitudes
if st.session_state.solicitudes:
    st.header("3. Resultados procesados por Colab")
    
    for i, solicitud in enumerate(st.session_state.solicitudes):
        with st.expander(f"Solicitud {solicitud['id']}: Número {solicitud['numero']}", expanded=(i==len(st.session_state.solicitudes)-1)):
            st.write(f"Enviada: {solicitud['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
            
            resultado = solicitud['resultado']
            
            # Crear una tabla con los resultados
            df = pd.DataFrame({
                'Métrica': [
                    'Número original',
                    'Cuadrado',
                    'Raíz cuadrada',
                    'Doble',
                    'Mitad'
                ],
                'Valor': [
                    resultado.get('numero_original', 'N/A'),
                    resultado.get('cuadrado', 'N/A'),
                    resultado.get('raiz_cuadrada', 'N/A'),
                    resultado.get('doble', 'N/A'),
                    resultado.get('mitad', 'N/A')
                ]
            })
            
            st.dataframe(df)
            
            # Información adicional
            st.info(f"Procesado por: {resultado.get('procesado_por', 'Desconocido')}")
            st.text(f"Timestamp: {resultado.get('timestamp', 'N/A')}")
            
            # Ver datos JSON completos
            with st.expander("Ver respuesta JSON completa"):
                st.json(resultado)

# Instrucciones y explicación para Streamlit Cloud
st.markdown("---")
with st.expander("🔍 Cómo funciona esta integración", expanded=True):
    st.markdown("""
    ### Integración Streamlit Cloud ↔ Google Colab
    
    Esta aplicación demuestra una conexión directa entre Streamlit Cloud y un notebook de Google Colab.
    
    **Flujo de trabajo:**
    
    1. **Google Colab** ejecuta un servidor API usando Flask y lo expone a internet con ngrok.
    2. **Streamlit Cloud** se conecta directamente a este servidor a través de solicitudes HTTP.
    3. Puedes enviar datos desde Streamlit, procesarlos en Colab, y recibir los resultados automáticamente.
    
    **Ventajas:**
    
    - Ambos componentes funcionan en la nube (no se necesita nada local)
    - Comunicación bidireccional en tiempo real
    - Puedes utilizar todo el poder de procesamiento de Colab
    - Interfaz amigable con Streamlit
    
    **Limitaciones:**
    
    - La URL de ngrok cambia cada vez que reinicies el notebook de Colab
    - Las sesiones gratuitas de Colab tienen tiempo limitado
    
    Si necesitas una solución más permanente, considera implementar un servidor en Google Cloud Run o similar.
    """)

# Información para implementar en Streamlit Cloud
with st.expander("📋 Implementación en Streamlit Cloud"):
    st.markdown("""
    ### Cómo implementar esta app en Streamlit Cloud
    
    Para implementar esta aplicación en Streamlit Cloud:
    
    1. **Crea un repositorio en GitHub** con estos archivos:
       - `app.py` (este código)
       - `requirements.txt` (con las dependencias: streamlit, pandas, requests)
    
    2. **Despliega en Streamlit Cloud:**
       - Inicia sesión en [share.streamlit.io](https://share.streamlit.io)
       - Conecta tu repositorio de GitHub
       - Configura el despliegue
    
    3. **Configura tu notebook de Colab:**
       - Crea una API como la descrita aquí
       - Copia la URL de ngrok generada
    
    4. **Conecta ambos sistemas:**
       - Pega la URL de ngrok en esta aplicación
       - ¡Disfruta de la integración!
    """)

# Sidebar con estado e información adicional
st.sidebar.header("Estado de la conexión")
if st.session_state.api_url:
    st.sidebar.success(f"✅ Conectado a: {st.session_state.api_url}")
    
    if st.sidebar.button("Verificar estado"):
        exito, mensaje, status_info = verificar_conexion(st.session_state.api_url)
        if exito:
            st.sidebar.success(mensaje)
            if status_info:
                st.sidebar.info(f"Servidor activo desde: {status_info.get('timestamp', 'desconocido')}")
        else:
            st.sidebar.error(mensaje)
else:
    st.sidebar.warning("❌ No conectado")
    st.sidebar.info("Configura la URL de la API en el paso 1")

# Archivo requirements.txt
st.sidebar.markdown("---")
st.sidebar.subheader("Archivo requirements.txt")
st.sidebar.code("""
streamlit==1.22.0
pandas==1.5.3
requests==2.28.2
""")

# Nota de implementación
st.sidebar.markdown("---")
st.sidebar.caption("Integración Streamlit Cloud ↔ Google Colab")
