import streamlit as st
import pandas as pd
import time
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from crossref.restful import Works
import tempfile
from io import BytesIO

# Configuración de la página
st.set_page_config(
    page_title="DOI Extractor",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título principal
st.title("📚 DOI Extractor - Crossref API")
st.markdown("**Extrae metadatos de DOIs registrados en Crossref de forma automatizada**")

# Funciones auxiliares
@st.cache_data
def limpiar_doi(doi):
    """Limpia y valida DOIs"""
    if pd.isna(doi) or doi == '':
        return None
    
    patron_doi = re.compile(r'10\.\d{4,9}/[-._;()/:A-Z0-9]+', re.IGNORECASE)
    
    if 'doi.org/' in str(doi):
        doi = str(doi).split('doi.org/')[-1].strip()
    
    doi = str(doi).replace('https://doi.org/', '').strip()
    
    if patron_doi.fullmatch(doi):
        return doi
    else:
        return None

def limpiar_texto(texto):
    """Limpia texto de etiquetas HTML/XML"""
    if isinstance(texto, str):
        texto = re.sub(r'<\/?jats:[p|sec|title|italic]+>', '', texto)
        texto = re.sub(r'<\/?jats:p[^>]*>', '', texto)
        texto = re.sub(r'&lt;p class="Resumen"&gt;', '', texto)
        texto = re.sub(r'&lt;/p&gt;', '', texto)
        texto = re.sub(r'&lt;p&gt;', '', texto)
        texto = re.sub(r'<p>', '', texto)
        texto = re.sub(r'</p>', '', texto)
        texto = re.sub(r'<i>', '', texto)
        texto = re.sub(r'<[^>]*>', '', texto)
        return texto.strip()
    return texto

def reordenar_autores(fila):
    """Reordena autores eliminando espacios vacíos"""
    autores = [fila[f'autor_{i}'] for i in range(1, 6) if pd.notna(fila[f'autor_{i}']) and fila[f'autor_{i}'] != '']
    
    for i in range(1, 6):
        fila[f'autor_{i}'] = autores[i-1] if i <= len(autores) else None
    
    return fila

def formatear_fecha(fecha):
    """Normaliza diferentes formatos de fecha a YYYY-MM-DD"""
    if pd.isna(fecha):
        return None
    
    # Si ya es un string datetime (para indexed_date y created_date)
    if isinstance(fecha, str):
        try:
            dt = datetime.fromisoformat(fecha.replace('Z', ''))
            return dt.strftime('%Y-%m-%d')
        except:
            return None
    
    # Si es una lista [año, mes, día] (para issued_date y published_date)
    elif isinstance(fecha, list) and len(fecha) >= 3:
        try:
            year = int(fecha[0]) if fecha[0] else None
            month = int(fecha[1]) if len(fecha) > 1 and fecha[1] else 1
            day = int(fecha[2]) if len(fecha) > 2 and fecha[2] else 1
            
            if year:
                return f"{year:04d}-{month:02d}-{day:02d}"
        except:
            return None
    
    return None

def fetch_crossref_data(doi, retries=3, delay=1):
    """Obtiene datos de Crossref para un DOI específico"""
    works = Works()
    attempt = 0
    
    while attempt < retries:
        try:
            data = works.doi(doi)
            if data:
                result = {"doi": doi}
                
                if "title" in campos_seleccionados:
                    result["title"] = data.get("title", [""])[0]
                
                if "abstract" in campos_seleccionados:
                    result["abstract"] = data.get("abstract", "")
                
                if "authors" in campos_seleccionados:
                    result["authors"] = ", ".join([
                        f"{a.get('given', '')} {a.get('family', '')}".strip()
                        for a in data.get("author", [])
                    ])
                
                if "reference_count" in campos_seleccionados:
                    result["reference_count"] = data.get("reference-count", None)
                
                if "is_referenced_by_count" in campos_seleccionados:
                    result["is_referenced_by_count"] = data.get("is-referenced-by-count", None)
                
                if "indexed_date" in campos_seleccionados:
                    result["indexed_date"] = data.get("indexed", {}).get("date-time") if data.get("indexed") else None
                
                if "created_date" in campos_seleccionados:
                    result["created_date"] = data.get("created", {}).get("date-time") if data.get("created") else None
                
                if "issued_date" in campos_seleccionados:
                    result["issued_date"] = data.get("issued", {}).get("date-parts")[0] if data.get("issued") else None
                
                if "published_date" in campos_seleccionados:
                    result["published_date"] = data.get("published", {}).get("date-parts")[0] if data.get("published") else None

                return pd.DataFrame([result])
            else:
                return None
        except Exception as e:
            attempt += 1
            if attempt < retries:
                time.sleep(delay)
            else:
                st.warning(f"Error final al buscar el DOI {doi}: {e}")
                return None

def procesar_autores(df):
    """Procesa y separa autores en columnas individuales"""
    if 'authors' in df.columns:
        autores_split = df['authors'].str.split(',', expand=True, n=5)
        autores_split = autores_split.iloc[:, :5]
        autores_split = autores_split.apply(lambda x: x.str.strip())
        autores_split.columns = [f'autor_{i+1}' for i in range(autores_split.shape[1])]
        df = pd.concat([df.drop('authors', axis=1), autores_split], axis=1)
    return df

# Sidebar para configuración
st.sidebar.header("⚙️ Configuración")

# Parámetros de procesamiento
num_parts = st.sidebar.number_input("Número de bloques", min_value=1, max_value=50, value=4, step=1,
                                   help="Divide la lista de DOIs en este número de bloques")

num_threads = st.sidebar.number_input("Hilos simultáneos", min_value=1, max_value=20, value=3, step=1,
                                     help="Número de consultas simultáneas a la API")

retries = st.sidebar.number_input("Número de reintentos", min_value=1, max_value=10, value=3, step=1,
                                 help="Intentos por cada DOI en caso de error")

delay = st.sidebar.number_input("Delay entre reintentos (s)", min_value=0.1, max_value=5.0, value=1.0, step=0.1,
                               help="Tiempo de espera entre reintentos")

fixed_delay = st.sidebar.number_input("Delay fijo entre requests (s)", min_value=0.0, max_value=2.0, value=0.1, step=0.1,
                                     help="Pausa entre cada request individual")

block_pause = st.sidebar.number_input("Pausa entre bloques (s)", min_value=0, max_value=120, value=10, step=5,
                                     help="Tiempo de espera entre bloques para evitar rate limiting")


# Campos a extraer
st.sidebar.header("📋 Campos a Extraer")
campos_disponibles = {
    "title": "Título",
    "abstract": "Abstract",
    "authors": "Autores",
    "reference_count": "Conteo de referencias",
    "is_referenced_by_count": "Conteo de citas",
    "indexed_date": "Fecha de indexación",
    "created_date": "Fecha de creación",
    "issued_date": "Fecha de emisión",
    "published_date": "Fecha de publicación"
}

campos_seleccionados = st.sidebar.multiselect(
    "Selecciona los campos a extraer:",
    options=list(campos_disponibles.keys()),
    default=list(campos_disponibles.keys()),
    format_func=lambda x: campos_disponibles[x]
)


# Área principal
st.header("📁 Carga de Archivos")

# Upload de archivo
uploaded_file = st.file_uploader(
    "Sube tu archivo con DOIs",
    type=['csv', 'xlsx'],
    help="El archivo debe contener una columna llamada 'DOI' o 'doi'"
)

if uploaded_file is not None:
    try:
        # Leer archivo
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        st.success(f"✅ Archivo cargado exitosamente: {len(df)} filas")
        
        # Mostrar columnas disponibles
        st.subheader("Columnas detectadas:")
        st.write(list(df.columns))
        
        # Seleccionar columna de DOI
        doi_column = st.selectbox(
            "Selecciona la columna que contiene los DOIs:",
            options=df.columns,
            index=0 if 'DOI' in df.columns else (1 if 'doi' in df.columns else 0)
        )
        
        # Vista previa
        st.subheader("Vista previa de los datos:")
        st.dataframe(df.head(10))
        
        # Limpieza de DOIs
        st.subheader("🧹 Limpieza y Validación de DOIs")
        
        if st.button("Limpiar y Validar DOIs"):
            with st.spinner("Limpiando DOIs..."):
                df['DOI_limpio'] = df[doi_column].apply(limpiar_doi)
                df_validos = df[df['DOI_limpio'].notna()].copy()
                df_invalidos = df[df['DOI_limpio'].isna()].copy()
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("DOIs válidos", len(df_validos))
                with col2:
                    st.metric("DOIs inválidos", len(df_invalidos))
                
                if len(df_invalidos) > 0:
                    st.warning("⚠️ Algunos DOIs no son válidos")
                    with st.expander("Ver DOIs inválidos"):
                        st.dataframe(df_invalidos[[doi_column]])
                
                # Guardar en session state
                st.session_state.df_validos = df_validos
                st.session_state.df_invalidos = df_invalidos
        
        # Procesamiento principal
        if 'df_validos' in st.session_state and len(st.session_state.df_validos) > 0:
            st.subheader("🚀 Extracción de Metadatos")
            
            df_validos = st.session_state.df_validos
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("DOIs a procesar", len(df_validos))
            with col2:
                tiempo_estimado = (len(df_validos) * (fixed_delay + 0.5)) / num_threads + (num_parts * block_pause)
                st.metric("Tiempo estimado", f"{tiempo_estimado/60:.1f} min")
            
            if st.button("🔄 Iniciar Extracción", type="primary"):
                # Crear directorio temporal
                with tempfile.TemporaryDirectory() as temp_dir:
                    
                    # Dividir en chunks
                    chunk_size = len(df_validos) // num_parts + 1
                    chunks = [df_validos[i:i+chunk_size] for i in range(0, len(df_validos), chunk_size)]
                    
                    # Progress bars
                    overall_progress = st.progress(0)
                    status_text = st.empty()
                    
                    datos_extraidos = []
                    
                    for i, chunk in enumerate(chunks):
                        status_text.text(f"Procesando bloque {i+1}/{len(chunks)} ({len(chunk)} DOIs)")
                        
                        chunk_data = []
                        with ThreadPoolExecutor(max_workers=num_threads) as executor:
                            future_to_doi = {
                                executor.submit(fetch_crossref_data, doi, retries, delay): doi 
                                for doi in chunk['DOI_limpio']
                            }
                            
                            for future in as_completed(future_to_doi):
                                data = future.result()
                                if data is not None:
                                    chunk_data.append(data)
                                time.sleep(fixed_delay)
                        
                        if chunk_data:
                            datos_extraidos.extend(chunk_data)
                        
                        # Actualizar progreso
                        progress = (i + 1) / len(chunks)
                        overall_progress.progress(progress)
                        
                        # Pausa entre bloques
                        if i < len(chunks) - 1 and block_pause > 0:
                            status_text.text(f"Esperando {block_pause}s antes del siguiente bloque...")
                            time.sleep(block_pause)
                    
                    # Procesamiento final
                    if datos_extraidos:
                        status_text.text("Consolidando y limpiando datos...")
                        
                        # Combinar todos los datos
                        df_resultado = pd.concat(datos_extraidos, ignore_index=True)
                        df_resultado = df_resultado.drop_duplicates(subset=['doi'], keep='first')
                        
                        # Procesar autores
                        df_resultado = procesar_autores(df_resultado)
                        df_resultado = df_resultado.apply(reordenar_autores, axis=1)
                        
                        # Limpiar texto (sólo si el campo fue seleccionado y existe)
                        if 'title' in df_resultado.columns and "title" in campos_seleccionados:
                            df_resultado['title'] = df_resultado['title'].apply(limpiar_texto)
                        if 'abstract' in df_resultado.columns and "abstract" in campos_seleccionados:
                            df_resultado['abstract'] = df_resultado['abstract'].apply(limpiar_texto)
                        
                        # Hacer left join con datos originales
                        df_final = pd.merge(
                            df_resultado,
                            df_validos,
                            how='left',
                            left_on='doi',
                            right_on='DOI_limpio'
                        )
                        
                        # Limpiar columnas duplicadas
                        df_final = df_final.drop(['DOI_limpio'], axis=1, errors='ignore')
                        
                        st.success(f"✅ Extracción completada: {len(df_final)} registros procesados")
                        
                        # Mostrar estadísticas
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Registros extraídos", len(df_final))
                        with col2:
                            con_abstract = df_final['abstract'].notna().sum()
                            st.metric("Con abstract", con_abstract)
                        with col3:
                            con_autores = df_final['autor_1'].notna().sum()
                            st.metric("Con autores", con_autores)
                        
                        # Vista previa del resultado
                        st.subheader("📊 Resultado Final")
                        st.dataframe(df_final.head(10))
                        
                        # Descarga
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        
                        # Crear archivo Excel
                        output = BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            df_final.to_excel(writer, sheet_name='Datos_Extraidos', index=False)
                            if len(st.session_state.df_invalidos) > 0:
                                st.session_state.df_invalidos.to_excel(writer, sheet_name='DOIs_Invalidos', index=False)
                        
                        st.download_button(
                            label="📥 Descargar Resultado (Excel)",
                            data=output.getvalue(),
                            file_name=f"doi_extraction_results_{timestamp}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                        
                        # También ofrecer CSV
                        csv_data = df_final.to_csv(index=False)
                        st.download_button(
                            label="📥 Descargar Resultado (CSV)",
                            data=csv_data,
                            file_name=f"doi_extraction_results_{timestamp}.csv",
                            mime="text/csv"
                        )
                    
                    else:
                        st.error("❌ No se pudieron extraer datos de ningún DOI")
                    
                    overall_progress.progress(1.0)
                    status_text.text("✅ Proceso completado")

    except Exception as e:
        st.error(f"❌ Error al cargar el archivo: {str(e)}")

else:
    st.info("👆 Por favor, sube un archivo CSV o Excel con DOIs para comenzar")

# Footer
st.markdown("---")
st.markdown("""
**💡 Instrucciones de uso:**
1. Sube un archivo CSV o Excel que contenga una columna con DOIs
2. Configura los parámetros en la barra lateral
3. Limpia y valida los DOIs
4. Inicia la extracción
5. Descarga el resultado final

**📚 Acerca de esta herramienta:**
Esta aplicación extrae metadatos de DOIs usando la API de Crossref, incluyendo títulos, abstracts, autores, fechas y métricas de citas.
""")