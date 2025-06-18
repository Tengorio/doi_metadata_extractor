# 📚 DOI Metadata Extractor

Una aplicación web desarrollada en Streamlit que permite extraer metadatos de DOIs (Digital Object Identifiers) de forma automatizada utilizando la API de Crossref.

## 🚀 Características

- **Extracción masiva**: Procesa múltiples DOIs desde archivos CSV o Excel
- **Metadatos completos**: Extrae títulos, abstracts, autores, fechas y métricas de citación
- **Procesamiento paralelo**: Utiliza hilos múltiples para acelerar la extracción 
- **Validación de DOIs**: Limpia y valida automáticamente los DOIs
- **Configuración flexible**: Parámetros ajustables para optimizar el rendimiento
- **Exportación múltiple**: Descarga resultados en formato Excel o CSV
- **Interfaz intuitiva**: Diseño limpio y fácil de usar

## 📋 Campos Extraídos

- **Título** del artículo
- **Abstract** (resumen)
- **Autores** (hasta 5 autores principales)
- **Conteo de referencias**
- **Conteo de citas** (is-referenced-by-count)
- **Fecha de indexación**
- **Fecha de creación**
- **Fecha de emisión**
- **Fecha de publicación**

## 🛠️ Instalación Local

### Requisitos Previos

- Python 3.7 o superior
- pip (gestor de paquetes de Python)

### Pasos de Instalación

1. **Clona el repositorio**
   ```bash
   git clone https://github.com/tu-usuario/doi-metadata-extractor.git
   cd doi-metadata-extractor
   ```

2. **Crea un entorno virtual (recomendado)**
   ```bash
   python -m venv venv
   
   # En Windows
   venv\Scripts\activate
   
   # En macOS/Linux
   source venv/bin/activate
   ```

3. **Instala las dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Ejecuta la aplicación**
   ```bash
   streamlit run doi_metadata_extractor.py
   ```

La aplicación se abrirá automáticamente en tu navegador en `http://localhost:8501`

## 🌐 Aplicación en Línea

Puedes usar la aplicación directamente sin instalación en:
**[https://doi-metadata-extractor.streamlit.app](https://doi-metadata-extractor.streamlit.app)**

## 📖 Cómo Usar

### 1. Preparar tus Datos
- Crea un archivo CSV o Excel con una columna que contenga DOIs
- Los DOIs pueden estar en cualquier formato (con o sin https://doi.org/)
- Nombra la columna como 'DOI' o 'doi' para detección automática

### 2. Configurar Parámetros
En la barra lateral puedes ajustar:
- **Número de bloques**: Divide el procesamiento para mejor gestión
- **Hilos simultáneos**: Controla la velocidad de procesamiento
- **Reintentos**: Número de intentos por DOI en caso de error
- **Delays**: Pausas para respetar límites de la API

### 3. Seleccionar Campos
Elige qué metadatos extraer para optimizar el tiempo de procesamiento:
- Título y abstract para análisis de contenido
- Autores para estudios bibliométricos
- Fechas para análisis temporal
- Métricas de citación para análisis de impacto

### 4. Procesar
1. Sube tu archivo
2. Limpia y valida los DOIs
3. Inicia la extracción
4. Descarga los resultados

## 📊 Formato de Salida

La aplicación genera archivos con las siguientes columnas:
- `doi`: DOI original
- `title`: Título del artículo
- `abstract`: Resumen del artículo
- `autor_1` a `autor_5`: Autores principales
- `reference_count`: Número de referencias
- `is_referenced_by_count`: Número de citas recibidas
- `indexed_date`: Fecha de indexación en Crossref
- `created_date`: Fecha de creación del registro
- `issued_date`: Fecha de emisión
- `published_date`: Fecha de publicación

## ⚙️ Configuración Avanzada

### Optimización de Rendimiento
- **Pocos DOIs (< 100)**: Usa más hilos (5-10) y menos bloques (1-2)
- **Muchos DOIs (> 1000)**: Usa menos hilos (2-3) y más bloques (5-10)
- **Conexión lenta**: Aumenta los delays y reduce hilos

### Gestión de Rate Limits
La API de Crossref tiene límites de velocidad. La aplicación incluye:
- Delays configurables entre requests
- Pausas entre bloques de procesamiento
- Sistema de reintentos automático
- Procesamiento por lotes

## 🔧 Tecnologías Utilizadas

- **[Streamlit](https://streamlit.io/)**: Framework de aplicación web
- **[Pandas](https://pandas.pydata.org/)**: Manipulación y análisis de datos
- **[crossref-commons](https://github.com/CrossRef/crossref-commons)**: Cliente Python para API de Crossref
- **[openpyxl](https://openpyxl.readthedocs.io/)**: Lectura/escritura de archivos Excel
- **concurrent.futures**: Procesamiento paralelo

## 📝 Limitaciones

- Dependiente de la disponibilidad de la API de Crossref
- Algunos DOIs pueden no tener todos los metadatos disponibles
- Rate limits de la API pueden afectar la velocidad de procesamiento
- La calidad de los abstracts depende de lo que proporcione el editor

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Para contribuir:

1. Fork el proyecto
2. Crea una rama  (`git checkout -b nueva_rama`)
3. Commit tus cambios (`git commit -m 'Agrega una nueva característica'`)
4. Push a la rama (`git push origin nueva_rama`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 📧 Contacto

Si tienes preguntas, sugerencias o encuentras algún error, puedes:
- Contactar al desarrollador: [inktenorio@gmail.com]

## 🙏 Agradecimientos

- [Crossref](https://www.crossref.org/) por proporcionar la API gratuita
- [Streamlit](https://streamlit.io/) por el excelente framework
- La comunidad de código abierto por las librerías utilizadas

---

⭐ Si esta herramienta te resulta útil, ¡considera darle una estrella al repositorio!