import streamlit as st
import pandas as pd
from PIL import Image
import os

# Cargar datos desde el archivo Excel
df_modelos_llantas = pd.read_excel('./data/Modelos.xlsx')
df_inventario = pd.read_excel('./data/Inventario.xlsx')

# Agrupar por 'Equipment Description' y concatenar las descripciones
df_modelos_llantas_grouped = df_modelos_llantas.groupby('Equipment Description').agg({
    'Manufacturer': 'first',
    'Imagen': 'first',
    'Desc Michelin': lambda x: ', '.join(x.dropna().unique()),
    'Desc MAXAM': lambda x: ', '.join(x.dropna().unique()),
    'CAI': 'first',
    'MAXAM': 'first'
}).reset_index()

st.title("Catálogo de Equipos Mineros")
st.subheader('Equipos Mineros usados en México')

# Añadir un buscador para filtrar la lista de modelos
search_query = st.text_input("Buscar modelo de equipo")

# Filtrar el DataFrame en función de la entrada del usuario
if search_query:
    df_modelos_llantas_grouped = df_modelos_llantas_grouped[df_modelos_llantas_grouped['Equipment Description'].str.contains(search_query, case=False, na=False)]

# Mostrar imágenes correspondientes a cada modelo de equipo en columnas
num_columns = 3 
columns = st.columns(num_columns)

# Altura fija para las imágenes
fixed_height = 500

# Función para buscar en el inventario
def buscar_inventario(codigo_articulo):
    df_filtrado = df_inventario[df_inventario['Código de artículo'] == codigo_articulo]
    if not df_filtrado.empty:
        df_agrupado = df_filtrado.groupby('Almacén')['Física disponible'].sum().reset_index()
        return df_agrupado
    return pd.DataFrame(columns=['Almacén', 'Física disponible'])

# Función para mostrar detalles en el sidebar
def mostrar_detalles(row):
    st.sidebar.title(f"Detalles del equipo: {row['Equipment Description']}")
    image_path = os.path.join('./images', row['Imagen'])  # Asegúrate de tener una columna 'Imagen' en tu Excel
    if os.path.exists(image_path):
        image = Image.open(image_path)
        # Redimensionar la imagen manteniendo la relación de aspecto
        aspect_ratio = image.width / image.height
        new_width = int(fixed_height * aspect_ratio)
        resized_image = image.resize((new_width, fixed_height))
        st.sidebar.image(resized_image, caption=row['Equipment Description'], use_container_width=True)
    else:
        st.sidebar.write("Imagen no disponible")

    st.sidebar.write(f"**Fabricante:** {row['Manufacturer']}")
    st.sidebar.write(f"**Descripción Michelin:** {row['Desc Michelin']}")
    st.sidebar.write(f"**Descripción MAXAM:** {row['Desc MAXAM']}")

    # Buscar en el inventario para CAI
    if pd.notna(row['CAI']):
        df_inventario_cai = buscar_inventario(row['CAI'])
        st.sidebar.write(f"**Inventario físico disponible {row['Desc Michelin']} ({row['CAI']}):**")
        for _, row_inv in df_inventario_cai.iterrows():
            st.sidebar.write(f"Almacén: {row_inv['Almacén']}, Cantidad disponible: {row_inv['Física disponible']}")

    # Buscar en el inventario para MAXAM
    if pd.notna(row['MAXAM']):
        df_inventario_maxam = buscar_inventario(row['MAXAM'])
        st.sidebar.write(f"**Inventario físico disponible {row['Desc MAXAM']} ({row['MAXAM']}):**")
        for _, row_inv in df_inventario_maxam.iterrows():
            st.sidebar.write(f"Almacén: {row_inv['Almacén']}, Cantidad disponible: {row_inv['Física disponible']}")

for index, row in df_modelos_llantas_grouped.iterrows():
    col = columns[index % num_columns]
    with col:
        st.markdown(f"<h3>{row['Equipment Description']}</h3>", unsafe_allow_html=True)
        image_path = os.path.join('./images', row['Imagen'])
        
        if os.path.exists(image_path):
            image = Image.open(image_path)
            # Redimensionar la imagen manteniendo la relación de aspecto
            aspect_ratio = image.width / image.height
            new_width = int(fixed_height * aspect_ratio)
            resized_image = image.resize((new_width, fixed_height))
            st.image(resized_image, caption=row['Equipment Description'], use_container_width=True)
        else:
            st.write("Imagen no disponible")
        
        if st.button(f"Ver detalles de {row['Equipment Description']}", key=f"details_{index}"):
            mostrar_detalles(row)