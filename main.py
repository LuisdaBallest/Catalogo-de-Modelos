import streamlit as st
import folium
from streamlit_folium import st_folium
from PIL import Image, UnidentifiedImageError
import mysql.connector
import os
import json
import pandas as pd

# Inicializar la variable de estado para la contraseña
if 'password_correct' not in st.session_state:
    st.session_state.password_correct = False

# Solicitar la contraseña al usuario si no ha sido verificada
if not st.session_state.password_correct:
    password = st.text_input("Introduce la contraseña:", type="password")
    if password == st.secrets["PASSWORD-0"]:
        st.session_state.password_correct = True
        st.rerun()  # Recargar la aplicación para ocultar el campo de entrada de la contraseña
    elif password:
        st.error("Contraseña incorrecta")

# Mostrar el contenido de la aplicación solo si la contraseña es correcta
if st.session_state.password_correct:
    # Crear tabs
    tab1, tab2 = st.tabs(["Catálogo de Equipos Mineros", "Mapa de Plantas"])

    @st.cache_data
    def load_data_from_db():
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

        # Obtener datos de la tabla Rines
        cursor.execute("SELECT * FROM Rines")
        df_rines = pd.DataFrame(cursor.fetchall())

        # Obtener datos de la tabla Equipos_Mina
        cursor.execute("SELECT * FROM Equipos_Mina")
        df_equipos_mina = pd.DataFrame(cursor.fetchall())

        cursor.close()
        conn.close()

        return df_modelos, df_llantas, df_valvulas, df_rines, df_equipos_mina

    df_modelos, df_llantas, df_valvulas, df_rines, df_equipos_mina = load_data_from_db()

    with tab1:
        # Agrupar por 'Equipment Description' y concatenar las descripciones y códigos de artículo
        df_modelos_llantas_grouped = df_llantas.groupby('Equipment Description').agg({
            'Desc Michelin': lambda x: ', '.join(x.dropna().unique()),
            'Desc MAXAM': lambda x: ', '.join(x.dropna().unique()),
            'CAI': lambda x: ', '.join(x.dropna().astype(str).unique()),
            'MAXAM': lambda x: ', '.join(x.dropna().astype(str).unique())
        }).reset_index()

        df_modelos_llantas_grouped = df_modelos.merge(df_modelos_llantas_grouped, on='Equipment Description', how='left')

        # Añadir un identificador al inicio de la página
        st.markdown('<div id="inicio"></div>', unsafe_allow_html=True)

        st.title("Catálogo de Equipos Mineros")
        st.subheader('Equipos Mineros usados en México')

        # Obtener opciones únicas para los filtros
        tipos_equipo = df_modelos_llantas_grouped['Tipo'].unique()
        fabricantes = df_modelos_llantas_grouped['Fabricante'].unique()

        st.divider()

        # Función de devolución de llamada para restablecer los filtros
        def reset_filters():
            st.session_state["tipo_seleccionado"] = "Todos"
            st.session_state["fabricante_seleccionado"] = "Todos"
            st.session_state["search_query"] = ""

        # Añadir widgets de selección para los filtros
        tipo_seleccionado = st.selectbox("Selecciona el tipo de equipo", ["Todos"] + list(tipos_equipo), key="tipo_seleccionado")
        fabricante_seleccionado = st.selectbox("Selecciona el fabricante", ["Todos"] + list(fabricantes), key="fabricante_seleccionado")

        # Añadir un buscador para filtrar la lista de modelos
        search_query = st.text_input("Buscar modelo de equipo", key="search_query")

        # Filtrar el DataFrame en función de las selecciones del usuario
        if tipo_seleccionado != "Todos":
            df_modelos_llantas_grouped = df_modelos_llantas_grouped[df_modelos_llantas_grouped['Tipo'] == tipo_seleccionado]
        if fabricante_seleccionado != "Todos":
            df_modelos_llantas_grouped = df_modelos_llantas_grouped[df_modelos_llantas_grouped['Fabricante'] == fabricante_seleccionado]
        if search_query:
            df_modelos_llantas_grouped = df_modelos_llantas_grouped[df_modelos_llantas_grouped['Equipment Description'].str.contains(search_query, case=False, na=False)]

        # Botón de Limpiar Filtros
        st.button("Limpiar Filtros", on_click=reset_filters)

        st.divider()

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

            # Mostrar tabla de Valvulas en el sidebar dentro de un expander
            if not df_valvulas_filtrado.empty:
                with st.sidebar.expander("**Válvulas**"):
                    st.table(df_valvulas_filtrado[['Marca Valvula', 'Componente', 'Nombre KT', 'Codigo KT']].set_index('Codigo KT'))

            # Filtrar datos de la tabla Rines
            df_rines_filtrado = df_rines[df_rines['Equipment Description'] == row['Equipment Description']]

            # Mostrar tabla de Rines en el sidebar dentro de un expander
            if not df_rines_filtrado.empty:
                with st.sidebar.expander("**Rines**"):
                    st.table(df_rines_filtrado[['Marca Rin', 'Componentes', 'Descripcion Sugerida', 'Codigo KT']].set_index('Codigo KT'))

            # Filtrar datos de la tabla Equipos_Mina
            df_equipos_mina_filtrado = df_equipos_mina[df_equipos_mina['Equipment Description'] == row['Equipment Description']]

            # Agrupar datos de la tabla Equipos_Mina por 'Mina' y contar el número de equipos
            df_equipos_mina_grouped = df_equipos_mina_filtrado.groupby('Mina').agg({'No Equipos': 'sum'}).reset_index()

            # Mostrar el número de equipos por mina en el sidebar dentro de un expander
            if not df_equipos_mina_grouped.empty:
                with st.sidebar.expander("**Equipos por Mina**"):
                    st.table(df_equipos_mina_grouped.set_index('Mina'))

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

        # Añadir el botón de "Volver arriba"
        st.markdown("""
            <style>
            .scroll-to-top {
                position: fixed;
                bottom: 100px;
                right: 50px;
                background-color: #ff5e00;
                color: white;
                border: none;
                border-radius: 50%;
                padding: 10px 15px;
                font-size: 15px;
                cursor: pointer;
                z-index: 1000;
                opacity: 0.5;
                transition: opacity 0.4s;
            }
            .scroll-to-top:hover {
                opacity: 1;
            }        
            </style>
            <a href="#inicio">
                <button class="scroll-to-top">
                    ↑
                </button>
            </a>
            """, unsafe_allow_html=True)

    @st.cache_data
    def load_plantas_data():
        with open('Plantas.json') as f:
            return json.load(f)

    # Inicializar la variable de estado para la planta seleccionada
    if 'selected_planta' not in st.session_state:
        st.session_state.selected_planta = None

    with tab2:
        # Cargar datos del archivo JSON
        plantas_data = load_plantas_data()

        st.title("Plantas Mineras en México")
        st.divider()
        # Filtros para las plantas
        col1, col2, col3 = st.columns(3)
        with col1:
            surface = st.checkbox("Surface", value=True, key="surface")
        with col2:
            underground = st.checkbox("Underground", value=True, key="underground")
        with col3:
            quarry = st.checkbox("Quarry", value=True, key="quarry")
        
        st.divider()

        # Filtrar los datos en función de las selecciones del usuario
        filtered_plantas = [
            planta for planta in plantas_data
            if (st.session_state.surface and planta['Surface'] == 'si') or
               (st.session_state.underground and planta['Underground'] == 'si') or
               (st.session_state.quarry and planta['Quarry'] == 'si')
        ]

        # Crear el mapa
        if filtered_plantas:
            m = folium.Map(
                location=[filtered_plantas[0]['LATITUDE'], filtered_plantas[0]['LONGITUDE']],
                zoom_start=5,
                tiles='https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
                attr='&copy; <a href="https://opentopomap.org">OpenTopoMap</a> contributors'
            )

            # Añadir marcadores al mapa
            for idx, planta in enumerate(filtered_plantas):
                folium.Marker(
                    location=[planta['LATITUDE'], planta['LONGITUDE']],
                    popup=folium.Popup(f"{planta['PLANT_NAME']} ({planta['OPER_NAME']})", parse_html=True),
                    tooltip=planta['PLANT_NAME'],
                    icon=folium.Icon(color='green' if planta['Surface'] == 'si' else 'red' if planta['Underground'] == 'si' else 'blue', icon="person-digging", prefix='fa')
                ).add_to(m)

            # Añadir LatLngPopup al mapa
            folium.LatLngPopup().add_to(m)

            # Mostrar el mapa en Streamlit
            map_data = st_folium(m, use_container_width=True, zoom=5)

            # Mostrar detalles de la planta seleccionada en el sidebar
            if map_data and map_data['last_clicked']:
                last_clicked = map_data['last_clicked']
                for planta in filtered_plantas:
                    if planta['LATITUDE'] == last_clicked['lat'] and planta['LONGITUDE'] == last_clicked['lng']:
                        st.session_state.selected_planta = planta
                        break

            if st.session_state.selected_planta is not None:
                selected_planta = st.session_state.selected_planta
                st.sidebar.title(f"Detalles de la planta: {selected_planta['PLANT_NAME']}")
                st.sidebar.write(f"**Operador:** {selected_planta['OPER_NAME']}")
                st.sidebar.write(f"**Dirección:** {selected_planta['Direccion']}")
                st.sidebar.write(f"**Ciudad:** {selected_planta['Ciudad']}")
                st.sidebar.write(f"**Estado:** {selected_planta['Estado']}")
                st.sidebar.write(f"**Web:** {selected_planta['WEB']}")
        else:
            st.write("No hay plantas que coincidan con los filtros seleccionados.")