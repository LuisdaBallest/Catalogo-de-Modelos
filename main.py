import streamlit as st
import pandas as pd
from PIL import Image, UnidentifiedImageError
import mysql.connector
import os

# Inicializar la variable de estado para la contraseña
if 'password_correct' not in st.session_state:
    st.session_state.password_correct = False

# Solicitar la contraseña al usuario si no ha sido verificada
if not st.session_state.password_correct:
    password = st.text_input("Introduce la contraseña:", type="password")
    if password == st.secrets["PASSWORD-0"]:
        st.session_state.password_correct = True
        st.experimental_rerun()  # Recargar la aplicación para ocultar el campo de entrada de la contraseña
    elif password:
        st.error("Contraseña incorrecta")

# Mostrar el contenido de la aplicación solo si la contraseña es correcta
if st.session_state.password_correct:
    # Conectar a la base de datos MySQL usando st.secrets
    conn = mysql.connector.connect(
        host=st.secrets["host"],
        port=st.secrets["port"],
        user=st.secrets["user"],
        password=st.secrets["password"],
        database=st.secrets["database"]
    )
    cursor = conn.cursor(dictionary=True)

    # Obtener datos de la tabla Modelos
    cursor.execute("SELECT * FROM Modelos")
    df_modelos = pd.DataFrame(cursor.fetchall())

    # Obtener datos de la tabla llantas
    cursor.execute("SELECT * FROM llantas")
    df_llantas = pd.DataFrame(cursor.fetchall())

    # Obtener datos de la tabla Valvulas
    cursor.execute("SELECT * FROM Valvulas")
    df_valvulas = pd.DataFrame(cursor.fetchall())

    cursor.close()
    conn.close()

    # Agrupar por 'Equipment Description' y concatenar las descripciones y códigos de artículo
    df_modelos_llantas_grouped = df_llantas.groupby('Equipment Description').agg({
        'Desc Michelin': lambda x: ', '.join(x.dropna().unique()),
        'Desc MAXAM': lambda x: ', '.join(x.dropna().unique()),
        'CAI': lambda x: ', '.join(x.dropna().astype(str).unique()),
        'MAXAM': lambda x: ', '.join(x.dropna().astype(str).unique())
    }).reset_index()

    df_modelos_llantas_grouped = df_modelos.merge(df_modelos_llantas_grouped, on='Equipment Description', how='left')

    st.title("Catálogo de Equipos Mineros")
    st.subheader('Equipos Mineros usados en México')

    # Obtener opciones únicas para los filtros
    tipos_equipo = df_modelos_llantas_grouped['Tipo'].unique()
    fabricantes = df_modelos_llantas_grouped['Fabricante'].unique()

    # Añadir widgets de selección para los filtros
    tipo_seleccionado = st.selectbox("Selecciona el tipo de equipo", ["Todos"] + list(tipos_equipo))
    fabricante_seleccionado = st.selectbox("Selecciona el fabricante", ["Todos"] + list(fabricantes))

    # Filtrar el DataFrame en función de las selecciones del usuario
    if tipo_seleccionado != "Todos":
        df_modelos_llantas_grouped = df_modelos_llantas_grouped[df_modelos_llantas_grouped['Tipo'] == tipo_seleccionado]
    if fabricante_seleccionado != "Todos":
        df_modelos_llantas_grouped = df_modelos_llantas_grouped[df_modelos_llantas_grouped['Fabricante'] == fabricante_seleccionado]

    # Añadir un buscador para filtrar la lista de modelos
    search_query = st.text_input("Buscar modelo de equipo")

    # Filtrar el DataFrame en función de la entrada del usuario
    if search_query:
        df_modelos_llantas_grouped = df_modelos_llantas_grouped[df_modelos_llantas_grouped['Equipment Description'].str.contains(search_query, case=False, na=False)]

    # Mostrar imágenes correspondientes a cada modelo de equipo en filas y columnas
    num_columns = 3  # Número de columnas
    rows = [df_modelos_llantas_grouped[i:i + num_columns] for i in range(0, df_modelos_llantas_grouped.shape[0], num_columns)]

    # Altura fija para las imágenes
    fixed_height = 500

    # Función para mostrar detalles en el sidebar
    def mostrar_detalles(row):
        st.sidebar.title(f"Detalles del equipo: {row['Equipment Description']}")
        image_path = os.path.join('./images', row['Imagen'])  # Asegúrate de tener una columna 'Imagen' en tu tabla Modelos
        try:
            if os.path.exists(image_path):
                image = Image.open(image_path)
                # Redimensionar la imagen manteniendo la relación de aspecto
                aspect_ratio = image.width / image.height
                new_width = int(fixed_height * aspect_ratio)
                resized_image = image.resize((new_width, fixed_height))
                st.sidebar.image(resized_image, caption=row['Equipment Description'], use_container_width=True)
            else:
                st.sidebar.write("Imagen no disponible")
        except UnidentifiedImageError:
            st.sidebar.write("Error al cargar la imagen")

        st.sidebar.write(f"**Fabricante:** {row['Fabricante']}")

        # Añadir descripciones Michelin con CAI
        desc_michelin_list = row['Desc Michelin'].split(', ')
        cai_list = row['CAI'].split(', ')
        for desc_michelin, cai in zip(desc_michelin_list, cai_list):
            st.sidebar.write(f"**Descripción Michelin:** {desc_michelin} ({cai})")

        # Añadir descripciones MAXAM con MAXAM
        desc_maxam_list = row['Desc MAXAM'].split(', ')
        maxam_list = row['MAXAM'].split(', ')
        for desc_maxam, maxam in zip(desc_maxam_list, maxam_list):
            st.sidebar.write(f"**Descripción MAXAM:** {desc_maxam} ({maxam})")

        # Filtrar datos de la tabla Valvulas
        df_valvulas_filtrado = df_valvulas[df_valvulas['Equipment Description'] == row['Equipment Description']]

        # Mostrar tabla de Valvulas en el sidebar
        if not df_valvulas_filtrado.empty:
            st.sidebar.write("**Válvulas:**")
            st.sidebar.table(df_valvulas_filtrado[['Marca Valvula', 'Componente', 'Nombre KT', 'Codigo KT']])

    for row in rows:
        cols = st.columns(num_columns)
        for col, (_, row_data) in zip(cols, row.iterrows()):
            with col:
                st.markdown(f"<h3>{row_data['Equipment Description']}</h3>", unsafe_allow_html=True)
                image_path = os.path.join('./images', row_data['Imagen'])
                
                try:
                    if os.path.exists(image_path):
                        image = Image.open(image_path)
                        # Redimensionar la imagen manteniendo la relación de aspecto
                        aspect_ratio = image.width / image.height
                        new_width = int(fixed_height * aspect_ratio)
                        resized_image = image.resize((new_width, fixed_height))
                        st.image(resized_image, caption=row_data['Equipment Description'], use_container_width=True)
                    else:
                        st.write("Imagen no disponible")
                except UnidentifiedImageError:
                    st.write("Error al cargar la imagen")
                
                if st.button(f"Ver detalles de {row_data['Equipment Description']}", key=f"details_{row_data.name}"):
                    mostrar_detalles(row_data)