import pandas as pd
import numpy as np
import easyocr
import streamlit as st
from streamlit_option_menu import option_menu
from PIL import Image
import re
import io
import os
import psycopg2


def img_to_text(img):
    img_1=Image.open(img)
    img_array = np.array(img_1)
    reader = easyocr.Reader(['en'])
    text = reader.readtext(img_array,detail=0)
    return text,img_1 

def extracted_text(texts):
    extrd_dict = {"NAME":[],"DESIGNATION":[],"COMPANY_NAME":[],"CONTACT":[],"EMAIL":[],
                  "WEBSITE":[],"ADDRESS":[],"PINCODE":[]}
    extrd_dict["NAME"].append(texts[0])
    extrd_dict["DESIGNATION"].append(texts[1])

    for i in range(2,len(texts)):
        if texts[i].startswith("+") or (texts[i].replace("-","").isdigit() and '-' in texts[i]):
            extrd_dict["CONTACT"].append(texts[i])

        elif "@" in texts[i] and ".com" in texts[i]:
            small =texts[i].lower()
            extrd_dict["EMAIL"].append(small)

        elif "WWW" in texts[i] or "www" in texts[i] or "Www" in texts[i] or "wWw" in texts[i] or "wwW" in texts[i]:
            small = texts[i].lower()
            extrd_dict["WEBSITE"].append(texts[i])
            

        elif ("Tamil Nadu" in texts[i]  or "TamilNadu" in texts[i]) or texts[i].isdigit():
            extrd_dict["PINCODE"].append(texts[i]) 
        
        elif re.match(r'^[A-Za-z]',texts[i]):
            extrd_dict["COMPANY_NAME"].append(texts[i])

        else:
            remove_colon = re.sub(r'[,;]', '', texts[i])
            extrd_dict["ADDRESS"].append(remove_colon)

    for key,value in extrd_dict.items():
        if len(value)>0:
            concadenate = ' '.join(value)
            extrd_dict[key] = [concadenate]
        else:
            value = 'NA'
            extrd_dict[key] = [value]

    return extrd_dict
                         


# streamlit part
st.set_page_config(layout= "wide")

st.title("EXTRACTING BUSINESS CARD DATA WITH OCR")
st.write("")

with st.sidebar:
    select= option_menu("Main Menu",["Home", "Upload & Modify", "Delete"])

if select == "Home":
  st.markdown("### :green[**Technologies Used :**] Python,easy OCR, Streamlit, SQL, Pandas")



  st.write(
            "### :green[**About :**] Bizcard is a Python application designed to extract information from business cards.")
  st.write(
            '### The main purpose of Bizcard is to automate the process of extracting key details from business card images, such as the name, designation, company, contact information, and other relevant data. By leveraging the power of OCR (Optical Character Recognition) provided by EasyOCR, Bizcard is able to extract text from the images.')


if select=="Upload & Modify":
    img = st.file_uploader(label="Upload the image", type=['png', 'jpg', 'jpeg'], label_visibility="hidden")

    if img is not None:
        st.image(img,width=300)

        text_img,img_1 = img_to_text(img)

        text_dict = extracted_text(text_img)
        df = pd.DataFrame(text_dict)
        

        # CONVERTING IMAGE INTO BYTES
        image_bytes = io.BytesIO()
        img_1.save(image_bytes,format="PNG")
        image_data = image_bytes.getvalue()

        # creating dictionery

        data = {"image":[image_data]}
        df_1 = pd.DataFrame(data)
        concat_df = pd.concat([df,df_1],axis=1)
        
        
        method = st.radio("Select The Options",["Preview","Modify"])

        if method == "None":
            st.write("")

        if method == "Preview":
            st.image(img,width=300)
            st.dataframe(concat_df) 

        
        
        elif method == "Modify":


            col1,col2 = st.columns(2)

            with col1:

                modfd_name = st.text_input("Name",text_dict["NAME"][0])
                modfd_dsntn = st.text_input("Designation",text_dict["DESIGNATION"][0])
                modfd_cn = st.text_input("Company_name",text_dict["COMPANY_NAME"][0])
                modfd_cntct = st.text_input("Contact",text_dict["CONTACT"][0])

                concat_df["NAME"]=modfd_name,
                concat_df["DESIGNATION"]=modfd_dsntn,
                concat_df["COMPANY_NAME"]=modfd_cn,
                concat_df["CONTACT"]=modfd_cntct

            with col2:

                modfy_email = st.text_input("Email",text_dict["EMAIL"][0])
                modfy_wbste = st.text_input("Website",text_dict["WEBSITE"][0])
                modfy_adrss = st.text_input("Adress",text_dict["ADDRESS"][0])
                modfy_pncde = st.text_input("Pincode",text_dict["PINCODE"][0]) 

                concat_df["EMAIL"]=modfy_email,
                concat_df["WEBSITE"]=modfy_wbste,
                concat_df["ADDRESS"]=modfy_adrss,
                concat_df["PINCODE"]=modfy_pncde

            col1,col2 = st.columns(2)

            with col1:
                button_3 = st.button("Save",use_container_width= True)

           
            if button_3:
                    
            
                kalai = psycopg2.connect(host='localhost', port=5432,
                            user='postgres', password='root',database = 'bizcard')
                cursor = kalai.cursor()
                kalai.commit()

                create_query = '''create table if not exists bizcard_data(NAME varchar(250),
                                                                        DESIGNATION varchar(250),
                                                                        COMPANY_NAME text,
                                                                        CONTACT text,
                                                                            EMAIL text,
                                                                            WEBSITE text,
                                                                            ADDRESS text,
                                                                            PINCODE text,
                                                                            image text)'''
                cursor.execute(create_query)
                kalai.commit()
                insert_query = '''insert into bizcard_data(NAME,DESIGNATION,COMPANY_NAME,CONTACT,EMAIL,WEBSITE,ADDRESS,PINCODE,IMAGE)
                                values(%s,%s,%s,%s,%s,%s,%s,%s,%s)'''

                for index,row in concat_df.iterrows():
                    values = (row["NAME"],
                            row["DESIGNATION"],
                            row["COMPANY_NAME"],
                            row["CONTACT"],
                            row["EMAIL"],
                            row["WEBSITE"],
                            row["ADDRESS"],
                            row["PINCODE"],
                            row["image"]
                            )
                    cursor.execute(insert_query,values)
                    kalai.commit()
                    st.success("SUCCESSFULLY UPLODED")
                    st.snow()
            
elif select == "Delete":
    kalai = psycopg2.connect(host='localhost', port=5432,
                            user='postgres', password='root',database = 'bizcard')
    cursor = kalai.cursor()
    

    col1,col2 = st.columns(2)

    with col1:
        cursor.execute("select NAME from bizcard_data")
        kalai.commit()
        table1 = cursor.fetchall()

        names = []

        for i in table1:
            names.append(i[0])
        
        name_select= st.selectbox("Select the Name",options= names)

    with col2:
        cursor.execute(f"select DESIGNATION from bizcard_data Where NAME='{name_select}'")
        kalai.commit()
        table2 = cursor.fetchall()

        designation = []
        
        for j in table2:
            designation.append(j[0])

        Designation_select= st.selectbox("Select the Designation",options= designation)

    if name_select and Designation_select:
        col1,col2,col3 = st.columns(3)

        with col1:
            st.write(f"Selected Name : {name_select}")
            st.write("")
            st.write("")

            st.write(f"Selected Designation : {Designation_select}")

        with col2:
            st.write("")
            st.write("")
            st.write("")
            st.write("")

            remove = st.button("Delete",use_container_width=True)

            if remove:
                cursor.execute(f"DELETE FROM bizcard_data WHERE NAME ='{name_select}' AND DESIGNATION = '{Designation_select}'")
                kalai.commit()

                st.warning("DELETED")


        
            
        


                    
                    