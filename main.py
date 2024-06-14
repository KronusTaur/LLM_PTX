import streamlit as st
import os
import numpy as np
import pandas as pd
from PIL import Image, ImageEnhance
import cv2
import requests
from io import BytesIO
from ppt_data_gen import slide_data_gen
from ppt_gen import ppt_gen
from diffusers import StableDiffusionPipeline
import torch
from rgb2colorname import rgb_to_colorname
def rgb2hex(r, g, b):
    return '#{:02x}{:02x}{:02x}'.format(r, g, b)

st.title(" AI помощник создания презентаций")
uploaded_files = st.file_uploader("Choose a txt file", accept_multiple_files=True)
for uploaded_file in uploaded_files:
    filename, filename_extension = os.path.splitext(uploaded_file.name)
    if filename_extension == '.txt':
        text = open(uploaded_file.name, 'r').read()  
        output = st.text_area("Output is: ", text, height=220)   
    if filename_extension == '.doc':
        ...
    if filename_extension == '.md':
        ...

slide_count = st.text_input("Введите количество слайдов:")
url_tab = st.tabs(["Image URL"])
# with upload_tab:
#     img_file = st.file_uploader("Upload Art", key="file_uploader")
#     if img_file is not None:
#         try:
#             img = Image.open(img_file)
#         except:
#             st.error("The file you uploaded does not seem to be a valid image. Try uploading a png or jpg file.")

#     if st.session_state.get("image_url"):
#         st.warning("To use the file uploader, remove the image URL first.")
#     with st.expander("🖼  Artwork", expanded=True):
#         st.image(img, use_column_width=True)


# with url_tab:
url = st.text_input("Image URL", key="image_url")
if url != "":
    try:
        response = requests.get(url)
        img = Image.open(BytesIO(response.content))
        img = ImageEnhance.Color(img)
        img = img.enhance(2.5)
        enhancement_range = {
        # "enhancement_type": [min, max, step_size]

            "Color": [0., 5., 0.2], 
            "Sharpness": [0., 3., 0.2], 
            "Contrast": [0.5, 1.5, 0.1], 
            "Brightness": [0.5, 1.5, 0.1]
        }

        enhancement_categories = enhancement_range.keys()

        # put adjustment sliders inside an expander 
        enh_expander = st.sidebar.expander("Image Enhancements", expanded=False)

        # create a reset button that resets all enhancements to default value (1.0)
        with enh_expander:
            if st.button("reset"):
                for cat in enhancement_categories:
                    if f"{cat}_enhancement" in st.session_state:
                        st.session_state[f"{cat}_enhancement"] = 1.0

        # create sliders for each enhancement category using the dictionary values (min, max, step_size)
        enhancement_factor_dict = {
            cat: enh_expander.slider(f"{cat} Enhancement", 
                                    value=1., 
                                    min_value=enhancement_range[cat][0], 
                                    max_value=enhancement_range[cat][1], 
                                    step=enhancement_range[cat][2],
                                    key=f"{cat}_enhancement")
            for cat in enhancement_categories
        }
        from PIL import ImageEnhance

        for cat in enhancement_categories:
            img = getattr(ImageEnhance, cat)(img)
            img = img.enhance(enhancement_factor_dict[cat])

        with st.expander("🖼  Artwork", expanded=True):
            st.image(img, use_column_width=True)
            img.save('background_user.jpg')
        cap = cv2.resize(np.array(img), (340,480))
        red = []
        green = []
        blue = []
        for x in range (0,340,1):
            for y in range(0,480,1):
                color = cap[y,x]
                blue.append(int(color[0]))
                green.append(int(color[1]))
                red.append(int(color[2]))
        df_rgb = pd.DataFrame({"R": red, "G": green, "B": blue}).sample(n=100)
        from sklearn.cluster import KMeans

        palette_size = st.sidebar.number_input("palette size", min_value=1, max_value=20, value=5, step=1, 
                                                                                    help="Основные цвета .")
        model = KMeans(n_clusters=palette_size)
        clusters = model.fit_predict(df_rgb)
        palette = model.cluster_centers_.astype(int).tolist()
        columns = st.columns(palette_size)
        presentation_colors = []
        for i, col in enumerate(columns):
            with col:        
                result_color = str(rgb2hex(palette[i][2], palette[i][1], palette[i][0])).upper()
                st.session_state[f"col_{i}"]= st.color_picker(label=str(i), value=result_color, key=f"pal_{i}")
                presentation_colors.append(result_color)
    except:
        st.error("The URL does not seem to be valid.")


if st.button("Cгенерировать фон"):
    prompt = "Draw a background for technical presentation witр predominant colors " + str(rgb_to_colorname(palette[0]))
    model_id = "runwayml/stable-diffusion-v1-5"
    pipe = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float16)
    pipe = pipe.to("cuda")
    image = pipe(prompt).images[0] 
    st.image(image, use_column_width=True)
    image.save('background_neuro.jpg')

if st.button("Cгенерировать презентацию"):
    data = slide_data_gen(output, slide_count)
    if os.path.exists('background_neuro.jpg') == True:
        os.rename('background_neuro.jpg', 'background.jpg')
    else:
        os.rename('background_user.jpg', 'background.jpg')
    ppt_file = ppt_gen(data)
    file_name = f"Presentation.pptx"
    st.download_button(
        label="Скачать презентацию",
        data=ppt_file,
        file_name=file_name,
        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
    )
    if os.path.exists('background_neuro.jpg') == True:
        os.remove('background_neuro.jpg')
    if os.path.exists('background_user.jpg') == True:
        os.remove('background_user.jpg')
    # os.remove('background_neuro.jpg')
