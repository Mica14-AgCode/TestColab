# app.py - Aplicación Streamlit mínima para integración con Colab
import streamlit as st
import pandas as pd
import json
import os
import uuid
import time
from datetime import datetime
import matplotlib.pyplot as plt

# Título y configuración
st.set_page_config(
    page_title="Test Streamlit-Colab",
    page_icon="🔄",
    layout="wide"
)

st.title("Prueba de integración Streamlit-Colab")
st.subheader("Un ejemplo super simple")

# Definir rutas locales (simular Drive)
# En producción, estas carpetas deberían estar en Google Drive
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
    id_tarea = str(uuid.uuid4())
    
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
    
    return id_tarea

# Función para verificar si Colab ha procesado un número
def verificar_resultado(id_tarea):
    """Verifica si hay resultados disponibles para el ID dado"""
    ruta_resultado = os.path.join(OUTPUT_DIR, f"{id_tarea}_resultado.json")
    
    if os.path.exists(ruta_resultado):
        with open(ruta_resultado, 'r') as f:
            return json.load(f)
    
    return None

# Inicializar el estado de la sesión si es necesario
if "tareas" not in st.session_state:
    st.session_state.tareas = []

# Panel lateral con instrucciones
st.sidebar.header("Instrucciones")
st.sidebar.markdown("""
1. Ingresa un número y haz clic en "Procesar en Colab"
2. La aplicación guardará el número en un archivo JSON
3. Ejecuta el notebook de Colab para procesar el número
4. Regresa aquí y haz clic en "Verificar resultados"
5. ¡Verás los resultados procesados por Colab!
""")

st.sidebar.markdown("---")

# Si estás en modo local, mostrar la ubicación de los archivos
st.sidebar.subheader("Ubicación de archivos")
st.sidebar.code(f"Input: {os.path.abspath(INPUT_DIR)}")
st.sidebar.code(f"Output: {os.path.abspath(OUTPUT_DIR)}")

st.sidebar.markdown("---")
st.sidebar.info("Esta es una demostración mínima de integración Streamlit-Colab.")

# Formulario para ingresar un número
st.header("Ingresa un número para procesar en Colab")

with st.form("form_numero"):
    numero = st.number_input("Número", min_value=1, max_value=100, value=42)
    submitted = st.form_submit_button("Procesar en Colab")
    
    if submitted:
        with st.spinner("Enviando número a Colab..."):
            # Simulamos un pequeño retraso
            time.sleep(0.5)
            
            # Enviamos el número
            id_tarea = enviar_a_colab(numero)
            
            # Guardamos la tarea en el estado
            st.session_state.tareas.append({
                "id": id_tarea,
                "numero": numero,
                "timestamp": datetime.now(),
                "estado": "pendiente"
            })
            
            st.success(f"¡Número enviado! ID de tarea: {id_tarea}")
            st.info("Ahora ejecuta el notebook de Colab para procesar este número.")

# Mostrar tareas y resultados
if st.session_state.tareas:
    st.header("Tareas enviadas a Colab")
    
    for i, tarea in enumerate(st.session_state.tareas):
        with st.expander(f"Tarea {i+1}: Número {tarea['numero']} - {tarea['estado'].capitalize()}", expanded=(i==0)):
            st.write(f"ID de tarea: {tarea['id']}")
            st.write(f"Enviada: {tarea['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Botón para verificar el resultado
            if st.button(f"Verificar resultado #{i+1}"):
                resultado = verificar_resultado(tarea['id'])
                
                if resultado:
                    # Actualizar estado
                    st.session_state.tareas[i]['estado'] = "completado"
                    st.session_state.tareas[i]['resultado'] = resultado
                    
                    # Mostrar el resultado
                    st.success("¡Resultado procesado por Colab!")
                    
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
                            resultado['numero_original'],
                            resultado['cuadrado'],
                            resultado['raiz_cuadrada'],
                            resultado['doble'],
                            resultado['mitad']
                        ]
                    })
                    
                    st.dataframe(df)
                    
                    # Mostrar un gráfico simple
                    fig, ax = plt.subplots()
                    ax.bar(['Original', 'Cuadrado', 'Doble', 'Mitad'], 
                          [resultado['numero_original'], 
                           resultado['cuadrado'], 
                           resultado['doble'], 
                           resultado['mitad']])
                    ax.set_title(f"Operaciones con el número {resultado['numero_original']}")
                    st.pyplot(fig)
                    
                    # Información adicional
                    st.info(f"Procesado por: {resultado['procesado_por']}")
                    st.text(f"Timestamp: {resultado['timestamp']}")
                    
                else:
                    st.warning("Aún no hay resultados disponibles.")
                    st.info("Ejecuta el notebook de Colab para procesar este número.")
            
            # Si ya tenemos el resultado, mostrarlo
            if tarea.get('estado') == "completado" and 'resultado' in tarea:
                resultado = tarea['resultado']
                
                st.success("¡Resultado procesado por Colab!")
                
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
                        resultado['numero_original'],
                        resultado['cuadrado'],
                        resultado['raiz_cuadrada'],
                        resultado['doble'],
                        resultado['mitad']
                    ]
                })
                
                st.dataframe(df)
                
                # Mostrar un gráfico simple
                fig, ax = plt.subplots()
                ax.bar(['Original', 'Cuadrado', 'Doble', 'Mitad'], 
                      [resultado['numero_original'], 
                       resultado['cuadrado'], 
                       resultado['doble'], 
                       resultado['mitad']])
                ax.set_title(f"Operaciones con el número {resultado['numero_original']}")
                st.pyplot(fig)
                
                # Información adicional
                st.info(f"Procesado por: {resultado['procesado_por']}")
                st.text(f"Timestamp: {resultado['timestamp']}")
else:
    st.info("No hay tareas enviadas. Ingresa un número y haz clic en 'Procesar en Colab'.")
