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
    """
    Evalúa si asignar `equipo_actual` al `grupo_target` dejaría al menos un grupo válido
    para cada uno de los equipos restantes del bombo.

    Si algún equipo futuro queda sin grupo disponible, regresa False.
    Si todos conservan al menos una opción, regresa True.
    """

    # 1. Crear copia independiente del estado actual de los grupos
    #    (para simular sin alterar el sorteo real)
    grupos_sim = {g: lst.copy() for g, lst in grupos_dict.items()}

    # Obtener confederación del equipo actual para validar constraints
    conf_actual = df_bombos.loc[df_bombos['codigo'] == equipo_actual, 'confederacion'].iloc[0]

    # 2. Simular colocar el equipo actual en el grupo_target
    grupos_sim[grupo_target].append({
        "codigo": equipo_actual,
        "slot": None,   # Slot no importa para lookahead
        "conf": conf_actual
    })

    # 3. Para cada equipo restante del bombo:
    #    verificar si tiene al menos un grupo posible
    for eq in equipos_restantes:

        conf_eq = df_bombos.loc[df_bombos['codigo'] == eq, 'confederacion'].iloc[0]
        grupo_viable = False

        # Revisar grupo por grupo en orden alfabético
        for g in bombos_slots.keys():

            # 3a. Validar límite máximo de equipos permitido para este bombo
            if len(grupos_sim[g]) >= numero_de_bombo:
                continue

            # 3b. Validar constraint de confederación simulando eq en g
            if checker_validez_grupo(g, eq, grupos_sim, verbose=False):
                grupo_viable = True
                break

        # Si este equipo NO tiene ningún grupo disponible → falla el lookahead
        if not grupo_viable:
            return False

    # Si todos los equipos tienen al menos una opción → la asignación es segura
    return True


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


print("----BOMBO 2----")

grupos = list(bombos_slots.keys())  # A→L

eq_bombo_2 = df_bombos[df_bombos['bombo'] == 2].copy()

for _ in grupos:
    if eq_bombo_2.empty:
        break

    # Sacamos un equipo del bombo 2
    eq_sorteado = eq_bombo_2['codigo'].sample(1).iloc[0]
    eq_bombo_2 = eq_bombo_2[eq_bombo_2['codigo'] != eq_sorteado]

    grupo_asignado = None

    for g in grupos:

        # 1) Máximo 2 equipos en este bombo
        if len(grupos_dict[g]) >= 2:
            continue

        # 2) Constraint normal de confederación
        if not checker_validez_grupo(g, eq_sorteado, grupos_dict):
            continue

        # 3) Lookahead — ¿ponerlo aquí ahorca los grupos para los restantes?
        if not lookahead(
            grupo_target=g,
            equipo_actual=eq_sorteado,
            equipos_restantes=list(eq_bombo_2['codigo']),
            grupos_dict=grupos_dict,
            bombos_slots=bombos_slots,
            numero_de_bombo=2
        ):
            print(f"Lookahead: {eq_sorteado} NO puede ir en grupo {g}, causaría dead-end. Reasignando...")
            continue

        # 4) Si pasa todo → este es su grupo
        grupo_asignado = g
        break

    if grupo_asignado is None:
        raise ValueError(f"No hay grupo válido para {eq_sorteado}. Revisa constraints!")

    # ---- Asignación real ----
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



#Bombo 3:

print("----BOMBO 3----")

grupos = list(bombos_slots.keys())  # A→L

eq_bombo_3 = df_bombos[df_bombos['bombo'] == 3].copy()

for _ in grupos:
    if eq_bombo_3.empty:
        break

    # Sacamos un equipo del bombo 3
    eq_sorteado = eq_bombo_3['codigo'].sample(1).iloc[0]
    eq_bombo_3 = eq_bombo_3[eq_bombo_3['codigo'] != eq_sorteado]

    grupo_asignado = None

    for g in grupos:

        # 1) Máximo 3 equipos en este bombo
        if len(grupos_dict[g]) >= 3:
            continue

        # 2) Constraint normal de confederación
        if not checker_validez_grupo(g, eq_sorteado, grupos_dict):
            continue

        # 3) Lookahead — ¿ponerlo aquí ahorca los grupos para los restantes?
        if not lookahead(
            grupo_target=g,
            equipo_actual=eq_sorteado,
            equipos_restantes=list(eq_bombo_3['codigo']),
            grupos_dict=grupos_dict,
            bombos_slots=bombos_slots,
            numero_de_bombo=3
        ):
            print(f"Lookahead: {eq_sorteado} NO puede ir en grupo {g}, causaría dead-end. Reasignando...")
            continue

        # 4) Si pasa todo → este es su grupo
        grupo_asignado = g
        break

    if grupo_asignado is None:
        raise ValueError(f"No hay grupo válido para {eq_sorteado}. Revisa constraints!")

    # ---- Asignación real ----
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


#Bombo 4:

print("----BOMBO 4----")

grupos = list(bombos_slots.keys())  # A→L

eq_bombo_4 = df_bombos[df_bombos['bombo'] == 4].copy()

for _ in grupos:
    if eq_bombo_4.empty:
        break

    # Sacamos un equipo del bombo 3
    eq_sorteado = eq_bombo_4['codigo'].sample(1).iloc[0]
    eq_bombo_4 = eq_bombo_4[eq_bombo_4['codigo'] != eq_sorteado]

    grupo_asignado = None

    for g in grupos:

        # 1) Máximo 4 equipos en este bombo
        if len(grupos_dict[g]) >= 4:
            continue

        # 2) Constraint normal de confederación
        if not checker_validez_grupo(g, eq_sorteado, grupos_dict):
            continue

        # 3) Lookahead — ¿ponerlo aquí ahorca los grupos para los restantes?
        if not lookahead(
            grupo_target=g,
            equipo_actual=eq_sorteado,
            equipos_restantes=list(eq_bombo_4['codigo']),
            grupos_dict=grupos_dict,
            bombos_slots=bombos_slots,
            numero_de_bombo=4
        ):
            print(f"Lookahead: {eq_sorteado} NO puede ir en grupo {g}, causaría dead-end. Reasignando...")
            continue

        # 4) Si pasa todo → este es su grupo
        grupo_asignado = g
        break

    if grupo_asignado is None:
        raise ValueError(f"No hay grupo válido para {eq_sorteado}. Revisa constraints!")

    # ---- Asignación real ----
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

# Crear lista de filas
filas = []
for grupo, equipos in grupos_dict.items():
    for eq in equipos:
        filas.append({
            "Grupo": grupo,
            "Equipo": eq["codigo"],
            "Slot": eq["slot"],
            "Confederacion": eq["conf"]
        })

# Convertir a DataFrame
df_tabla = pd.DataFrame(filas)

# Mostrar tabla
for grupo in sorted(df_tabla['Grupo'].unique()):
    print(f"\n--- Grupo {grupo} ---")

    tabla = (
        df_tabla[df_tabla['Grupo'] == grupo]
        .sort_values(by="Slot")
        .drop(columns=["Grupo"])
        .reset_index(drop=True)
    )

    print(tabla)
