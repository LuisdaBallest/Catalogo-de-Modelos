import streamlit as st
from PIL import Image, UnidentifiedImageError
import os
import pandas as pd
import sshtunnel
from mysql.connector import connect

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
    @st.cache_data
    def load_data_from_db():
        try:
            # Configurar timeouts para el túnel SSH
            sshtunnel.SSH_TIMEOUT = 15.0
            sshtunnel.TUNNEL_TIMEOUT = 15.0
            
            # Crear el túnel SSH
            with sshtunnel.SSHTunnelForwarder(
                ('ssh.pythonanywhere.com'),
                ssh_username=st.secrets["ssh_username"], 
                ssh_password=st.secrets["ssh_password"],
                remote_bind_address=(st.secrets["remote_bind_address"], 3306)
            ) as tunnel:
                # Conectar a la base de datos a través del túnel
                conn = connect(
                    user=st.secrets["user"],
                    password=st.secrets["password"],
                    host='127.0.0.1', 
                    port=tunnel.local_bind_port,
                    database=st.secrets["database"]  # Ajusta el nombre de la base de datos si es necesario
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
        
        except Exception as e:
            st.error(f"Error al conectar a la base de datos: {e}")
            
            # Si hay error, intentar cargar desde archivos CSV locales
            try:
                st.warning("Intentando cargar datos desde archivos locales...")
                df_modelos = pd.DataFrame()
                df_llantas = pd.DataFrame()
                df_valvulas = pd.DataFrame()
                df_rines = pd.DataFrame()
                df_equipos_mina = pd.DataFrame()
                
                # Intenta cargar desde CSV si existen
                try:
                    df_modelos = pd.read_csv("data/modelos.csv")
                    st.success("Datos de Modelos cargados correctamente")
                except:
                    st.warning("No se pudieron cargar los datos de Modelos")
                    
                try:
                    df_llantas = pd.read_csv("data/llantas.csv")
                    st.success("Datos de Llantas cargados correctamente")
                except:
                    st.warning("No se pudieron cargar los datos de Llantas")
                    
                try:
                    df_valvulas = pd.read_csv("data/valvulas.csv")
                    st.success("Datos de Válvulas cargados correctamente")
                except:
                    st.warning("No se pudieron cargar los datos de Válvulas")
                    
                try:
                    df_rines = pd.read_csv("data/rines.csv")
                    st.success("Datos de Rines cargados correctamente")
                except:
                    st.warning("No se pudieron cargar los datos de Rines")
                    
                try:
                    df_equipos_mina = pd.read_csv("data/equipos_mina.csv")
                    st.success("Datos de Equipos Mina cargados correctamente")
                except:
                    st.warning("No se pudieron cargar los datos de Equipos Mina")
                    
                return df_modelos, df_llantas, df_valvulas, df_rines, df_equipos_mina
                
            except Exception as e2:
                st.error(f"Error al cargar datos locales: {e2}")
                return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    # Cargar los datos aquí, fuera de la definición de la función
    df_modelos, df_llantas, df_valvulas, df_rines, df_equipos_mina = load_data_from_db()

    # Verificar que los DataFrames necesarios no estén vacíos
    if not df_modelos.empty and not df_llantas.empty:
        # Crear dos pestañas para búsqueda por modelo o por llanta
        tab1, tab2 = st.tabs(["Búsqueda por Modelo", "Búsqueda por Llanta"])
        
        with tab1:
            # Añadir un identificador al inicio de la página
            st.markdown('<div id="inicio"></div>', unsafe_allow_html=True)

            st.title("Catálogo de Equipos Mineros")
            st.subheader('Equipos Mineros usados en México')

            # Agrupar por 'Equipment Description' y concatenar las descripciones y códigos de artículo
            df_modelos_llantas_grouped = df_llantas.groupby('Equipment Description').agg({
                'Desc Michelin': lambda x: ', '.join(x.dropna().unique()),
                'Desc MAXAM': lambda x: ', '.join(x.dropna().unique()),
                'CAI': lambda x: ', '.join(x.dropna().astype(str).unique()),
                'MAXAM': lambda x: ', '.join(x.dropna().astype(str).unique())
            }).reset_index()

            df_modelos_llantas_grouped = df_modelos.merge(df_modelos_llantas_grouped, on='Equipment Description', how='left')

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
            filtered_df = df_modelos_llantas_grouped.copy()
            if tipo_seleccionado != "Todos":
                filtered_df = filtered_df[filtered_df['Tipo'] == tipo_seleccionado]
            if fabricante_seleccionado != "Todos":
                filtered_df = filtered_df[filtered_df['Fabricante'] == fabricante_seleccionado]
            if search_query:
                filtered_df = filtered_df[filtered_df['Equipment Description'].str.contains(search_query, case=False, na=False)]

            # Botón de Limpiar Filtros
            st.button("Limpiar Filtros", on_click=reset_filters)

            st.divider()

            # Mostrar imágenes correspondientes a cada modelo de equipo en filas y columnas
            num_columns = 3  # Número de columnas
            rows = [filtered_df[i:i + num_columns] for i in range(0, filtered_df.shape[0], num_columns)]

            # Altura fija para las imágenes
            fixed_height = 500

            # Función para mostrar detalles en el sidebar
            def mostrar_detalles(row):
                st.sidebar.title(f"Detalles del equipo: {row['Equipment Description']}")
                image_path = os.path.join('./images', row['Imagen']) 
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
                if pd.notna(row['Desc Michelin']) and pd.notna(row['CAI']):
                    desc_michelin_list = row['Desc Michelin'].split(', ')
                    cai_list = row['CAI'].split(', ')
                    for desc_michelin, cai in zip(desc_michelin_list, cai_list):
                        st.sidebar.write(f"**Descripción Michelin:** {desc_michelin} ({cai})")

                # Añadir descripciones MAXAM con MAXAM
                if pd.notna(row['Desc MAXAM']) and pd.notna(row['MAXAM']):
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
                if not df_equipos_mina_filtrado.empty:
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
        
        with tab2:
            st.title("Búsqueda por Llanta")
            st.subheader("Encuentra modelos de equipo por código o descripción de llanta")
            st.divider()

            # Crear listas de todas las descripciones y códigos disponibles de llantas
            all_michelin_desc = df_llantas['Desc Michelin'].dropna().unique()
            all_maxam_desc = df_llantas['Desc MAXAM'].dropna().unique()
            all_cai_codes = df_llantas['CAI'].dropna().astype(str).unique()
            all_maxam_codes = df_llantas['MAXAM'].dropna().astype(str).unique()

            # Combinar todas las opciones para el selector
            all_tire_options = []
            for desc in all_michelin_desc:
                all_tire_options.append(f"MICHELIN - {desc}")
            for desc in all_maxam_desc:
                all_tire_options.append(f"MAXAM - {desc}")
            for code in all_cai_codes:
                all_tire_options.append(f"CAI - {code}")
            for code in all_maxam_codes:
                all_tire_options.append(f"MAXAM Code - {code}")
            
            # Opción de búsqueda libre
            search_type = st.radio("Método de búsqueda", ["Seleccionar de la lista", "Búsqueda por texto"])
            
            if search_type == "Seleccionar de la lista":
                selected_tire = st.selectbox("Selecciona una llanta", [""] + sorted(all_tire_options))
            else:
                selected_tire = st.text_input("Buscar por descripción o código de llanta")

            # Filtrar modelos según la llanta seleccionada
            if selected_tire:
                filtered_models = []
                
                if search_type == "Seleccionar de la lista":
                    if selected_tire.startswith("MICHELIN - "):
                        desc = selected_tire.replace("MICHELIN - ", "")
                        filtered_equipment = df_llantas[df_llantas['Desc Michelin'] == desc]['Equipment Description'].unique()
                    elif selected_tire.startswith("MAXAM - "):
                        desc = selected_tire.replace("MAXAM - ", "")
                        filtered_equipment = df_llantas[df_llantas['Desc MAXAM'] == desc]['Equipment Description'].unique()
                    elif selected_tire.startswith("CAI - "):
                        code = selected_tire.replace("CAI - ", "")
                        filtered_equipment = df_llantas[df_llantas['CAI'].astype(str) == code]['Equipment Description'].unique()
                    elif selected_tire.startswith("MAXAM Code - "):
                        code = selected_tire.replace("MAXAM Code - ", "")
                        filtered_equipment = df_llantas[df_llantas['MAXAM'].astype(str) == code]['Equipment Description'].unique()
                else:
                    # Búsqueda por texto en todos los campos relevantes
                    query = selected_tire.lower()
                    michelin_match = df_llantas[df_llantas['Desc Michelin'].str.lower().fillna('').str.contains(query)]
                    maxam_match = df_llantas[df_llantas['Desc MAXAM'].str.lower().fillna('').str.contains(query)]
                    cai_match = df_llantas[df_llantas['CAI'].astype(str).str.lower().str.contains(query)]
                    maxam_code_match = df_llantas[df_llantas['MAXAM'].astype(str).str.lower().str.contains(query)]
                    
                    # Combinar todos los resultados
                    all_matches = pd.concat([michelin_match, maxam_match, cai_match, maxam_code_match])
                    filtered_equipment = all_matches['Equipment Description'].unique()
                
                # Obtener los detalles completos de los equipos filtrados
                filtered_models = df_modelos[df_modelos['Equipment Description'].isin(filtered_equipment)]
                
                # Mostrar resultados
                st.divider()
                if len(filtered_models) > 0:
                    st.write(f"Se encontraron {len(filtered_models)} modelos compatibles con esta llanta:")
                    
                    # Mostrar imágenes correspondientes a cada modelo de equipo en filas y columnas
                    num_columns = 3  # Número de columnas
                    rows = [filtered_models[i:i + num_columns] for i in range(0, filtered_models.shape[0], num_columns)]
                    
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
                                
                                # Necesitamos una key única para cada botón
                                if st.button(f"Ver detalles de {row_data['Equipment Description']}", key=f"tire_details_{row_data.name}"):
                                    # Necesitamos obtener los datos completos con llantas para mostrar detalles
                                    full_row_data = df_modelos_llantas_grouped[df_modelos_llantas_grouped['Equipment Description'] == row_data['Equipment Description']].iloc[0]
                                    mostrar_detalles(full_row_data)
                else:
                    st.warning("No se encontraron modelos compatibles con esta llanta.")
            else:
                st.info("Selecciona una llanta para ver los modelos compatibles.")
    else:
        st.error("No hay datos disponibles para mostrar en el catálogo.")