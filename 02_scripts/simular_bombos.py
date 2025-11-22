import pandas as pd
import numpy as np


#Importamos lista de selecciones clasificadas y dejamos slots para las de repechaje

df_clasificados = pd.read_excel('01_datos_brutos/Clasificados_WC_26.xlsx', 
                                sheet_name='Clasificados')

df_repechaje_uefa = pd.read_excel('01_datos_brutos/Clasificados_WC_26.xlsx', 
                                sheet_name='Repechaje_UEFA')

df_repechaje_fifa = pd.read_excel('01_datos_brutos/Clasificados_WC_26.xlsx', 
                                sheet_name='Repechaje_FIFA')

#Cargamos Power Ranking FIFA

df_power_ranking = pd.read_csv('01_datos_brutos/FIFA_PR_19_11_2025.csv').drop(columns=['Unnamed: 7'])

#Generamos los repechajes

def generar_repechaje_uefa(df, random_state=None):
    ganadores = df.groupby('llave', group_keys=False).sample(1, random_state=random_state)

    ganadores = pd.merge(ganadores, 
                         df_power_ranking[['codigo', 'puntos_totales']], 
                         on='codigo', 
                         how='left')
    
    return ganadores  # devuelve todas las columnas


def generar_repechaje_fifa(df, random_state = None):

    ganadores = df.groupby('llave').sample(1, random_state = random_state)

    ganadores = pd.merge(ganadores, 
                         df_power_ranking[['codigo', 'puntos_totales']], 
                         on='codigo', 
                         how='left')

    return ganadores


#Simulamos bombos

def asignar_bombos(df_clasificados, 
                   clasificados_uefa = None,
                   clasificados_fifa = None,
                   random_state = None):
    # Merge
    df_merged = pd.merge(df_clasificados, df_power_ranking[['codigo', 'puntos_totales']],
                          on='codigo', 
                          how='left')
    df_sorted = df_merged.sort_values(by='puntos_totales', ascending=False).reset_index(drop=True)

    # Bombo 1: anfitriones + mejores restantes hasta 12
    anfitriones=['MEX','USA','CAN']
    bombo1 = df_sorted[df_sorted['codigo'].isin(anfitriones)].copy()
    restantes = df_sorted[~df_sorted['codigo'].isin(anfitriones)]
    bombo1 = pd.concat([bombo1, restantes.head(12 - len(bombo1))])
    bombo1['bombo'] = 1

    # Actualizamos restantes
    restantes = restantes.drop(restantes.head(9).index)

    # Bombo 2
    bombo2 = restantes.head(12).copy()
    bombo2['bombo'] = 2
    restantes = restantes.drop(restantes.head(12).index)

    # Bombo 3
    bombo3 = restantes.head(12).copy()
    bombo3['bombo'] = 3
    restantes = restantes.drop(restantes.head(12).index)

    # Bombo 4 inicial
    bombo4 = restantes.copy()
    bombo4['bombo'] = 4
    bombo4['repechaje'] = 0

    # Ganadores de repechaje UEFA
    if clasificados_uefa is None:
        ganadores_uefa = generar_repechaje_uefa(df_repechaje_uefa, random_state=random_state)
        ganadores_uefa['repechaje'] = 1
        ganadores_uefa['anfitrion'] = 0
    else:
        ganadores_uefa = df_repechaje_uefa[df_repechaje_uefa['codigo'].isin(clasificados_uefa)].copy()
        ganadores_uefa['repechaje'] = 1
        ganadores_uefa['anfitrion'] = 0

    # Ganadores de repechaje FIFA
    if clasificados_fifa is None:
        ganadores_fifa = generar_repechaje_fifa(df_repechaje_fifa, random_state=random_state)
        ganadores_fifa['repechaje'] = 1
        ganadores_fifa['anfitrion'] = 0
    else:
        ganadores_fifa = df_repechaje_fifa[df_repechaje_fifa['codigo'].isin(clasificados_fifa)].copy()
        ganadores_fifa['repechaje'] = 1
        ganadores_fifa['anfitrion'] = 0

    # Concatenamos repechajes al bombo 4
    bombo4_concat = pd.concat([bombo4, ganadores_uefa, ganadores_fifa], ignore_index=True)
    bombo4_concat['bombo'] = 4

    # Limpiamos columnas y aseguramos tipos
    columnas_base = ['pais', 'codigo', 'confederacion', 'anfitrion','puntos_totales', 'bombo']
    columnas_bombo4 = columnas_base + ['repechaje']
    bombo4_concat = bombo4_concat[columnas_bombo4]

    bombo4_concat['repechaje'] = bombo4_concat['repechaje'].fillna(0).astype(int)
    bombo4_concat['anfitrion'] = bombo4_concat['anfitrion'].fillna(0).astype(int)

    # Concatenamos todos los bombos
    df_final = pd.concat([bombo1, bombo2, bombo3, bombo4_concat]).reset_index(drop=True)
    df_final['repechaje'] = df_final['repechaje'].fillna(0).astype(int)

    return df_final

df_bombos = asignar_bombos(df_clasificados, random_state= 42)