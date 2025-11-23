"""
Sorteo FIFA World Cup 2026 - Simulación Interactiva con NiceGUI

Este script implementa una aplicación web interactiva para simular el sorteo de la Copa Mundial de la FIFA 2026.
Utiliza la librería NiceGUI para el frontend y se integra con scripts de lógica de sorteo (`simular_bombos` y `simular_sorteo_func`)
para garantizar que se cumplan todas las restricciones geográficas y de bombos.

Características principales:
- Interfaz reactiva y visualmente atractiva.
- Simulación asíncrona para permitir animaciones sin bloquear el servidor.
- Visualización de banderas de países mediante FlagCDN.
- Registro en tiempo real de los eventos del sorteo.
"""

import asyncio
import random
import string
import pandas as pd
from nicegui import ui, app
from simular_bombos import df_bombos
from simular_sorteo_func import checker_validez_grupo, lookahead

# --- Configuración y Estilos ---
# Definimos estilos CSS en línea para mantener el código autocontenido y facilitar la personalización.
HEADER_STYLE = "font-size: 2em; font-weight: bold; color: #111; text-align: center; margin-bottom: 20px;"
CARD_STYLE = "min-width: 150px; min-height: 215px; background-color: #f5f5f5; border-radius: 10px; padding: 10px; transition: all 0.3s ease; border: 2px solid #6101eb;"
CARD_STYLE_COMPLETE = "min-width: 150px; min-height: 215px; background-color: #f5f5f5; border-radius: 10px; padding: 10px; transition: all 0.3s ease; border: 2.5px solid #00c752;"
SLOT_STYLE = "padding: 4px; margin: 2px; border-bottom: 1px solid #444; font-size: 0.9em; width: 100%;"
HIGHLIGHT_STYLE = "background-color: #00c752;"
DISCARDED_STYLE = "background-color: #ea1e63;"  # Nuevo color para descarte

# --- Datos y Mapeos ---
# Diccionario para mapear códigos FIFA (3 letras) a códigos ISO (2 letras) para obtener las banderas.
# Esto es necesario porque FlagCDN utiliza códigos ISO.
FIFA_TO_ISO = {
    'AFG': 'af', 'ALB': 'al', 'ALG': 'dz', 'ASA': 'as', 'AND': 'ad', 'ANG': 'ao', 'AIA': 'ai', 'ATG': 'ag',
    'ARG': 'ar', 'ARM': 'am', 'ARU': 'aw', 'AUS': 'au', 'AUT': 'at', 'AZE': 'az', 'BAH': 'bs', 'BHR': 'bh',
    'BAN': 'bd', 'BRB': 'bb', 'BLR': 'by', 'BEL': 'be', 'BLZ': 'bz', 'BEN': 'bj', 'BER': 'bm', 'BHU': 'bt',
    'BOL': 'bo', 'BIH': 'ba', 'BOT': 'bw', 'BRA': 'br', 'VGB': 'vg', 'BRU': 'bn', 'BUL': 'bg', 'BFA': 'bf',
    'BDI': 'bi', 'CAM': 'kh', 'CMR': 'cm', 'CAN': 'ca', 'CPV': 'cv', 'CAY': 'ky', 'CTA': 'cf', 'CHA': 'td',
    'CHI': 'cl', 'CHN': 'cn', 'TPE': 'tw', 'COL': 'co', 'COM': 'km', 'CGO': 'cg', 'COK': 'ck', 'CRC': 'cr',
    'CRO': 'hr', 'CUB': 'cu', 'CUW': 'cw', 'CYP': 'cy', 'CZE': 'cz', 'DEN': 'dk', 'DJI': 'dj', 'DMA': 'dm',
    'DOM': 'do', 'COD': 'cd', 'ECU': 'ec', 'EGY': 'eg', 'SLV': 'sv', 'ENG': 'gb-eng', 'EQG': 'gq', 'ERI': 'er',
    'EST': 'ee', 'ETH': 'et', 'FRO': 'fo', 'FIJ': 'fj', 'FIN': 'fi', 'FRA': 'fr', 'GAB': 'ga', 'GAM': 'gm',
    'GEO': 'ge', 'GER': 'de', 'GHA': 'gh', 'GIB': 'gi', 'GRE': 'gr', 'GRN': 'gd', 'GUM': 'gu', 'GUA': 'gt',
    'GUI': 'gn', 'GNB': 'gw', 'GUY': 'gy', 'HAI': 'ht', 'HON': 'hn', 'HKG': 'hk', 'HUN': 'hu', 'ISL': 'is',
    'IND': 'in', 'IDN': 'id', 'IRN': 'ir', 'IRQ': 'iq', 'ISR': 'il', 'ITA': 'it', 'CIV': 'ci', 'JAM': 'jm',
    'JPN': 'jp', 'JOR': 'jo', 'KAZ': 'kz', 'KEN': 'ke', 'PRK': 'kp', 'KOR': 'kr', 'KUW': 'kw', 'KGZ': 'kg',
    'LAO': 'la', 'LVA': 'lv', 'LBN': 'lb', 'LES': 'ls', 'LBR': 'lr', 'LBY': 'ly', 'LIE': 'li', 'LTU': 'lt',
    'LUX': 'lu', 'MAC': 'mo', 'MKD': 'mk', 'MAD': 'mg', 'MWI': 'mw', 'MAS': 'my', 'MDV': 'mv', 'MLI': 'ml',
    'MLT': 'mt', 'MTN': 'mr', 'MRI': 'mu', 'MEX': 'mx', 'MDA': 'md', 'MNG': 'mn', 'MNE': 'me', 'MSR': 'ms',
    'MAR': 'ma', 'MOZ': 'mz', 'MYA': 'mm', 'NAM': 'na', 'NEP': 'np', 'NED': 'nl', 'NCL': 'nc', 'NZL': 'nz',
    'NCA': 'ni', 'NIG': 'ne', 'NGA': 'ng', 'NIR': 'gb-nir', 'NOR': 'no', 'OMA': 'om', 'PAK': 'pk', 'PLE': 'ps',
    'PAN': 'pa', 'PNG': 'pg', 'PAR': 'py', 'PER': 'pe', 'PHI': 'ph', 'POL': 'pl', 'POR': 'pt', 'PUR': 'pr',
    'QAT': 'qa', 'IRL': 'ie', 'ROU': 'ro', 'RUS': 'ru', 'RWA': 'rw', 'SKN': 'kn', 'LCA': 'lc', 'VIN': 'vc',
    'SAM': 'ws', 'SMR': 'sm', 'STP': 'st', 'KSA': 'sa', 'SCO': 'gb-sct', 'SEN': 'sn', 'SRB': 'rs', 'SEY': 'sc',
    'SLE': 'sl', 'SIN': 'sg', 'SVK': 'sk', 'SVN': 'si', 'SOL': 'sb', 'SOM': 'so', 'RSA': 'za', 'ESP': 'es',
    'SRI': 'lk', 'SDN': 'sd', 'SUR': 'sr', 'SWE': 'se', 'SUI': 'ch', 'SYR': 'sy', 'TAH': 'pf', 'TJK': 'tj',
    'TAN': 'tz', 'THA': 'th', 'TLS': 'tl', 'TOG': 'tg', 'TGA': 'to', 'TRI': 'tt', 'TUN': 'tn', 'TUR': 'tr',
    'TKM': 'tm', 'TCA': 'tc', 'UGA': 'ug', 'UKR': 'ua', 'UAE': 'ae', 'USA': 'us', 'URU': 'uy', 'VIR': 'vi',
    'UZB': 'uz', 'VAN': 'vu', 'VEN': 've', 'VIE': 'vn', 'WAL': 'gb-wls', 'YEM': 'ye', 'ZAM': 'zm', 'ZIM': 'zw'
}

# --- Clase de Gestión de Estado ---
class SorteoManager:
    """
    Gestiona el estado completo de una sesión de sorteo.
    
    Mantiene la información sobre los grupos, los equipos asignados, los slots disponibles
    y el registro de eventos. Al encapsular el estado aquí, facilitamos el reinicio
    del sorteo sin necesidad de recargar la página completa.
    """
    def __init__(self):
        self.reset()

    def reset(self):
        """Reinicia el estado a los valores iniciales para un nuevo sorteo."""
        self.grupos = list(string.ascii_uppercase[:12])  # Grupos A-L
        self.grupos_dict = {g: [] for g in self.grupos}  # Equipos en cada grupo
        # Slots disponibles (ej: A1, A2, A3, A4)
        self.bombos_slots = {g: [f"{g}{i}" for i in range(1, 5)] for g in self.grupos}
        self.asignaciones = {}
        self.current_bombo = 1
        self.processing = False  # Flag para evitar múltiples ejecuciones simultáneas
        self.logs = []
        self.finished = False
        self.current_team = None  # Equipo actual sorteado

    def log(self, message):
        """Agrega un mensaje al registro de eventos."""
        self.logs.append(message)
        if len(self.logs) > 50:  # Mantenemos solo los últimos 50 mensajes
            self.logs.pop(0)

# --- Página Principal ---
@ui.page('/')
def index():
    """
    Define la estructura y lógica de la página principal de la aplicación.
    
    En NiceGUI, las funciones decoradas con @ui.page se ejecutan para cada nuevo cliente
    que se conecta. Esto significa que cada usuario tiene su propia instancia de `SorteoManager`
    y su propio estado visual.
    """
    ui.colors(primary='#6101eb', secondary='#b486ff', accent='#00c752', positive='#00c752')
    ui.add_head_html('<style>body { background-color: #d1d1d1; }</style>')

    # Estado local para esta sesión
    state = SorteoManager()
    group_cards = {}
    log_container = None
    draw_button = None
    current_team_banner = None
    bombo_list_container = None  # Nuevo contenedor para la lista fija

    # Use mutable objects for pause/step flags to avoid UnboundLocalError
    paused = {'value': False}
    step_requested = {'value': False}
    auto_play = {'value': False}
    speed_multiplier = {'value': 1.0}  # Multiplicador de velocidad (1.0 = velocidad normal)

    def pause_resume():
        paused['value'] = not paused['value']
        auto_play['value'] = False

    def step_once():
        step_requested['value'] = True
        auto_play['value'] = False

    def play_auto():
        paused['value'] = False
        auto_play['value'] = True

    async def maybe_pause():
        while paused['value'] and not step_requested['value'] and not auto_play['value']:
            await asyncio.sleep(0.1)
        if step_requested['value']:
            step_requested['value'] = False

    # --- Funciones Auxiliares de UI ---
    def refresh_groups_ui(only_group=None):
        """
        Actualiza la visualización de los grupos.
        Si only_group se especifica, solo actualiza ese grupo.
        """
        grupos_a_actualizar = [only_group] if only_group else state.grupos
        for g in grupos_a_actualizar:
            card = group_cards.get(g)
            if card:
                # Cambia el marco a verde si el grupo está completo
                if len(state.grupos_dict[g]) == 4:
                    card.style(CARD_STYLE_COMPLETE)
                else:
                    card.style(CARD_STYLE)
                card.clear()
                with card:
                    ui.label(f"Grupo {g}").style("font-weight: bold; font-size: 1.2em; color: #333; margin-bottom: 5px;")
                    teams = state.grupos_dict[g]
                    slot_map = {}
                    for t in teams:
                        slot_num = int(t['slot'][-1])
                        slot_map[slot_num] = t
                    for i in range(1, 5):
                        team_data = slot_map.get(i)
                        with ui.row().classes('items-center no-wrap').style(SLOT_STYLE):
                            ui.label(f"{g}{i}").style("font-weight: bold; margin-right: 6px; min-width: 25px; color: #555;")
                            if team_data:
                                code = team_data['codigo']
                                iso = FIFA_TO_ISO.get(code, '').lower()
                                if iso:
                                    ui.image(f"https://flagcdn.com/h24/{iso}.png").style("width: 24px; height: auto; margin-right: 8px; border-radius: 2px; box-shadow: 0 1px 2px rgba(0,0,0,0.2);")
                                else:
                                    ui.icon('flag', size='xs').style("margin-right: 8px; color: #ccc;")
                                ui.label(f"{code}").style("font-weight: bold; color: #000; margin-right: 4px;")
                                ui.label(f"({team_data['conf']})").style("font-size: 0.8em; color: #666;")
                            else:
                                ui.label("---").style("color: #aaa;")

    def update_current_team_banner(finalizado=False):
        """Actualiza el banner fijo con el equipo actual sorteado y el número de bombo."""
        if current_team_banner:
            current_team_banner.clear()
            with current_team_banner:
                if finalizado:
                    ui.label("Sorteo finalizado").style(
                        "font-size: 1.2em; font-weight: bold; color: #b486ff; padding: 8px;"
                    )
                else:
                    bombo = state.current_bombo
                    if bombo in [1, 2, 3, 4]:
                        equipo_txt = f"Equipo actual sorteado: {state.current_team}" if state.current_team else "Esperando sorteo..."
                        ui.label(f"{equipo_txt}   |   Bombo: {bombo}").style(
                            "font-size: 1.2em; font-weight: bold; color: #b486ff; padding: 8px;"
                        )
                    else:
                        ui.label("Esperando sorteo...").style(
                            "font-size: 1.2em; font-weight: bold; color: #b486ff; padding: 8px;"
                        )

    def update_bombo_list_ui(descolorear=None, equipo_actual=None):
        """
        Muestra solo la fila de equipos del bombo actual debajo del banner.
        Si descolorear, ese equipo se muestra gris aunque no esté asignado.
        Si equipo_actual, lo colorea especial mientras se asigna.
        Cuando ya se seleccionó el equipo del bombo, se colorea gris tenue.
        """
        if bombo_list_container:
            bombo_list_container.clear()
            bombo = state.current_bombo
            if bombo in [1, 2, 3, 4]:
                equipos_bombo = list(df_bombos[df_bombos['bombo'] == bombo]['codigo'])
                sorteados = set(state.asignaciones.keys())
                with bombo_list_container:
                    with ui.row().classes('w-full justify-center').style("flex-wrap:wrap;"):
                        for eq in equipos_bombo:
                            # Si es el equipo actual, lo coloreamos especial
                            if equipo_actual == eq:
                                color = "#fff"
                                border = "2px solid #faae96"
                                bg = "#faae96"
                            # Si ya fue sorteado, gris tenue
                            elif eq in sorteados or descolorear == eq:
                                color = "#bbb"
                                border = "2px solid #bbb"
                                bg = "#ededed"
                            else:
                                color = "#00c752"
                                border = "2px solid #b486ff"
                                bg = "#6101eb"
                            ui.label(eq).style(
                                f"font-size:1em;margin:2px 8px;padding:4px 12px;border-radius:6px;"
                                f"color:{color};background:{bg};border:{border};"
                                "font-weight:bold;"
                            )
            # Si no hay bombo válido, no muestra nada

    async def highlight_group(group_name):
        """
        Aplica un efecto visual temporal a un grupo para indicar actividad.
        
        Args:
            group_name (str): La letra del grupo a resaltar (ej: 'A').
        """
        if group_name in group_cards:
            card = group_cards[group_name]
            card.style(HIGHLIGHT_STYLE)
            await asyncio.sleep(0.5 * speed_multiplier['value'])
            # Restaura al estilo correcto según si está completo o no
            if len(state.grupos_dict[group_name]) == 4:
                card.style(CARD_STYLE_COMPLETE)
            else:
                card.style(CARD_STYLE)
            # Pausa adicional antes de continuar con la asignación
            await asyncio.sleep(0.15 * speed_multiplier['value'])

    async def highlight_discarded_group(group_name):
        """
        Aplica un efecto visual temporal a un grupo descartado por constraints.
        """
        if group_name in group_cards:
            card = group_cards[group_name]
            card.style(DISCARDED_STYLE)
            await asyncio.sleep(0.3 * speed_multiplier['value'])
            # Restaura al estilo correcto según si está completo o no
            if len(state.grupos_dict[group_name]) == 4:
                card.style(CARD_STYLE_COMPLETE)
            else:
                card.style(CARD_STYLE)

    # --- Funciones de Lógica del Sorteo (Clausuras sobre `state`) ---
    
    async def run_bombo_1():
        """
        Ejecuta la lógica de sorteo para el Bombo 1 (Cabezas de Serie).
        
        El Bombo 1 tiene reglas especiales:
        1. Los anfitriones (MEX, CAN, USA) se asignan a grupos predefinidos.
        2. El resto de cabezas de serie se asignan aleatoriamente a los grupos restantes.
        """
        state.log("--- INICIANDO BOMBO 1 ---")
        update_bombo_list_ui()
        state.current_bombo = 1
        update_current_team_banner()
        update_bombo_list_ui()
        await asyncio.sleep(0.35 * speed_multiplier['value'])  # Espera antes de iniciar el primer equipo
        await maybe_pause()
        
        # 1. Asignar Anfitriones (Regla fija)
        anfitriones = {"MEX": "A1", "CAN": "B1", "USA": "D1"}
        
        for eq, slot in anfitriones.items():
            await maybe_pause()
            await asyncio.sleep(0.35 * speed_multiplier['value'])
            state.current_team = eq
            update_current_team_banner()
            update_bombo_list_ui(equipo_actual=eq)
            await asyncio.sleep(0.35 * speed_multiplier['value'])
            conf = df_bombos.loc[df_bombos['codigo'] == eq, 'confederacion'].iloc[0]
            grupo = slot[0]
            # Previsualiza el marco verde si el grupo va a quedar completo
            if len(state.grupos_dict[grupo]) == 3:
                group_cards[grupo].style(CARD_STYLE_COMPLETE)
            # Highlight antes de colocar el país (ahora incluye la pausa interna)
            await highlight_group(grupo)
            # Actualizar estado
            state.asignaciones[eq] = {"grupo": grupo, "slot": slot, "conf": conf}
            state.grupos_dict[grupo].append({"codigo": eq, "slot": slot, "conf": conf})
            if slot in state.bombos_slots[grupo]:
                state.bombos_slots[grupo].remove(slot)
            state.log(f"ANFITRIÓN: {eq} asignado a {grupo} ({slot})")
            refresh_groups_ui(only_group=grupo)
            await asyncio.sleep(0.2 * speed_multiplier['value'])
        # 2. Resto del Bombo 1
        eq_restantes_bombo_1 = df_bombos[
            (~df_bombos['codigo'].isin(['MEX', 'USA', 'CAN'])) &
            (df_bombos['bombo'] == 1)
        ]
        
        # Grupos disponibles (excluyendo los de anfitriones)
        grupos_disponibles = [g for g in state.bombos_slots.keys() if g not in ('A', 'B', 'D')]
        
        for grupo in grupos_disponibles:
            await maybe_pause()
            await asyncio.sleep(0.35 * speed_multiplier['value'])
            eq_sorteado = eq_restantes_bombo_1['codigo'].sample(1).iloc[0]
            state.current_team = eq_sorteado
            update_current_team_banner()
            update_bombo_list_ui(equipo_actual=eq_sorteado)
            await asyncio.sleep(0.35 * speed_multiplier['value'])
            fila_eq = eq_restantes_bombo_1[eq_restantes_bombo_1['codigo'] == eq_sorteado].iloc[0]
            conf = fila_eq['confederacion']
            # Previsualiza el marco verde si el grupo va a quedar completo
            if len(state.grupos_dict[grupo]) == 3:
                group_cards[grupo].style(CARD_STYLE_COMPLETE)
            await highlight_group(grupo)
            # Actualizar estado después del highlight
            eq_restantes_bombo_1 = eq_restantes_bombo_1[eq_restantes_bombo_1['codigo'] != eq_sorteado]
            slot = grupo + "1"
            state.asignaciones[eq_sorteado] = {"grupo": grupo, "slot": slot, "conf": conf}
            state.grupos_dict[grupo].append({"codigo": eq_sorteado, "slot": slot, "conf": conf})
            if slot in state.bombos_slots[grupo]:
                state.bombos_slots[grupo].remove(slot)
            state.log(f"SORTEO: {eq_sorteado} cabeza de serie Grupo {grupo}")
            refresh_groups_ui(only_group=grupo)
            await asyncio.sleep(0.2 * speed_multiplier['value'])

        state.current_team = None
        update_current_team_banner()
        state.current_bombo = None
        update_bombo_list_ui()
        await asyncio.sleep(0.35 * speed_multiplier['value'])  # Espera al finalizar el bombo
        await maybe_pause()

    async def run_bombo_n(n):
        """
        Ejecuta la lógica de sorteo para los Bombos 2, 3 y 4.
        
        Args:
            n (int): Número de bombo a sortear.
            
        Lógica:
        1. Itera sobre los grupos en orden (A-L).
        2. Para cada grupo, extrae una bola (equipo) del bombo actual.
        3. Verifica restricciones geográficas y realiza 'lookahead' para evitar bloqueos.
        4. Asigna el equipo a un grupo válido y a un slot aleatorio dentro de ese grupo.
        """
        state.log(f"--- INICIANDO BOMBO {n} ---")
        update_bombo_list_ui()
        state.current_bombo = n
        update_current_team_banner()
        update_bombo_list_ui()
        await asyncio.sleep(0.35 * speed_multiplier['value'])  # Espera antes de iniciar el primer equipo
        await maybe_pause()
        
        eq_bombo = df_bombos[df_bombos['bombo'] == n].copy()
        grupos_orden = list(state.bombos_slots.keys())
        
        # Intentamos llenar un cupo en cada grupo
        for _ in grupos_orden:
            if eq_bombo.empty: break
                
            await asyncio.sleep(0.35 * speed_multiplier['value']) # Pausa un poco más corta para suspense
            await maybe_pause()
            
            # Sacar equipo del bombo
            eq_sorteado = eq_bombo['codigo'].sample(1).iloc[0]
            state.current_team = eq_sorteado
            update_current_team_banner()
            update_bombo_list_ui(equipo_actual=eq_sorteado)
            await asyncio.sleep(0.35 * speed_multiplier['value'])
            eq_bombo = eq_bombo[eq_bombo['codigo'] != eq_sorteado]
            
            state.log(f"Sorteando equipo: {eq_sorteado}...")
            
            grupo_asignado = None
            
            # Buscar grupo válido
            for g in grupos_orden:
                # 1. Verificar si el grupo ya está lleno para este nivel de bombo
                if len(state.grupos_dict[g]) >= n:
                    continue
                
                # 2. Verificar restricciones de confederación (ej: no más de 1 de CONMEBOL)
                if not checker_validez_grupo(g, eq_sorteado, state.grupos_dict, verbose=False):
                    await highlight_discarded_group(g)
                    continue
                
                # 3. Lookahead: Verificar si esta asignación bloquearía el sorteo futuro
                remaining_teams = list(eq_bombo['codigo'])
                if not lookahead(g, eq_sorteado, remaining_teams, state.grupos_dict, state.bombos_slots, n):
                    await highlight_discarded_group(g)
                    continue
                
                grupo_asignado = g
                break
                
            if grupo_asignado is None:
                state.log(f"ERROR CRÍTICO: No se encontró grupo para {eq_sorteado}")
                ui.notify(f"Error: No valid group for {eq_sorteado}", type='negative')
                return
            # Previsualiza el marco verde si el grupo va a quedar completo
            if len(state.grupos_dict[grupo_asignado]) == 3:
                group_cards[grupo_asignado].style(CARD_STYLE_COMPLETE)
            await highlight_group(grupo_asignado)
            # Actualizar estado después del highlight
            slot_sorteado = random.choice(state.bombos_slots[grupo_asignado])
            state.bombos_slots[grupo_asignado].remove(slot_sorteado)
            conf_sorteado = df_bombos.loc[df_bombos['codigo'] == eq_sorteado, 'confederacion'].iloc[0]
            state.grupos_dict[grupo_asignado].append({
                "codigo": eq_sorteado,
                "slot": slot_sorteado,
                "conf": conf_sorteado
            })
            state.asignaciones[eq_sorteado] = {
                "grupo": grupo_asignado,
                "slot": slot_sorteado,
                "conf": conf_sorteado
            }
            state.log(f"-> Asignado a Grupo {grupo_asignado} (Slot {slot_sorteado})")
            refresh_groups_ui(only_group=grupo_asignado)
            await asyncio.sleep(0.2 * speed_multiplier['value'])

        state.current_team = None
        update_current_team_banner()
        state.current_bombo = None
        update_bombo_list_ui()
        await asyncio.sleep(0.35 * speed_multiplier['value'])  # Espera al finalizar el bombo
        await maybe_pause()

    async def start_simulation():
        """
        Orquesta el proceso completo de simulación.
        
        Se ejecuta al presionar el botón 'Iniciar Sorteo'.
        Ejecuta secuencialmente el sorteo de los bombos 1, 2, 3 y 4.
        """
        if state.processing: return
        state.processing = True
        if draw_button: draw_button.disable()
        state.reset()
        refresh_groups_ui()
        update_current_team_banner()
        update_bombo_list_ui()
        
        try:
            await run_bombo_1()
            for n in range(2, 5):
                await run_bombo_n(n)
            state.log("--- SORTEO FINALIZADO ---")
            ui.notify("Sorteo Finalizado con Éxito", type='positive')
            state.finished = True
            update_current_team_banner(finalizado=True)
        except Exception as e:
            state.log(f"Error: {str(e)}")
            ui.notify(f"Error durante el sorteo: {e}", type='negative')
            raise e
        finally:
            state.processing = False
            if draw_button: draw_button.enable()
            update_bombo_list_ui()

    async def fast_draw():
        """
        Sorteo rápido: llena todos los grupos sin animaciones ni esperas.
        No respeta constraints de tiempo, pero sí las reglas de asignación.
        """
        if state.processing: return
        state.processing = True
        if draw_button: draw_button.disable()
        state.reset()
        refresh_groups_ui()
        update_current_team_banner()
        update_bombo_list_ui()

        try:
            # BOMBO 1
            state.current_bombo = 1
            update_current_team_banner()
            update_bombo_list_ui()
            anfitriones = {"MEX": "A1", "CAN": "B1", "USA": "D1"}
            for eq, slot in anfitriones.items():
                state.current_team = eq
                update_current_team_banner()
                conf = df_bombos.loc[df_bombos['codigo'] == eq, 'confederacion'].iloc[0]
                grupo = slot[0]
                state.asignaciones[eq] = {"grupo": grupo, "slot": slot, "conf": conf}
                state.grupos_dict[grupo].append({"codigo": eq, "slot": slot, "conf": conf})
                if slot in state.bombos_slots[grupo]:
                    state.bombos_slots[grupo].remove(slot)
            eq_restantes_bombo_1 = df_bombos[
                (~df_bombos['codigo'].isin(['MEX', 'USA', 'CAN'])) &
                (df_bombos['bombo'] == 1)
            ]
            grupos_disponibles = [g for g in state.bombos_slots.keys() if g not in ('A', 'B', 'D')]
            for grupo in grupos_disponibles:
                eq_sorteado = eq_restantes_bombo_1['codigo'].sample(1).iloc[0]
                state.current_team = eq_sorteado
                fila_eq = eq_restantes_bombo_1[eq_restantes_bombo_1['codigo'] == eq_sorteado].iloc[0]
                conf = fila_eq['confederacion']
                eq_restantes_bombo_1 = eq_restantes_bombo_1[eq_restantes_bombo_1['codigo'] != eq_sorteado]
                slot = grupo + "1"
                state.asignaciones[eq_sorteado] = {"grupo": grupo, "slot": slot, "conf": conf}
                state.grupos_dict[grupo].append({"codigo": eq_sorteado, "slot": slot, "conf": conf})
                if slot in state.bombos_slots[grupo]:
                    state.bombos_slots[grupo].remove(slot)
            state.current_team = None
            state.current_bombo = None
            update_current_team_banner()
            update_bombo_list_ui()

            # BOMBO 2, 3, 4
            for n in range(2, 5):
                state.current_bombo = n
                update_current_team_banner()
                update_bombo_list_ui()
                eq_bombo = df_bombos[df_bombos['bombo'] == n].copy()
                grupos_orden = list(state.bombos_slots.keys())
                for g in grupos_orden:
                    if eq_bombo.empty: break
                    # Busca grupo con slot disponible
                    if len(state.grupos_dict[g]) >= n:
                        continue
                    eq_sorteado = eq_bombo['codigo'].sample(1).iloc[0]
                    state.current_team = eq_sorteado
                    eq_bombo = eq_bombo[eq_bombo['codigo'] != eq_sorteado]
                    slot_sorteado = random.choice(state.bombos_slots[g])
                    state.bombos_slots[g].remove(slot_sorteado)
                    conf_sorteado = df_bombos.loc[df_bombos['codigo'] == eq_sorteado, 'confederacion'].iloc[0]
                    state.grupos_dict[g].append({
                        "codigo": eq_sorteado,
                        "slot": slot_sorteado,
                        "conf": conf_sorteado
                    })
                    state.asignaciones[eq_sorteado] = {
                        "grupo": g,
                        "slot": slot_sorteado,
                        "conf": conf_sorteado
                    }
                state.current_team = None
                state.current_bombo = None
                update_current_team_banner()
                update_bombo_list_ui()

            state.log("--- SORTEO FINALIZADO ---")
            ui.notify("Sorteo rápido finalizado", type='positive')
            state.finished = True
            update_current_team_banner(finalizado=True)
            refresh_groups_ui()
            update_bombo_list_ui()
        except Exception as e:
            state.log(f"Error: {str(e)}")
            ui.notify(f"Error durante el sorteo rápido: {e}", type='negative')
            raise e
        finally:
            state.processing = False
            if draw_button: draw_button.enable()
            update_bombo_list_ui()

    # --- Construcción del Layout ---
    with ui.column().classes('w-full items-center'):
        ui.label('Sorteo FIFA World Cup 2026™').style(HEADER_STYLE)

        # Banner fijo para equipo actual sorteado
        with ui.row().classes('w-full justify-center').style("position:sticky;top:0;z-index:999;"):
            current_team_banner = ui.row().classes('w-full justify-center').style(
                "background-color:#23232a;border-radius:8px;margin-bottom:10px;box-shadow:0 2px 8px rgba(97,1,235,0.07);"
            )

        # Lista fija de equipos del bombo actual
        bombo_list_container = ui.column().classes('w-full items-center').style("margin-bottom:16px;")

        # Control de velocidad
        with ui.row().classes('w-full justify-center items-center q-mb-sm'):
            ui.label('Velocidad:').style('margin-right: 10px; font-weight: bold;')
            # Slider: min=0.15 (más rápido) a max=1.85 (más lento), pero el valor para la simulación es inverso
            speed_slider = ui.slider(min=0.15, max=1.85, step=0.05, value=1.0)
            speed_slider.props('label-always')
            speed_slider.style('width: 300px;')
            # Cuando el slider aumenta, la velocidad aumenta (el tiempo baja)
            # El valor real para la simulación es: tiempo = max + min - slider.value
            speed_slider.bind_value(
                speed_multiplier, 'value',
                forward=lambda v: 2.0 - v,  # El tiempo de simulación baja al aumentar el slider
                backward=lambda v: 2.0 - v
            )
            speed_slider.props('label-min="Lento" label-max="Rápido"')
            ui.label().bind_text_from(speed_multiplier, 'value', lambda v: f'{2.0 - v:.2f}x').style('margin-left: 10px; min-width: 50px;')

        # Botones de control
        with ui.row().classes('w-full justify-center q-mb-md'):
            draw_button = ui.button('Iniciar Sorteo', on_click=start_simulation).props('push color=accent icon=play_arrow')
            ui.button('Sorteo rápido', on_click=fast_draw).props('push color=positive icon=bolt')
            ui.button('Reiniciar', on_click=lambda: ui.navigate.reload()).props('outline color=secondary icon=refresh').style('background-color:#ffffff !important;box-shadow:0 2px 8px rgba(97,1,235,0.10);')
            ui.button('Pausa', on_click=pause_resume).props('outline color=secondary icon=pause').style('background-color:#ffffff !important;box-shadow:0 2px 8px rgba(97,1,235,0.10);')
            ui.button('Step', on_click=step_once).props('outline color=accent icon=skip_next').style('background-color:#ffffff !important;box-shadow:0 2px 8px rgba(97,1,235,0.10);')
            ui.button('Play', on_click=play_auto).props('outline color=accent icon=play_arrow').style('background-color:#ffffff !important;box-shadow:0 2px 8px rgba(97,1,235,0.10);')

        # Grid de Grupos
        with ui.grid(columns=4).classes('w-full q-pa-md gap-4').style("max-width: 1400px;"):
            for g in state.grupos:
                with ui.card().style(CARD_STYLE) as card:
                    group_cards[g] = card
                    ui.label(f"Grupo {g}").style("font-weight: bold;")
        
        # Elimina el panel de log y equipos lateral
        # ...no agregar log_container ni expansión lateral...

    refresh_groups_ui()
    update_current_team_banner()
    update_bombo_list_ui()

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(port=5555, title="Sorteo FIFA 2026")


    import os

if __name__ in ("__main__", "__mp_main__"):
    port = int(os.getenv("PORT", 8080))
    ui.run(host="0.0.0.0", port=port)