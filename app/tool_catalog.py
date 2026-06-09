TOOL_LABELS = {
    "welding-console": "Пульт сварки",
    "seam-gauge": "Шаблон контроля шва",
    "thermal-scanner": "Тепловизор",
    "voice-terminal": "Голосовой терминал",
    "torque-wrench": "Динамометрический ключ",
    "angle-gauge": "Датчик угла затяжки",
    "scanner": "Сканер",
    "paint-gun": "Краскопульт",
    "thickness-meter": "Толщиномер",
    "tablet": "Планшет",
    "hinge-aligner": "Шаблон петель",
    "gap-gauge": "Щуп зазоров",
    "camera-rig": "Камера фотофиксации",
    "pick-to-light": "Pick-to-light терминал",
}


def tool_label(tool_code: str) -> str:
    return TOOL_LABELS.get(tool_code, tool_code)
