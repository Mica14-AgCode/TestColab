# app.py - Versión mínima con dependencias nativas
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

st.title("Prueba de integración Streamlit-Colab")
st.subheader("Versión con dependencias nativas")

# Definir rutas locales (simular Drive)
BASE_DIR = "streamlit_colab_test"
INPUT_DIR = os.path.join(BASE_DIR, "input")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

# Crear carpetas si no existen
os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

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
    
    # Guardar en archivo
    ruta_archivo = os.path.join(INPUT_DIR, f"{id_tarea}.json")
    with open(ruta_archivo, 'w') as f:
        json.dump(datos, f, indent=2)
    
    return id_tarea, ruta_archivo

# Función para verificar si Colab ha procesado un número
def verificar_resultado(id_tarea):
    """Verifica si hay resultados disponibles para el ID dado"""
    ruta_resultado = os.path.join(OUTPUT_DIR, f"{id_tarea}_resultado.json")
    
    if os.path.exists(ruta_resultado):
        with open(ruta_resultado, 'r') as f:
            return json.load(f), ruta_resultado
    
    return None, ruta_resultado

# Inicializar el estado de la sesión si es necesario
if "tareas" not in st.session_state:
    st.session_state.tareas = []

# Instrucciones
st.info("""
### Instrucciones:
1. Ingresa un número abajo y haz clic en "Procesar en Colab"
2. La app guardará un archivo JSON en la carpeta `streamlit_colab_test/input/`
3. Copia manualmente este archivo a Google Drive (o configura una carpeta compartida)
4. Ejecuta el notebook de Colab que procesará el archivo
5. Colab guardará los resultados en una carpeta de salida
6. Copia el archivo de resultados a la carpeta `streamlit_colab_test/output/` en tu máquina
7. Haz clic en "Verificar resultados" para ver los resultados procesados
""")

# Ubicación de archivos
st.code(f"Carpeta de entrada: {os.path.abspath(INPUT_DIR)}")
st.code(f"Carpeta de salida: {os.path.abspath(OUTPUT_DIR)}")

# Formulario para ingresar un número
st.header("Ingresa un número para procesar en Colab")

with st.form("form_numero"):
    numero = st.number_input("Número", min_value=1, max_value=100, value=42)
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
            st.write("### Próximos pasos:")
            st.write("1. Copia este archivo a Google Drive (carpeta que Colab pueda acceder)")
            st.write("2. Ejecuta el notebook de Colab para procesar el archivo")
            st.write("3. Copia el archivo de resultados a la carpeta de salida local")
            st.write("4. Haz clic en 'Verificar resultados' para ver los resultados")

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
                    st.info("Asegúrate de que Colab haya procesado el archivo y hayas copiado el resultado a la carpeta de salida.")
            
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
st.caption("Versión minimalista para prueba de concepto Streamlit-Colab")
