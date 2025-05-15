# app.py - Aplicación Streamlit con API de Google Drive
import streamlit as st
import pandas as pd
import json
import os
import uuid
import time
import io
from datetime import datetime
import matplotlib.pyplot as plt

# Importaciones para Google Drive API
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

# Título y configuración
st.set_page_config(
    page_title="Streamlit-Colab con Google Drive API",
    page_icon="🔄",
    layout="wide"
)

st.title("Integración Streamlit-Colab con Google Drive API")
st.subheader("Un ejemplo usando la API oficial de Google Drive")

# Configuración para la API de Google Drive
# Si modificas estos ámbitos, elimina el archivo token.pickle
SCOPES = ['https://www.googleapis.com/auth/drive']

# Nombres de carpetas en Google Drive
DRIVE_FOLDER_NAME = "streamlit_colab_test"
INPUT_FOLDER_NAME = "input"
OUTPUT_FOLDER_NAME = "output"

# Función para autenticar y obtener servicio de Drive
@st.cache_resource
def get_drive_service():
    """Configura la autenticación y devuelve el servicio de Drive"""
    creds = None
    # El archivo token.pickle almacena los tokens de acceso y actualización del usuario
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
            
    # Si no hay credenciales válidas disponibles, permite al usuario iniciar sesión
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            credentials_file = st.file_uploader("Sube tu archivo credentials.json de Google Cloud", type=['json'])
            
            if not credentials_file:
                st.warning("⚠️ Se necesita un archivo credentials.json para continuar.")
                st.info("""
                Para obtener este archivo:
                1. Ve a [Google Cloud Console](https://console.developers.google.com/)
                2. Crea un proyecto (o usa uno existente)
                3. Habilita la API de Google Drive
                4. Crea credenciales OAuth para 'Aplicación de escritorio'
                5. Descarga el archivo JSON
                """)
                return None
            
            credentials_content = credentials_file.read()
            flow = InstalledAppFlow.from_client_config(
                json.loads(credentials_content.decode('utf-8')), 
                SCOPES
            )
            creds = flow.run_local_server(port=0)
            
            # Guarda las credenciales para la próxima ejecución
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
                
    # Construir el servicio
    service = build('drive', 'v3', credentials=creds)
    return service

# Función para buscar o crear carpeta en Drive
def find_or_create_folder(service, parent_id, folder_name):
    """Busca una carpeta por nombre y la crea si no existe"""
    # Buscar carpeta
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
    if parent_id:
        query += f" and '{parent_id}' in parents"
        
    results = service.files().list(
        q=query,
        spaces='drive',
        fields='files(id, name)'
    ).execute()
    
    items = results.get('files', [])
    
    # Si la carpeta existe, devolver su ID
    if items:
        return items[0]['id']
    
    # Si no existe, crearla
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    
    if parent_id:
        file_metadata['parents'] = [parent_id]
        
    folder = service.files().create(
        body=file_metadata,
        fields='id'
    ).execute()
    
    return folder.get('id')

# Función para configurar carpetas en Drive
@st.cache_resource
def setup_drive_folders(service):
    """Configura las carpetas necesarias en Drive y devuelve sus IDs"""
    # Buscar o crear carpeta principal
    base_folder_id = find_or_create_folder(service, None, DRIVE_FOLDER_NAME)
    
    # Buscar o crear subcarpetas
    input_folder_id = find_or_create_folder(service, base_folder_id, INPUT_FOLDER_NAME)
    output_folder_id = find_or_create_folder(service, base_folder_id, OUTPUT_FOLDER_NAME)
    
    return {
        'base_id': base_folder_id,
        'input_id': input_folder_id,
        'output_id': output_folder_id
    }

# Función para guardar datos en Drive
def save_to_drive(service, folder_id, filename, data):
    """Guarda datos JSON en un archivo en Google Drive"""
    # Crear archivo temporal
    with open(filename, 'w') as f:
        json.dump(data, f)
    
    # Configurar metadata y media
    file_metadata = {
        'name': filename,
        'parents': [folder_id]
    }
    
    media = MediaFileUpload(
        filename,
        mimetype='application/json',
        resumable=True
    )
    
    # Subir a Drive
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()
    
    # Eliminar archivo temporal
    os.remove(filename)
    
    return file.get('id')

# Función para verificar archivos en Drive
def check_file_in_drive(service, folder_id, filename):
    """Verifica si existe un archivo en una carpeta de Drive"""
    query = f"name='{filename}' and '{folder_id}' in parents"
    
    results = service.files().list(
        q=query,
        spaces='drive',
        fields='files(id, name)'
    ).execute()
    
    items = results.get('files', [])
    
    if items:
        return items[0]['id']
    else:
        return None

# Función para leer archivo de Drive
def read_from_drive(service, file_id):
    """Lee un archivo JSON desde Google Drive"""
    request = service.files().get_media(fileId=file_id)
    
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        
    fh.seek(0)
    return json.load(fh)

# Función para enviar un número a Colab
def enviar_a_colab(service, folder_ids, numero):
    """Envía un número a Colab a través de Google Drive"""
    # Crear ID único
    id_tarea = str(uuid.uuid4())
    
    # Crear un diccionario con los datos
    datos = {
        "id": id_tarea,
        "numero": numero,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Guardar en Drive
    filename = f"{id_tarea}.json"
    file_id = save_to_drive(service, folder_ids['input_id'], filename, datos)
    
    return id_tarea

# Función para verificar resultado
def verificar_resultado(service, folder_ids, id_tarea):
    """Verifica si Colab ha procesado el número y devuelve el resultado"""
    filename = f"{id_tarea}_resultado.json"
    file_id = check_file_in_drive(service, folder_ids['output_id'], filename)
    
    if file_id:
        return read_from_drive(service, file_id)
    else:
        return None

# Inicializar el estado de la sesión si es necesario
if "tareas" not in st.session_state:
    st.session_state.tareas = []

# Panel lateral con instrucciones
st.sidebar.header("Instrucciones")
st.sidebar.markdown("""
1. Autentícate con Google Drive (sube tu archivo credentials.json)
2. Ingresa un número y haz clic en "Procesar en Colab"
3. La aplicación guardará el número en Google Drive
4. Ejecuta el notebook de Colab para procesar el número
5. Regresa aquí y haz clic en "Verificar resultados"
6. ¡Verás los resultados procesados por Colab!
""")

st.sidebar.markdown("---")
st.sidebar.info("Esta aplicación usa la API oficial de Google Drive para comunicarse con Colab")

# Configurar servicio de Drive
service = get_drive_service()

if service:
    # Configurar carpetas
    try:
        folder_ids = setup_drive_folders(service)
        st.sidebar.success("✅ Conectado a Google Drive")
        st.sidebar.write(f"Carpeta base: {DRIVE_FOLDER_NAME}")
        
        # Formulario para ingresar un número
        st.header("Ingresa un número para procesar en Colab")
        
        with st.form("form_numero"):
            numero = st.number_input("Número", min_value=1, max_value=100, value=42)
            submitted = st.form_submit_button("Procesar en Colab")
            
            if submitted:
                with st.spinner("Enviando número a Colab a través de Google Drive..."):
                    # Enviamos el número
                    id_tarea = enviar_a_colab(service, folder_ids, numero)
                    
                    # Guardamos la tarea en el estado
                    st.session_state.tareas.append({
                        "id": id_tarea,
                        "numero": numero,
                        "timestamp": datetime.now(),
                        "estado": "pendiente"
                    })
                    
                    st.success(f"¡Número enviado a Google Drive! ID de tarea: {id_tarea}")
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
                        with st.spinner("Verificando en Google Drive..."):
                            resultado = verificar_resultado(service, folder_ids, tarea['id'])
                            
                            if resultado:
                                # Actualizar estado
                                st.session_state.tareas[i]['estado'] = "completado"
                                st.session_state.tareas[i]['resultado'] = resultado
                                
                                # Mostrar el resultado
                                st.success("¡Resultado procesado por Colab encontrado en Google Drive!")
                                
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
                                st.warning("Aún no hay resultados disponibles en Google Drive.")
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
    
    except Exception as e:
        st.error(f"Error al configurar carpetas en Drive: {str(e)}")
