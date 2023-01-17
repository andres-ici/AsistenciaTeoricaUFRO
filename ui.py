import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account
import gspread_dataframe as gd
import plotly.express as px



# Connect to Google Sheets

credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=[
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ],
)


client = gspread.authorize(credentials=credentials)



#credentials = ServiceAccountCredentials.f(st.secrets["gcp_service_account"])

#client = gspread.authorize(credentials=credentials)


#Funciones

def convert_df(df):
   return df.to_csv(index=False).encode('utf-8')

def verificar1(data):

    valor = [data.iloc[0,0]]

    if valor[0] == "ID de la reunión":
        return 1
    else:
        return 0

def verificar2(data):

    valor = [data.iloc[0,0]]

    if valor[0] == "First Name":
        return 1
    else:
        return 0


#Titulo y subir archivos

st.title("Proyecto asistencia teórica")

st.header("Ingresar archivos")

asistenciaFile = st.file_uploader("Asistencia", type="csv")
registroFile = st.file_uploader("Registro", type="csv")

#Cuando se suben los archivos

if (asistenciaFile and registroFile) is not None: #Varificar si se suben los archivos

    #Trabajo de analisis de datos Pandas

    asistencia = pd.read_csv(asistenciaFile, header=None)
    registro = pd.read_csv(registroFile, header=None)

    if verificar1(asistencia) or verificar2(registro): #Verifica el formato de los csv subidos

        duracionTotal = [asistencia.iloc[1,5]]
        maximo =  int(duracionTotal[0])
        minimo = int(duracionTotal[0])*0.9*0.5
        fecha = [asistencia.iloc[1,2]]
        fecha = fecha[0]

        datosAsistencia = asistencia.iloc[3:,[1,2]]
        datosRegistro = registro.iloc[1:,[0,1,5,2]]

        datosAsistencia.rename(columns={1:"Correo", 2:"Tiempo"}, inplace = True)
        datosRegistro.rename(columns={0:"Nombre", 1:"Apellido", 5:"Matrícula", 2:"Correo"}, inplace = True)

        datosMerge = pd.merge(datosAsistencia, datosRegistro, how = "outer")
        datosMerge = datosMerge.reindex(columns=["Correo", "Matrícula", "Nombre", "Apellido", "Tiempo"])
        datosMerge["Tiempo"] = datosMerge["Tiempo"].astype("int64")
        datosMerge["Estado"] = ["Presente" if a >= minimo else "Ausente" for a in datosMerge["Tiempo"]]

        presentes = datosMerge[datosMerge["Tiempo"] >= minimo]
        ausentes = datosMerge[datosMerge["Tiempo"] < minimo]

        #Mostrar resultados y descargar

        #Variables

        total = datosMerge["Tiempo"].size
        totalPresentes = presentes["Tiempo"].size
        totalAusentes = ausentes["Tiempo"].size
        porcentajePresentes = (totalPresentes * 100)/total
        porcentajeAusentes = (totalAusentes * 100)/total

        st.header("Resultados")

        st.subheader("Resumen")

        st.write("<p style='margin:2px'>Fecha de la reunión</p>\n<p style='font-size:25px;margin-botton:20px;'>{}</p>".format(fecha), unsafe_allow_html=True)

        col11, col22, col33 = st.columns(3)

        col33.metric("", "")
        col11.metric("Tiempo total", "{} min".format(maximo))
        col22.metric("Tiempo mínimo para estar presente", "{} min".format(minimo))

        col1, col2, col3 = st.columns(3)
        col1.metric("Participantes", total,"", delta_color="off")
        col2.metric("Presentes", totalPresentes,  "{}%".format(porcentajePresentes))
        col3.metric("Ausentes", totalAusentes,  "{}%". format(porcentajeAusentes))

        fig = px.pie(datosMerge, values=[totalPresentes, totalAusentes], names=["Presentes", "Ausentes"], hole=0.4,  title="Grafico de asistencia")

        fig.update_traces(textposition= "inside", textinfo= "percent", textfont=dict(size=25))

        st.plotly_chart(fig)
        
        archivoClass = convert_df(datosMerge)
        archivoPresentes = convert_df(presentes)
        archivoAusentes = convert_df(ausentes)

        st.subheader("Alumnos clasificados")
        st.write(datosMerge) 
        st.download_button("Descargar", archivoClass, "Alumnos Clasificados {}.csv".format(fecha), "text/csv", key='Clasificados-csv')
        st.subheader("Alumnos presentes")
        st.write(presentes) 
        st.download_button("Descargar", archivoPresentes, "Alumnos Clasificados {}.csv".format(fecha), "text/csv", key='presentes-csv')
        st.subheader("Alumnos ausentes")
        st.write(ausentes)
        st.download_button("Descargar", archivoAusentes, "Alumnos Clasificados {}.csv".format(fecha), "text/csv", key='ausentes-csv')

        #Subir a Google drive

        st.header("Subir datos a Google Drive")

        colDate, colModulo = st.columns(2)

        with colDate:

            date = st.date_input("Fecha de clase")

        with colModulo:

            modulo = st.selectbox("Módulo", ("1", "2", "3", "4", "5"))

        if st.button('Subir datos'):

            if modulo == "1":
                sheet = client.open_by_url(st.secrets["modulo1"])
            elif modulo == "2":
                sheet = client.open_by_url(st.secrets["modulo2"])
            elif modulo == "3":
                sheet = client.open_by_url(st.secrets["modulo3"])
            elif modulo == "4":
                sheet = client.open_by_url(st.secrets["modulo4"])
            elif modulo == "5":
                sheet = client.open_by_url(st.secrets["modulo5"])

            worksheet_list = sheet.worksheets()

            try: #Verifica si existe la worksheet

                worksheet = sheet.worksheet(str(date))

            except: #Crea la worksheet en caso de ser necesario 

                worksheet = sheet.add_worksheet(title=str(date), rows=100, cols=30)

            gd.set_with_dataframe(worksheet, datosMerge)
            st.write("Datos subidos")
    
    else:

        st.error("El formato de los archivos es incorrecto")

    
