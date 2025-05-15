# app.py - Streamlit app adaptada a tu estructura de Drive existente
import streamlit as st
import pandas as pd
import json
import os
import uuid
import time
from datetime import datetime

# Configuración de la página
st.set_page_config(
    page_title="Test Streamlit-Colab",
    page_icon="🔄"
)

st.title("Prueba de integración con notebook Streamlit de Colab")
st.subheader("Versión específica para tu notebook existente")

# Carpetas locales para simulación - estas son las carpetas donde guardarás temporalmente
# los archivos antes de transferirlos a Drive
LOCAL_DIR = "streamlit_colab_test_local"
LOCAL_INPUT_DIR = os.path.join(LOCAL_DIR, "input")
LOCAL_OUTPUT_DIR = os.path.join(LOCAL_DIR, "output")

# Crear carpetas locales si no existen
os.makedirs(LOCAL_INPUT_DIR, exist_ok=True)
os.makedirs(LOCAL_OUTPUT_DIR, exist_ok=True)

# Mostrar rutas de Drive para el usuario
st.info("""
### Carpetas correspondientes en Google Drive:
- Carpeta de entrada: `/content/drive/MyDrive/Colab Notebooks/streamlit_input/`
- Carpeta de salida: `/content/drive/MyDrive/Colab Notebooks/streamlit_output/`

Estas carpetas se crearán automáticamente cuando ejecutes el código en tu notebook de Colab.
""")

# Función para guardar un número para ser procesado por Colab
def enviar_a_colab(numero):
    """Guarda un número en un archivo para que Colab lo procese"""
    # Crear ID único
    id_tarea = str(uuid.uuid4())[:8]  # Versión corta para facilitar la lectura
    
    # Crear un diccionario con los datos
    datos = {
        "id": id_tarea,
        "numero": numero,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Guardar en archivo local
    ruta_archivo = os.path.join(LOCAL_INPUT_DIR, f"{id_tarea}.json")
    with open(ruta_archivo, 'w') as f:
        json.dump(datos, f, indent=2)
    
    return id_tarea, ruta_archivo

# Función para verificar si Colab ha procesado un número
def verificar_resultado(id_tarea):
    """Verifica si hay resultados disponibles para el ID dado"""
    ruta_resultado = os.path.join(LOCAL_OUTPUT_DIR, f"{id_tarea}_resultado.json")
    
    if os.path.exists(ruta_resultado):
        with open(ruta_resultado, 'r') as f:
            return json.load(f), ruta_resultado
    
    return None, ruta_resultado

# Inicializar el estado de la sesión si es necesario
if "tareas" not in st.session_state:
    st.session_state.tareas = []

# Instrucciones
st.markdown("""
### Instrucciones para probar la integración:

1. **Paso 1:** Ingresa un número abajo y haz clic en "Procesar en Colab"
2. **Paso 2:** La app creará un archivo JSON en la carpeta local
3. **Paso 3:** Copia este archivo a Google Drive en la carpeta `/content/drive/MyDrive/Colab Notebooks/streamlit_input/`
4. **Paso 4:** Abre tu notebook "Streamlit" en Google Colab
5. **Paso 5:** Pega el código proporcionado en una celda y ejecútalo
6. **Paso 6:** El notebook procesará el archivo y guardará los resultados en `/content/drive/MyDrive/Colab Notebooks/streamlit_output/`
7. **Paso 7:** Copia el archivo de resultados a tu carpeta local `{LOCAL_OUTPUT_DIR}`
8. **Paso 8:** Regresa aquí y haz clic en "Verificar resultados" para ver los resultados
""")

# Ubicación de archivos locales
st.code(f"Carpeta local de entrada: {os.path.abspath(LOCAL_INPUT_DIR)}")
st.code(f"Carpeta local de salida: {os.path.abspath(LOCAL_OUTPUT_DIR)}")

# Formulario para ingresar un número
st.header("Ingresa un número para procesar en Colab")

with st.form("form_numero"):
    numero = st.number_input("Número", min_value=1, max_value=1000, value=42)
    submitted = st.form_submit_button("Procesar en Colab")
    
    if submitted:
        with st.spinner("Preparando archivo para Colab..."):
            # Enviamos el número
            id_tarea, ruta_archivo = enviar_a_colab(numero)
            
            # Guardamos la tarea en el estado
            st.session_state.tareas.append({
                "id": id_tarea,
                "numero": numero,
                "timestamp": datetime.now(),
                "estado": "pendiente"
            })
            
            st.success(f"¡Archivo creado con éxito!")
            st.info(f"ID de tarea: {id_tarea}")
            st.code(f"Ruta del archivo: {ruta_archivo}")
            
            # Instrucciones para el usuario
            st.markdown("""
            ### Próximos pasos:
            1. Copia este archivo a la carpeta `/content/drive/MyDrive/Colab Notebooks/streamlit_input/` en Google Drive
            2. Ejecuta tu notebook "Streamlit" en Colab con el código proporcionado
            3. Copia el archivo de resultados de Google Drive a tu carpeta local de salida
            4. Haz clic en "Verificar resultados" para ver los resultados
            """)

# Mostrar tareas y resultados
if st.session_state.tareas:
    st.header("Tareas enviadas a Colab")
    
    for i, tarea in enumerate(st.session_state.tareas):
        with st.expander(f"Tarea {i+1}: Número {tarea['numero']} - {tarea['estado'].capitalize()}", expanded=(i==0)):
            st.write(f"ID de tarea: {tarea['id']}")
            st.write(f"Enviada: {tarea['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Botón para verificar el resultado
            if st.button(f"Verificar resultado #{i+1}"):
                resultado, ruta_resultado = verificar_resultado(tarea['id'])
                
                if resultado:
                    # Actualizar estado
                    st.session_state.tareas[i]['estado'] = "completado"
                    st.session_state.tareas[i]['resultado'] = resultado
                    
                    # Mostrar el resultado
                    st.success("¡Resultado procesado por Colab encontrado!")
                    
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
                    
                else:
                    st.warning(f"Aún no hay resultados disponibles en: {ruta_resultado}")
                    st.info("Asegúrate de que Colab haya procesado el archivo y hayas copiado el resultado a la carpeta de salida local.")
            
            # Si ya tenemos el resultado, mostrarlo
            if tarea.get('estado') == "completado" and 'resultado' in tarea:
                resultado = tarea['resultado']
                
                st.success("Resultado procesado por Colab:")
                
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
else:
    st.info("No hay tareas enviadas. Ingresa un número y haz clic en 'Procesar en Colab'.")

# Información adicional
st.markdown("---")
st.caption("Versión adaptada para trabajar con tu notebook 'Streamlit' existente")
