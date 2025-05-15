# app.py - Aplicación Streamlit con conexión automática a Colab
import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime

# Configuración de la página
st.set_page_config(
    page_title="Conexión Streamlit-Colab",
    page_icon="🔄",
    layout="wide"
)

st.title("Conexión automática entre Streamlit y Colab")
st.subheader("Usando API REST en tiempo real")

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
                return True, "Conexión exitosa a la API de Colab"
            else:
                return False, f"Error en la ruta /status: {status_response.status_code}"
        else:
            return False, f"Error al conectar: Código {response.status_code}"
    except Exception as e:
        return False, f"Error de conexión: {str(e)}"

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
            exito, mensaje = verificar_conexion(api_url)
            
            if exito:
                st.session_state.api_url = api_url
                st.success(mensaje)
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

# Instrucciones
with st.expander("❓ Instrucciones de uso"):
    st.markdown("""
    ### Cómo probar la conexión automática entre Streamlit y Colab:
    
    1. **En Google Colab:**
       - Abre tu notebook "Streamlit" existente
       - Crea una nueva celda
       - Copia todo el código de la sección "API en Colab"
       - Ejecuta la celda
       - Espera a que se configure el túnel ngrok
       - Copia la URL que aparece (algo como https://xxxx-xx-xx-xxx-xx.ngrok.io)
    
    2. **En esta aplicación Streamlit:**
       - Pega la URL en el campo del paso 1
       - Haz clic en "Guardar y verificar conexión"
       - Si la conexión es exitosa, verás un mensaje verde
    
    3. **Prueba la integración:**
       - Ingresa un número en el campo del paso 2
       - Haz clic en "Procesar en Colab"
       - Streamlit enviará el número a Colab a través de la API
       - Colab procesará el número y devolverá los resultados
       - Los resultados se mostrarán automáticamente en Streamlit
    
    **Nota:** Esta es una conexión en tiempo real. No se necesitan pasos manuales ni transferencia de archivos.
    """)

# Información del estado de la conexión
st.sidebar.header("Estado de la conexión")
if st.session_state.api_url:
    st.sidebar.success(f"✅ Conectado a: {st.session_state.api_url}")
    
    if st.sidebar.button("Verificar estado"):
        exito, mensaje = verificar_conexion(st.session_state.api_url)
        if exito:
            st.sidebar.success(mensaje)
        else:
            st.sidebar.error(mensaje)
else:
    st.sidebar.warning("❌ No conectado")
    st.sidebar.info("Configura la URL de la API en el paso 1")

# Información adicional
st.sidebar.markdown("---")
st.sidebar.caption("Integración en tiempo real Streamlit-Colab")
