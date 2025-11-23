import pandas as pd
import numpy as np
import random
import string


from simular_bombos import df_bombos

#Definimos funciones
def checker_validez_grupo(grupo, eq_sorteado, grupos_dict, verbose=True):
    #Confederacion del sorteado
    conf_sorteado = df_bombos.loc[df_bombos['codigo'] == eq_sorteado, 'confederacion'].iloc[0]

    #Equipos en grupo
    equipos_en_grupo = grupos_dict[grupo]

    #Extraer confederaciones ya asignadas
    confs = [e['conf'] for e in equipos_en_grupo]

    #Contamos apariciones de confederacion
    conf_counts = pd.Series(confs).value_counts()

    #-----Constraints FIFA------

    if conf_sorteado != 'UEFA':
        if conf_sorteado in conf_counts.index:
            if verbose:
                print(f"Otro equipo de {conf_sorteado}. Reasignando...")
            return False
    else:
        #UEFA permite máximo 2
        if conf_counts.get('UEFA', 0) >= 2:
            if verbose:
                print("Dos equipos de UEFA actuales. Reasignando...")
            return False
        
    return True


def lookahead(grupo_target, equipo_actual, equipos_restantes, grupos_dict, bombos_slots, numero_de_bombo):
    # 1. Copia de los grupos
    grupos_sim = {g: lst.copy() for g, lst in grupos_dict.items()}
    conf_actual = df_bombos.loc[df_bombos['codigo'] == equipo_actual, 'confederacion'].iloc[0]
    grupos_sim[grupo_target].append({"codigo": equipo_actual, "slot": None, "conf": conf_actual})

    # 2. Función recursiva para asignar equipos restantes
    def asignar_restantes(restantes, grupos):
        if not restantes:
            return True  # todos asignados

        eq = restantes[0]
        conf_eq = df_bombos.loc[df_bombos['codigo'] == eq, 'confederacion'].iloc[0]

        for g in grupos.keys():
            if len(grupos[g]) >= numero_de_bombo:
                continue
            if not checker_validez_grupo(g, eq, grupos, verbose=False):
                continue

            # Asignación temporal
            grupos[g].append({"codigo": eq, "slot": None, "conf": conf_eq})
            if asignar_restantes(restantes[1:], grupos):
                return True  # éxito
            grupos[g].pop()  # deshacer asignación si no funciona

        return False  # ningún grupo válido para este equipo

    return asignar_restantes(equipos_restantes, grupos_sim)

def sortear_bombo_1(df_bombos):
    #Generamos esqueleto
    grupos = list(string.ascii_uppercase[:12])  # A-L
    asignaciones_sorteo = {}

    #Generamos los bombos de cada grupo (slots)
    bombos_slots = {}
    for grupo in grupos:
        bombos_slots[grupo] = [f"{grupo}{i}" for i in range(1, 5)]

    #Asignaciones de Anfitriones
    anfitriones = {
        "MEX": "A1",
        "CAN": "B1",
        "USA": "D1"
    }

    for eq, slot in anfitriones.items():
        conf = df_bombos.loc[df_bombos['codigo'] == eq, 'confederacion'].iloc[0]
        grupo = slot[0]       # "A", "B", "D"
        
        asignaciones_sorteo[eq] = {
            "grupo": grupo,
            "slot": slot,
            "conf": conf
        }

    #Retiramos las bolitas rojas de Anfitriones
    bombos_slots['A'].remove("A1")
    bombos_slots['B'].remove("B1")
    bombos_slots['D'].remove("D1")

    #Equipos restantes bombo 1
    eq_restantes_bombo_1 = df_bombos[
        (~df_bombos['codigo'].isin(['MEX', 'USA', 'CAN'])) &
        (df_bombos['bombo'] == 1)
    ]

    print("----BOMBO 1: CABEZAS DE GRUPO----")

    for grupo in bombos_slots.keys():
        if grupo not in ('A', 'B', 'D'):
            # Selecciona equipo
            eq_sorteado = eq_restantes_bombo_1['codigo'].sample(1).iloc[0]  # Bolita país
            fila_eq = eq_restantes_bombo_1[eq_restantes_bombo_1['codigo'] == eq_sorteado].iloc[0]
            conf = fila_eq['confederacion']  # Ajusta nombre si es distinto

            # Quitamos bolita del bombo de países
            eq_restantes_bombo_1 = eq_restantes_bombo_1[eq_restantes_bombo_1['codigo'] != eq_sorteado]

            # Asignamos grupo y slot
            slot = grupo + "1"
            asignaciones_sorteo[eq_sorteado] = {
                "grupo": grupo,
                "slot": slot,
                "conf": conf
            }

            # Quitamos slot del bombo de grupos
            bombos_slots[grupo].remove(slot)

            print(f"{eq_sorteado} ({conf}) cabeza de Grupo {grupo} → slot {slot}")

    grupos_dict = {g: [] for g in grupos}

    for equipo, info in asignaciones_sorteo.items():
        grupos_dict[info["grupo"]].append({
            "codigo": equipo,
            "slot": info["slot"],
            "conf": info["conf"]
        })

    return grupos_dict, asignaciones_sorteo, bombos_slots


def sortear_bombo_n(n_bombo,
                    df_bombos,
                    bombos_slots,
                    grupos_dict,
                    asignaciones_sorteo): 

    print(f"----BOMBO {n_bombo}----")

    grupos = list(bombos_slots.keys())  # A→L

    eq_bombo = df_bombos[df_bombos['bombo'] == n_bombo].copy()

    for _ in grupos:
        if eq_bombo.empty:
            break
        
        # Sacamos un equipo del bombo 2
        eq_sorteado = eq_bombo['codigo'].sample(1).iloc[0]
        eq_bombo = eq_bombo[eq_bombo['codigo'] != eq_sorteado]

        grupo_asignado = None

        for g in grupos:

            #1) Máximo de equipos por grupo en este bombo
            if len(grupos_dict[g]) >= n_bombo:
                continue

            #2) Constraint confederaciones
            if not checker_validez_grupo(g, eq_sorteado, grupos_dict):
                continue

            #3) Lookahead - ¿Ponerlo aquí ahorca los grupos para los restantes?
            if not lookahead(
                grupo_target=g,
                equipo_actual=eq_sorteado,
                equipos_restantes=list(eq_bombo['codigo']),
                grupos_dict=grupos_dict,
                bombos_slots=bombos_slots,
                numero_de_bombo=n_bombo
            ):
                print(f"Lookahead: {eq_sorteado} NO puede ir en grupo {g}, causaría dead-end. Reasignando...")
                continue

            #4) Si pasa todo -> este es su grupo
            grupo_asignado = g
            break

        if grupo_asignado is None:
            raise ValueError(f"No hay grupo válido para {eq_sorteado}. Revisa constraints!")
        
        #----Asignación Real----
        slot_sorteado = random.choice(bombos_slots[grupo_asignado])
        bombos_slots[grupo_asignado].remove(slot_sorteado)

        conf_sorteado = df_bombos.loc[df_bombos['codigo'] == eq_sorteado, 'confederacion'].iloc[0]

        grupos_dict[grupo_asignado].append({
            "codigo": eq_sorteado,
            "slot": slot_sorteado,
            "conf": conf_sorteado
        })

        asignaciones_sorteo[eq_sorteado] = {
            "grupo": grupo_asignado,
            "slot": slot_sorteado,
            "conf": conf_sorteado
        }

        print(f"{eq_sorteado} → Grupo {grupo_asignado}, slot {slot_sorteado}")

    return grupos_dict, asignaciones_sorteo, bombos_slots

