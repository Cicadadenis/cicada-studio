"""
Cicada Parser вЂ” РїСЂРµРІСЂР°С‰Р°РµС‚ .cicada С„Р°Р№Р» РІ AST (РґРµСЂРµРІРѕ РїСЂРѕРіСЂР°РјРјС‹).

РЎРёРЅС‚Р°РєСЃРёСЃ РїРѕРґРґРµСЂР¶РёРІР°РµС‚СЃСЏ:
    бот "TOKEN"
    РїСЂРё СЃС‚Р°СЂС‚Рµ: ...
    РµСЃР»Рё С‚РµРєСЃС‚ == "X": ...
    РёРЅР°С‡Рµ: ...
    РѕС‚РІРµС‚ "С‚РµРєСЃС‚" / РѕС‚РІРµС‚ "С‚РµРєСЃС‚" + РїРµСЂРµРјРµРЅРЅР°СЏ
    СЃРїСЂРѕСЃРёС‚СЊ "РІРѕРїСЂРѕСЃ" в†’ РїРµСЂРµРјРµРЅРЅР°СЏ
    Р·Р°РїРѕРјРЅРё РїРµСЂРµРјРµРЅРЅР°СЏ = Р·РЅР°С‡РµРЅРёРµ
    СЃС†РµРЅР°СЂРёР№ РёРјСЏ: ...
    РєРЅРѕРїРєРё "A" "B" "C"
    РєРЅРѕРїРєРё "A|B|C"          вЂ” С‚Рѕ Р¶Рµ, С‡С‚Рѕ С‚СЂРё РєРЅРѕРїРєРё РІ РѕРґРёРЅ СЂСЏРґ (СЂР°Р·РґРµР»РёС‚РµР»СЊ | РІРЅСѓС‚СЂРё СЃС‚СЂРѕРєРё)
    РєР°СЂС‚РёРЅРєР° "url"
    СЃС‚РёРєРµСЂ "file_id"
"""

import json as _json
import re
import random
from dataclasses import dataclass, field
from typing import Any


# в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ AST nodes в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ

@dataclass
class Program:
    config: dict = field(default_factory=dict)
    handlers: list = field(default_factory=list)   # on_start, on_text, on_command
    scenarios: dict = field(default_factory=dict)  # name в†’ list[Node]
    blocks: dict = field(default_factory=dict)      # name в†’ Block
    globals: dict = field(default_factory=dict)     # РіР»РѕР±Р°Р»СЊРЅС‹Рµ РїРµСЂРµРјРµРЅРЅС‹Рµ




def merge_programs(target: Program, imported: Program) -> Program:
    """РћР±СЉРµРґРёРЅСЏРµС‚ РёРјРїРѕСЂС‚РёСЂРѕРІР°РЅРЅС‹Р№ РјРѕРґСѓР»СЊ СЃ С‚РµРєСѓС‰РµР№ РїСЂРѕРіСЂР°РјРјРѕР№.

    РРјРїРѕСЂС‚РёСЂРѕРІР°РЅРЅС‹Рµ handlers РґРѕР±Р°РІР»СЏСЋС‚СЃСЏ РІ РєРѕРЅРµС†, СЃС†РµРЅР°СЂРёРё/Р±Р»РѕРєРё/globals
    РґРѕРїРѕР»РЅСЏСЋС‚ С‚РµРєСѓС‰СѓСЋ РїСЂРѕРіСЂР°РјРјСѓ, Р° config Р·Р°РїРѕР»РЅСЏРµС‚СЃСЏ С‚РѕР»СЊРєРѕ РѕС‚СЃСѓС‚СЃС‚РІСѓСЋС‰РёРјРё РєР»СЋС‡Р°РјРё,
    С‡С‚РѕР±С‹ РѕСЃРЅРѕРІРЅРѕР№ С„Р°Р№Р» РѕСЃС‚Р°РІР°Р»СЃСЏ РіР»Р°РІРЅС‹Рј РёСЃС‚РѕС‡РЅРёРєРѕРј РЅР°СЃС‚СЂРѕРµРє.
    """
    for key, value in imported.config.items():
        target.config.setdefault(key, value)
    target.handlers.extend(imported.handlers)
    target.scenarios.update(imported.scenarios)
    target.blocks.update(imported.blocks)
    target.globals.update(imported.globals)
    return target

@dataclass
class Handler:
    kind: str          # "start" | "text" | "command" | "button"
    trigger: Any       # None / str / list[str]
    body: list = field(default_factory=list)


@dataclass
class Scenario:
    name: str
    steps: list = field(default_factory=list)


# в”Ђв”Ђ statement nodes в”Ђв”Ђ

@dataclass
class Reply:
    parts: list   # list of str / VarRef


@dataclass
class Ask:
    question: str
    variable: str


@dataclass
class RandomReply:
    """РЎР»СѓС‡Р°Р№РЅС‹Р№ РѕС‚РІРµС‚ РёР· СЃРїРёСЃРєР° РІР°СЂРёР°РЅС‚РѕРІ"""
    variants: list  # СЃРїРёСЃРѕРє СЃС‚СЂРѕРє


@dataclass
class Remember:
    name: str
    value: Any    # str | int | float | VarRef | Expr


@dataclass
class If:
    condition: "Condition"
    then_body: list
    else_body: list = field(default_factory=list)


@dataclass
class Condition:
    left: Any
    op: str
    right: Any
    negate: bool = False  # РґР»СЏ РѕРїРµСЂР°С‚РѕСЂР° "РЅРµ"


@dataclass
class ComplexCondition:
    """РЎР»РѕР¶РЅРѕРµ СѓСЃР»РѕРІРёРµ СЃ Р»РѕРіРёС‡РµСЃРєРёРјРё РѕРїРµСЂР°С‚РѕСЂР°РјРё (Рё, РёР»Рё)"""
    conditions: list  # СЃРїРёСЃРѕРє Condition
    operators: list   # СЃРїРёСЃРѕРє РѕРїРµСЂР°С‚РѕСЂРѕРІ: "Рё" РёР»Рё "РёР»Рё"


@dataclass
class Buttons:
    labels: list  # РјРѕР¶РµС‚ Р±С‹С‚СЊ СЃРїРёСЃРєРѕРј СЃС‚СЂРѕРє РёР»Рё СЃРїРёСЃРєРѕРј СЃРїРёСЃРєРѕРІ (РјР°С‚СЂРёС†Р°)


@dataclass
class InlineButton:
    """РљРЅРѕРїРєР° СЃ callback_data РёР»Рё URL"""
    text: str
    callback: str = ""      # callback_data
    url: str = ""           # URL РґР»СЏ РѕС‚РєСЂС‹С‚РёСЏ
    data: str = ""          # РґРѕРїРѕР»РЅРёС‚РµР»СЊРЅС‹Рµ РґР°РЅРЅС‹Рµ


@dataclass
class InlineKeyboard:
    """
    Inline-РєР»Р°РІРёР°С‚СѓСЂР°: РјР°С‚СЂРёС†Р° РєРЅРѕРїРѕРє вЂ” СЃРїРёСЃРѕРє СЂСЏРґРѕРІ, РєР°Р¶РґС‹Р№ СЂСЏРґ СЃРїРёСЃРѕРє InlineButton.
    РџР°СЂСЃРёС‚СЃСЏ РёР· Р±Р»РѕРєР°:
        inline-РєРЅРѕРїРєРё:
            ["Р”Р°" в†’ "cb_yes", "РќРµС‚" в†’ "cb_no"]
            ["РћС‚РјРµРЅР°" в†’ "cb_cancel"]
    Р’РµСЃСЊ Р±Р»РѕРє = РѕРґРЅРѕ СЃРѕРѕР±С‰РµРЅРёРµ СЃ InlineKeyboardMarkup.
    """
    rows: list   # list[list[InlineButton]]


@dataclass
class InlineKeyboardFromList:
    """Р”РёРЅР°РјРёС‡РµСЃРєР°СЏ inline-РєР»Р°РІРёР°С‚СѓСЂР° РёР· СЃРїРёСЃРєР° РѕР±СЉРµРєС‚РѕРІ/СЃС‚СЂРѕРє."""
    items_expr: Any
    text_field: str = "name"
    id_field: str = "id"
    callback_prefix: str = "С‚РѕРІР°СЂ_"
    columns: int = 1
    append_back: bool = True


@dataclass
class InlineKeyboardFromDB:
    """Р”РёРЅР°РјРёС‡РµСЃРєР°СЏ inline-РєР»Р°РІРёР°С‚СѓСЂР° РёР· СЃРїРёСЃРєР° РІ Р‘Р” С‚РµРєСѓС‰РµРіРѕ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ."""
    key: object
    text_field: str = "name"
    id_field: str = "id"
    callback_prefix: str = ""
    columns: int = 1
    back_text: str = ""
    back_callback: str = ""


@dataclass
@dataclass
class Photo:
    """РљР°СЂС‚РёРЅРєР°: URL, file_id РёР»Рё BytesIO РѕР±СЉРµРєС‚"""
    url: Any  # str (URL/file_id) РёР»Рё BytesIO


@dataclass
class PhotoVar:
    """РљР°СЂС‚РёРЅРєР° РёР· РїРµСЂРµРјРµРЅРЅРѕР№ (URL, file_id РёР»Рё BytesIO)"""
    var_name: str


@dataclass
class Sticker:
    file_id: Any


@dataclass
class StartScenario:
    """Р—Р°РїСѓСЃС‚РёС‚СЊ РёРјРµРЅРѕРІР°РЅРЅС‹Р№ СЃС†РµРЅР°СЂРёР№"""
    name: str


@dataclass
class Step:
    """РРјРµРЅРѕРІР°РЅРЅС‹Р№ С€Р°Рі РІРЅСѓС‚СЂРё СЃС†РµРЅР°СЂРёСЏ"""
    name: str
    body: list = field(default_factory=list)


@dataclass
class ReturnFromScenario:
    """Р’РµСЂРЅСѓС‚СЊСЃСЏ РёР· СЃС†РµРЅР°СЂРёСЏ (РїСЂРµСЂРІР°С‚СЊ С‚РµРєСѓС‰РёР№ С€Р°Рі, РЅРѕ РЅРµ СЃС†РµРЅР°СЂРёР№ РїРѕР»РЅРѕСЃС‚СЊСЋ)"""
    pass


@dataclass
class RepeatStep:
    """РџРѕРІС‚РѕСЂРёС‚СЊ С‚РµРєСѓС‰РёР№ С€Р°Рі СЃС†РµРЅР°СЂРёСЏ"""
    pass


@dataclass
class GotoStep:
    """РџРµСЂРµР№С‚Рё Рє РєРѕРЅРєСЂРµС‚РЅРѕРјСѓ С€Р°РіСѓ СЃС†РµРЅР°СЂРёСЏ"""
    step_name: str


@dataclass
class EndScenario:
    """РџСЂРµСЂС‹РІР°РµС‚ РІС‹РїРѕР»РЅРµРЅРёРµ С‚РµРєСѓС‰РµРіРѕ СЃС†РµРЅР°СЂРёСЏ"""
    pass


@dataclass
class SaveToDB:
    """РЎРѕС…СЂР°РЅСЏРµС‚ Р·РЅР°С‡РµРЅРёРµ РІ Р±Р°Р·Сѓ РґР°РЅРЅС‹С…"""
    key: str
    value: Any


@dataclass
class LoadFromDB:
    """Р—Р°РіСЂСѓР¶Р°РµС‚ Р·РЅР°С‡РµРЅРёРµ РёР· Р±Р°Р·С‹ РґР°РЅРЅС‹С…"""
    variable: str
    key: str


@dataclass
class ForwardPhoto:
    caption: str = ""


@dataclass
class SaveFile:
    variable: str


@dataclass
class SendDocument:
    file: str
    caption: str = ""


@dataclass
class SendAudio:
    file: str
    caption: str = ""


@dataclass
class SendVideo:
    file: str
    caption: str = ""


@dataclass
class SendVoice:
    file: str
    caption: str = ""


@dataclass
class SendLocation:
    latitude: float
    longitude: float


@dataclass
class SendContact:
    phone: str
    name: str


@dataclass
class SendPoll:
    question: str
    options: list


@dataclass
class SendInvoice:
    title: str
    description: str
    amount: int


@dataclass
class SendGame:
    short_name: str


@dataclass
class SendMarkdown:
    parts: list


@dataclass
class SendHTML:
    parts: list


@dataclass
class SendMarkdownV2:
    parts: list


@dataclass
class DownloadFile:
    variable: str
    save_path: str = ""


@dataclass
class HttpGet:
    """HTTP GET Р·Р°РїСЂРѕСЃ"""
    url: object
    variable: str  # РєСѓРґР° СЃРѕС…СЂР°РЅРёС‚СЊ СЂРµР·СѓР»СЊС‚Р°С‚
    headers: dict = field(default_factory=dict)


@dataclass
class HttpPost:
    """HTTP POST Р·Р°РїСЂРѕСЃ"""
    url: object
    data: Any      # С‚РµР»Рѕ Р·Р°РїСЂРѕСЃР°
    variable: str  # РєСѓРґР° СЃРѕС…СЂР°РЅРёС‚СЊ СЂРµР·СѓР»СЊС‚Р°С‚
    headers: dict = field(default_factory=dict)


@dataclass
class Log:
    """Р’С‹РІРѕРґ Р·РЅР°С‡РµРЅРёСЏ РІ РєРѕРЅСЃРѕР»СЊ (РґР»СЏ РѕС‚Р»Р°РґРєРё)"""
    parts: list   # СЃРїРёСЃРѕРє str / VarRef РґР»СЏ РІС‹РІРѕРґР°


@dataclass
class Sleep:
    """Р—Р°РґРµСЂР¶РєР° РІ СЃРµРєСѓРЅРґР°С…"""
    seconds: float


@dataclass
class TelegramAPI:
    """РЈРЅРёРІРµСЂСЃР°Р»СЊРЅС‹Р№ РІС‹Р·РѕРІ Telegram API"""
    method: str      # РјРµС‚РѕРґ API (sendMessage, editMessageText Рё С‚.Рґ.)
    params: dict     # РїР°СЂР°РјРµС‚СЂС‹ РІС‹Р·РѕРІР°


@dataclass
class GlobalVar:
    """Р“Р»РѕР±Р°Р»СЊРЅР°СЏ РїРµСЂРµРјРµРЅРЅР°СЏ (РґРѕСЃС‚СѓРїРЅР° РІСЃРµРј РїРѕР»СЊР·РѕРІР°С‚РµР»СЏРј)"""
    name: str
    value: Any


@dataclass
class BeforeEach:
    """Middleware вЂ” РІС‹РїРѕР»РЅСЏРµС‚СЃСЏ РїРµСЂРµРґ РєР°Р¶РґС‹Рј СЃРѕРѕР±С‰РµРЅРёРµРј"""
    body: list


@dataclass
class AfterEach:
    """Middleware вЂ” РІС‹РїРѕР»РЅСЏРµС‚СЃСЏ РїРѕСЃР»Рµ РєР°Р¶РґРѕРіРѕ СЃРѕРѕР±С‰РµРЅРёСЏ"""
    body: list


@dataclass
class Block:
    """РџРµСЂРµРёСЃРїРѕР»СЊР·СѓРµРјС‹Р№ Р±Р»РѕРє РєРѕРґР°"""
    name: str
    body: list


@dataclass
class UseBlock:
    """РСЃРїРѕР»СЊР·РѕРІР°РЅРёРµ (РІСЃС‚Р°РІРєР°) Р±Р»РѕРєР°"""
    name: str


@dataclass
class VarRef:
    """РЈСЃС‚Р°СЂРµРІС€РёР№ СѓР·РµР» вЂ” РѕСЃС‚Р°РІР»РµРЅ РґР»СЏ СЃРѕРІРјРµСЃС‚РёРјРѕСЃС‚Рё. РСЃРїРѕР»СЊР·СѓР№С‚Рµ Variable."""
    name: str


@dataclass
class Expr:
    """РЈСЃС‚Р°СЂРµРІС€РёР№ СѓР·РµР» вЂ” РѕСЃС‚Р°РІР»РµРЅ РґР»СЏ СЃРѕРІРјРµСЃС‚РёРјРѕСЃС‚Рё."""
    parts: list   # mix of str / VarRef


@dataclass
class FunctionCall:
    """РЈСЃС‚Р°СЂРµРІС€РёР№ СѓР·РµР» вЂ” РѕСЃС‚Р°РІР»РµРЅ РґР»СЏ СЃРѕРІРјРµСЃС‚РёРјРѕСЃС‚Рё. РСЃРїРѕР»СЊР·СѓР№С‚Рµ Call."""
    name: str
    args: list


# в”Ђв”Ђ РЎРѕСЃС‚Р°РІРЅС‹Рµ С‚РёРїС‹ Рё РєРѕР»Р»РµРєС†РёРё в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ

@dataclass
class ListLiteral:
    """Р›РёС‚РµСЂР°Р» РјР°СЃСЃРёРІР°: [1, 2, 3] РёР»Рё ['a', 'b']"""
    items: list


@dataclass
class DictLiteral:
    """Р›РёС‚РµСЂР°Р» СЃР»РѕРІР°СЂСЏ: {РєР»СЋС‡: Р·РЅР°С‡РµРЅРёРµ, ...}"""
    pairs: list  # СЃРїРёСЃРѕРє (key, value) tuples


@dataclass
class Index:
    """РРЅРґРµРєСЃР°С†РёСЏ: РјР°СЃСЃРёРІ[0] РёР»Рё СЃР»РѕРІР°СЂСЊ['РєР»СЋС‡']"""
    target: object  # С‡С‚Рѕ РёРЅРґРµРєСЃРёСЂСѓРµРј
    key: object     # РєР»СЋС‡/РёРЅРґРµРєСЃ


@dataclass
class Attr:
    """Р”РѕСЃС‚СѓРї Рє Р°С‚СЂРёР±СѓС‚Сѓ: РїРѕР»СЊР·РѕРІР°С‚РµР»СЊ.РёРјСЏ, С‡Р°С‚.id"""
    target: object  # РѕР±СЉРµРєС‚
    name: str       # РёРјСЏ Р°С‚СЂРёР±СѓС‚Р°


@dataclass
class ForEach:
    """Р¦РёРєР» РїРѕ РєРѕР»Р»РµРєС†РёРё: РґР»СЏ РєР°Р¶РґРѕРіРѕ СЌР»РµРјРµРЅС‚Р° РІ СЃРїРёСЃРєРµ"""
    variable: str   # РёРјСЏ РїРµСЂРµРјРµРЅРЅРѕР№
    collection: object  # С‡С‚Рѕ РїРµСЂРµР±РёСЂР°РµРј
    body: list      # С‚РµР»Рѕ С†РёРєР»Р°


@dataclass
class WhileLoop:
    """Р¦РёРєР» while: РїРѕРєР° СѓСЃР»РѕРІРёРµ: С‚РµР»Рѕ"""
    condition: object
    body: list


@dataclass
class BreakLoop:
    """РџСЂРµСЂРІР°С‚СЊ С†РёРєР» (break)"""
    pass


@dataclass
class ContinueLoop:
    """РџСЂРѕРґРѕР»Р¶РёС‚СЊ СЃР»РµРґСѓСЋС‰СѓСЋ РёС‚РµСЂР°С†РёСЋ (continue)"""
    pass


@dataclass
class Timeout:
    """Р’С‹РїРѕР»РЅРµРЅРёРµ СЃ РѕРіСЂР°РЅРёС‡РµРЅРёРµРј РІСЂРµРјРµРЅРё: С‚Р°Р№РјР°СѓС‚ N СЃРµРєСѓРЅРґ: С‚РµР»Рѕ"""
    seconds: float
    body: list


# в”Ђв”Ђ РЈРІРµРґРѕРјР»РµРЅРёСЏ Рё СЂР°СЃСЃС‹Р»РєР° в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ

@dataclass
class Notify:
    """СѓРІРµРґРѕРјРёС‚СЊ USER_ID "С‚РµРєСЃС‚" вЂ” РѕС‚РїСЂР°РІРєР° СЃРѕРѕР±С‰РµРЅРёСЏ РєРѕРЅРєСЂРµС‚РЅРѕРјСѓ РїРѕР»СЊР·РѕРІР°С‚РµР»СЋ"""
    user_id: object   # РІС‹СЂР°Р¶РµРЅРёРµ в†’ user_id
    parts: list       # СЃРїРёСЃРѕРє С‡Р°СЃС‚РµР№ С‚РµРєСЃС‚Р°


@dataclass
class Broadcast:
    """СЂР°СЃСЃС‹Р»РєР° РІСЃРµРј: С‚РµРєСЃС‚ / СЂР°СЃСЃС‹Р»РєР° РіСЂСѓРїРїРµ TAG: С‚РµРєСЃС‚"""
    parts: list       # СЃРїРёСЃРѕРє С‡Р°СЃС‚РµР№ С‚РµРєСЃС‚Р°
    segment: str = "" # "" = РІСЃРµ, РёРЅР°С‡Рµ вЂ” РёРјСЏ СЃРµРіРјРµРЅС‚Р°


# в”Ђв”Ђ Telegram-СЃРїРµС†РёС„РёРєР° в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ

@dataclass
class CheckSubscription:
    """РїСЂРѕРІРµСЂРёС‚СЊ РїРѕРґРїРёСЃРєСѓ @РєР°РЅР°Р» в†’ РїРµСЂРµРјРµРЅРЅР°СЏ"""
    channel: object   # "@channel" РёР»Рё РІС‹СЂР°Р¶РµРЅРёРµ
    variable: str


@dataclass
class GetChatMemberRole:
    """СЂРѕР»СЊ @РєР°РЅР°Р» USER_ID в†’ РїРµСЂРµРјРµРЅРЅР°СЏ"""
    chat: object      # chat_id / "@channel"
    user_id: object   # user_id
    variable: str


@dataclass
class ForwardMsg:
    """РїРµСЂРµСЃР»Р°С‚СЊ СЃРѕРѕР±С‰РµРЅРёРµ USER_ID вЂ” РїРµСЂРµСЃС‹Р»Р°РµС‚ С‚РµРєСѓС‰РµРµ СЃРѕРѕР±С‰РµРЅРёРµ РґСЂСѓРіРѕРјСѓ РїРѕР»СЊР·РѕРІР°С‚РµР»СЋ"""
    to_user_id: object


# в”Ђв”Ђ Р¤Р°Р№Р»С‹ Рё JSON в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ

@dataclass
class LoadJson:
    """json_С„Р°Р№Р» "РїСѓС‚СЊ" в†’ РїРµСЂРµРјРµРЅРЅР°СЏ"""
    path: object
    variable: str


@dataclass
class ParseJson:
    """СЂР°Р·РѕР±СЂР°С‚СЊ_json РёСЃС‚РѕС‡РЅРёРє в†’ РїРµСЂРµРјРµРЅРЅР°СЏ"""
    source: object
    variable: str


@dataclass
class SaveJson:
    """СЃРѕС…СЂР°РЅРёС‚СЊ_json "РїСѓС‚СЊ" = РїРµСЂРµРјРµРЅРЅР°СЏ"""
    path: object
    source_var: str


@dataclass
class DeleteFile:
    """СѓРґР°Р»РёС‚СЊ_С„Р°Р№Р» 'РїСѓС‚СЊ' вЂ” СѓРґР°Р»РµРЅРёРµ С„Р°Р№Р»Р° СЃ РґРёСЃРєР°"""
    path: object


@dataclass
class DeleteDictKey:
    """СѓРґР°Р»РёС‚СЊ РѕР±СЉРµРєС‚["РєР»СЋС‡"] вЂ” СѓРґР°Р»РµРЅРёРµ РїРѕР»СЏ РёР· dict"""
    target: str    # РёРјСЏ РїРµСЂРµРјРµРЅРЅРѕР№
    key: object    # РєР»СЋС‡ (РІС‹СЂР°Р¶РµРЅРёРµ)


@dataclass
class SetDictKey:
    """РѕР±СЉРµРєС‚["РєР»СЋС‡"] = Р·РЅР°С‡РµРЅРёРµ вЂ” РїСЂРёСЃРІР°РёРІР°РЅРёРµ РїРѕР»СЏ dict"""
    target: str    # РёРјСЏ РїРµСЂРµРјРµРЅРЅРѕР№
    key: object    # РєР»СЋС‡ (РІС‹СЂР°Р¶РµРЅРёРµ)
    value: object  # Р·РЅР°С‡РµРЅРёРµ (РІС‹СЂР°Р¶РµРЅРёРµ)


# в”Ђв”Ђ HTTP СЂР°СЃС€РёСЂРµРЅРёСЏ в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ

@dataclass
class HttpPatch:
    """HTTP PATCH Р·Р°РїСЂРѕСЃ"""
    url: object
    data: object
    variable: str
    headers: dict = field(default_factory=dict)


@dataclass
class HttpPut:
    """HTTP PUT Р·Р°РїСЂРѕСЃ"""
    url: object
    data: object
    variable: str
    headers: dict = field(default_factory=dict)


@dataclass
class HttpDelete:
    """HTTP DELETE Р·Р°РїСЂРѕСЃ"""
    url: object
    variable: str
    headers: dict = field(default_factory=dict)


@dataclass
class SetHttpHeaders:
    """http_Р·Р°РіРѕР»РѕРІРєРё РїРµСЂРµРјРµРЅРЅР°СЏ вЂ” СѓСЃС‚Р°РЅР°РІР»РёРІР°РµС‚ Р·Р°РіРѕР»РѕРІРєРё РґР»СЏ СЃР»РµРґСѓСЋС‰РёС… HTTP-РІС‹Р·РѕРІРѕРІ"""
    variable: str


@dataclass
class FetchJson:
    """fetch_json url в†’ РїРµСЂРµРјРµРЅРЅР°СЏ вЂ” GET + JSON.parse"""
    url: object
    variable: str
    headers: dict = field(default_factory=dict)


# в”Ђв”Ђ Р‘Р°Р·Р° РґР°РЅРЅС‹С… СЂР°СЃС€РёСЂРµРЅРёСЏ в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ

@dataclass
class DeleteFromDB:
    """СѓРґР°Р»РёС‚СЊ "РєР»СЋС‡" вЂ” СѓРґР°Р»РµРЅРёРµ РєР»СЋС‡Р° РёР· Р‘Р” С‚РµРєСѓС‰РµРіРѕ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ"""
    key: object


@dataclass
class GetAllDBKeys:
    """РІСЃРµ_РєР»СЋС‡Рё в†’ РїРµСЂРµРјРµРЅРЅР°СЏ вЂ” РІСЃРµ РєР»СЋС‡Рё РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ РёР· Р‘Р”"""
    variable: str


@dataclass
class SaveGlobalDB:
    """СЃРѕС…СЂР°РЅРёС‚СЊ_РіР»РѕР±Р°Р»СЊРЅРѕ "РєР»СЋС‡" = Р·РЅР°С‡РµРЅРёРµ"""
    key: object
    value: object


@dataclass
class LoadFromUserDB:
    """РїРѕР»СѓС‡РёС‚СЊ РѕС‚ USER_ID "РєР»СЋС‡" в†’ РїРµСЂРµРјРµРЅРЅР°СЏ"""
    user_id: object
    key: object
    variable: str


# в”Ђв”Ђ РЈРїСЂР°РІР»РµРЅРёРµ РїРѕС‚РѕРєРѕРј СЂР°СЃС€РёСЂРµРЅРёСЏ в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ

@dataclass
class ReturnValue:
    """РІРµСЂРЅСѓС‚СЊ Р·РЅР°С‡РµРЅРёРµ вЂ” РІРѕР·РІСЂР°С‚ Р·РЅР°С‡РµРЅРёСЏ РёР· Р±Р»РѕРєР°"""
    value: object


@dataclass
class CallBlock:
    """РІС‹Р·РІР°С‚СЊ "Р±Р»РѕРє" в†’ РїРµСЂРµРјРµРЅРЅР°СЏ вЂ” РІС‹Р·РѕРІ Р±Р»РѕРєР° РєР°Рє С„СѓРЅРєС†РёРё"""
    name: str
    variable: str = ""


# в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ Expression AST в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
# РџРѕР»РЅРѕС†РµРЅРЅРѕРµ РґРµСЂРµРІРѕ РІС‹СЂР°Р¶РµРЅРёР№: РїРѕРґРґРµСЂР¶РёРІР°РµС‚ Р°СЂРёС„РјРµС‚РёРєСѓ, СЃСЂР°РІРЅРµРЅРёСЏ,
# РІР»РѕР¶РµРЅРЅС‹Рµ РІС‹Р·РѕРІС‹ С„СѓРЅРєС†РёР№, Р»РѕРіРёС‡РµСЃРєРёРµ РѕРїРµСЂР°С‚РѕСЂС‹.

@dataclass
class Literal:
    """РљРѕРЅСЃС‚Р°РЅС‚Р°: С‡РёСЃР»Рѕ, СЃС‚СЂРѕРєР°, bool."""
    value: object   # int | float | str | bool

    def __repr__(self):
        return f"Literal({self.value!r})"


@dataclass
class Variable:
    """РЎСЃС‹Р»РєР° РЅР° РїРµСЂРµРјРµРЅРЅСѓСЋ РєРѕРЅС‚РµРєСЃС‚Р° (Р·Р°РјРµРЅСЏРµС‚ VarRef)."""
    name: str

    def __repr__(self):
        return f"Variable({self.name!r})"


@dataclass
class BinaryOp:
    """Р‘РёРЅР°СЂРЅР°СЏ РѕРїРµСЂР°С†РёСЏ: left OP right.

    РџРѕРґРґРµСЂР¶РёРІР°РµРјС‹Рµ OP:
      Р°СЂРёС„РјРµС‚РёРєР° : +  -  *  /  //  %  **
      СЃСЂР°РІРЅРµРЅРёРµ  : ==  !=  >  <  >=  <=
      СЃС‚СЂРѕРєРё     : СЃРѕРґРµСЂР¶РёС‚  РЅР°С‡РёРЅР°РµС‚СЃСЏ_СЃ
      Р»РѕРіРёРєР°     : Рё  РёР»Рё
    """
    left: object
    op: str
    right: object

    def __repr__(self):
        return f"BinaryOp({self.left!r} {self.op} {self.right!r})"


@dataclass
class UnaryOp:
    """РЈРЅР°СЂРЅР°СЏ РѕРїРµСЂР°С†РёСЏ: РЅРµ / СѓРЅР°СЂРЅС‹Р№ РјРёРЅСѓСЃ."""
    op: str     # "РЅРµ" | "-"
    operand: object

    def __repr__(self):
        return f"UnaryOp({self.op} {self.operand!r})"


@dataclass
class Call:
    """Р’С‹Р·РѕРІ РІСЃС‚СЂРѕРµРЅРЅРѕР№ С„СѓРЅРєС†РёРё: РёРјСЏ(Р°СЂРі1, Р°СЂРі2, ...)."""
    name: str
    args: list

    def __repr__(self):
        return f"Call({self.name}({', '.join(repr(a) for a in self.args)}))"


# в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ Expression parser в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ

def parse_expr(raw: str):
    """
    РџР°СЂСЃРёС‚ СЃС‚СЂРѕРєСѓ РІ РґРµСЂРµРІРѕ РІС‹СЂР°Р¶РµРЅРёР№ (Expression AST).

    РџСЂРёРѕСЂРёС‚РµС‚ РѕРїРµСЂР°С‚РѕСЂРѕРІ (РѕС‚ РЅРёР·РєРѕРіРѕ Рє РІС‹СЃРѕРєРѕРјСѓ):
      1. РёР»Рё
      2. Рё
      3. РЅРµ
      4. ==  !=  >  <  >=  <=  СЃРѕРґРµСЂР¶РёС‚  РЅР°С‡РёРЅР°РµС‚СЃСЏ_СЃ
      5. +  -
      6. *  /  //  %
      7. **  (РїСЂР°РІРѕР°СЃСЃРѕС†РёР°С‚РёРІРЅС‹Р№)
      8. СѓРЅР°СЂРЅС‹Р№ -
      9. Р°С‚РѕРј: literal, variable, func(), (expr)
    """
    tokens = _tokenize_expr(raw.strip())
    if not tokens:
        return Literal("")
    ep = _ExprParser(tokens)
    node = ep.parse_or()
    if ep.pos < len(tokens):
        remaining = " ".join(str(t) for t in tokens[ep.pos:])
        raise SyntaxError(f"РќРµРїР°СЂСЃРёСЂРѕРІР°РЅРЅС‹Р№ РѕСЃС‚Р°С‚РѕРє РІС‹СЂР°Р¶РµРЅРёСЏ: {remaining!r}")
    return node


def _tokenize_expr(src: str) -> list:
    """Р Р°Р·Р±РёРІР°РµС‚ СЃС‚СЂРѕРєСѓ РІС‹СЂР°Р¶РµРЅРёСЏ РЅР° С‚РѕРєРµРЅС‹."""
    token_re = re.compile(
        r'"[^"]*"'                                      # СЃС‚СЂРѕРєР° РІ РґРІРѕР№РЅС‹С… РєР°РІС‹С‡РєР°С…
        r"|'[^']*'"                                     # СЃС‚СЂРѕРєР° РІ РѕРґРёРЅР°СЂРЅС‹С… РєР°РІС‹С‡РєР°С…
        r'|\d+(?:\.\d+)?'                               # С‡РёСЃР»Рѕ
        # РРґРµРЅС‚РёС„РёРєР°С‚РѕСЂС‹ Р РєР»СЋС‡РµРІС‹Рµ СЃР»РѕРІР° вЂ” РѕРґРЅРёРј РїР°С‚С‚РµСЂРЅРѕРј.
        # РљР»СЋС‡РµРІС‹Рµ СЃР»РѕРІР° РІС‹РґРµР»СЏСЋС‚СЃСЏ РїРѕСЃС‚РѕР±СЂР°ботРєРѕР№, Р° РЅРµ РѕС‚РґРµР»СЊРЅС‹Рј Р°Р»СЊС‚РµСЂРЅР°С‚РёРІРЅС‹Рј
        # РїР°С‚С‚РµСЂРЅРѕРј, С‡С‚РѕР±С‹ В«РёР»РёВ» РІ В«РїРµСЂРµРјРµРЅРЅР°СЏВ» РЅРµ СЃСЉРµРґР°Р»Рѕ С‡Р°СЃС‚СЊ РёРґРµРЅС‚РёС„РёРєР°С‚РѕСЂР°.
        r'|[Р°-СЏС‘Рђ-РЇРЃa-zA-Z_][Р°-СЏС‘Рђ-РЇРЃa-zA-Z0-9_.]*'  # РёРґРµРЅС‚РёС„РёРєР°С‚РѕСЂ / РєР»СЋС‡РµРІРѕРµ СЃР»РѕРІРѕ
        r'|\*\*|//|>=|<=|==|!='                        # РґРІРѕР№РЅС‹Рµ РѕРїРµСЂР°С‚РѕСЂС‹
        r'|[+\-*/%><!(),\[\]]'                         # РѕРґРёРЅРѕС‡РЅС‹Рµ РѕРїРµСЂР°С‚РѕСЂС‹
        r'|\s+'                                         # РїСЂРѕР±РµР»С‹
    )
    return [m.group() for m in token_re.finditer(src) if m.group().strip()]


class _ExprParser:
    def __init__(self, tokens: list):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def consume(self, expected=None):
        t = self.peek()
        if expected is not None and t != expected:
            raise SyntaxError(f"РћР¶РёРґР°Р»РѕСЃСЊ {expected!r}, РїРѕР»СѓС‡РµРЅРѕ {t!r}")
        self.pos += 1
        return t

    def parse_or(self):
        node = self.parse_and()
        while self.peek() == "РёР»Рё":
            self.consume()
            node = BinaryOp(node, "РёР»Рё", self.parse_and())
        return node

    def parse_and(self):
        node = self.parse_not()
        while self.peek() == "Рё":
            self.consume()
            node = BinaryOp(node, "Рё", self.parse_not())
        return node

    def parse_not(self):
        if self.peek() == "РЅРµ":
            self.consume()
            return UnaryOp("РЅРµ", self.parse_not())
        return self.parse_comparison()

    def parse_comparison(self):
        node = self.parse_addition()
        ops = {"==", "!=", ">", "<", ">=", "<=", "СЃРѕРґРµСЂР¶РёС‚", "РЅР°С‡РёРЅР°РµС‚СЃСЏ_СЃ", "РІ"}
        while self.peek() in ops:
            op = self.consume()
            node = BinaryOp(node, op, self.parse_addition())
        return node

    def parse_addition(self):
        node = self.parse_multiplication()
        while self.peek() in ("+", "-"):
            op = self.consume()
            node = BinaryOp(node, op, self.parse_multiplication())
        return node

    def parse_multiplication(self):
        node = self.parse_power()
        while self.peek() in ("*", "/", "//", "%"):
            op = self.consume()
            node = BinaryOp(node, op, self.parse_power())
        return node

    def parse_power(self):
        node = self.parse_unary()
        if self.peek() == "**":
            self.consume()
            node = BinaryOp(node, "**", self.parse_power())   # РїСЂР°РІРѕР°СЃСЃРѕС†РёР°С‚РёРІРЅС‹Р№
        return node

    def parse_unary(self):
        if self.peek() == "-":
            self.consume()
            return UnaryOp("-", self.parse_unary())
        return self.parse_atom()

    def parse_atom(self):
        t = self.peek()
        if t is None:
            raise SyntaxError("РќРµРѕР¶РёРґР°РЅРЅС‹Р№ РєРѕРЅРµС† РІС‹СЂР°Р¶РµРЅРёСЏ")

        # СЃРєРѕР±РєРё
        if t == "(":
            self.consume("(")
            node = self.parse_or()
            self.consume(")")
            return self._parse_postfix(node)

        # СЃРїРёСЃРѕРє [a, b, c]
        if t == "[":
            self.consume("[")
            items = []
            while self.peek() != "]":
                if items:
                    self.consume(",")
                items.append(self.parse_or())
            self.consume("]")
            return self._parse_postfix(ListLiteral(items))

        # СЃС‚СЂРѕРєРё
        if t.startswith('"') or t.startswith("'"):
            self.consume()
            return Literal(t[1:-1].replace('\\n', '\n'))

        # bool / None
        if t in ("РёСЃС‚РёРЅР°", "true"):
            self.consume(); return Literal(True)
        if t in ("Р»РѕР¶СЊ", "false"):
            self.consume(); return Literal(False)
        if t in ("РїСѓСЃС‚Рѕ", "None", "null"):
            self.consume(); return Literal(None)

        # С‡РёСЃР»Р°
        if re.match(r'^\d+(?:\.\d+)?$', t):
            self.consume()
            return Literal(int(t) if '.' not in t else float(t))

        # РёРґРµРЅС‚РёС„РёРєР°С‚РѕСЂ, РІС‹Р·РѕРІ С„СѓРЅРєС†РёРё РёР»Рё РёРЅРґРµРєСЃРёСЂРѕРІР°РЅРёРµ
        if re.match(r'^[Р°-СЏС‘Рђ-РЇРЃa-zA-Z_][Р°-СЏС‘Рђ-РЇРЃa-zA-Z0-9_.]*$', t):
            name = self.consume()
            if self.peek() == "(":
                self.consume("(")
                args = []
                while self.peek() != ")":
                    if args:
                        self.consume(",")
                    args.append(self.parse_or())
                self.consume(")")
                return self._parse_postfix(Call(name, args))
            return self._parse_postfix(Variable(name))

        raise SyntaxError(f"РќРµРѕР¶РёРґР°РЅРЅС‹Р№ С‚РѕРєРµРЅ РІ РІС‹СЂР°Р¶РµРЅРёРё: {t!r}")

    def _parse_postfix(self, node):
        """РћР±СЂР°Р±Р°С‚С‹РІР°РµС‚ РїРѕСЃС‚С„РёРєСЃРЅС‹Рµ РѕРїРµСЂР°С‚РѕСЂС‹: obj[key]."""
        while self.peek() == "[":
            self.consume("[")
            key = self.parse_or()
            self.consume("]")
            node = Index(node, key)
        return node


# в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ Tokeniser в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ

def tokenise(text: str):
    """Split source into logical lines, stripping comments."""
    lines = []
    for raw in text.splitlines():
        line = raw.split("#")[0].rstrip()
        if line.strip():
            lines.append(line)
    return lines


def indent_of(line: str) -> int:
    return len(line) - len(line.lstrip())


def parse_string_expr(raw: str) -> list:
    """
    Р Р°Р·Р±РёСЂР°РµС‚ СЃС‚СЂРѕРєСѓ-С€Р°Р±Р»РѕРЅ РІ СЃРїРёСЃРѕРє С‡Р°СЃС‚РµР№ [str | Variable | BinaryOp ...].

    РџРѕРґРґРµСЂР¶РёРІР°РµС‚:
      "РџСЂРёРІРµС‚ " + РёРјСЏ + " РєР°Рє РґРµР»Р°"  в†’  [str, Variable, str]
      "РџСЂРёРІРµС‚ {РёРјСЏ}!"                в†’  [str, Variable, str]
      РёРјСЏ + " Р±Р°Р»Р°РЅСЃ: " + Р±Р°Р»Р°РЅСЃ     в†’  С†РµРїРѕС‡РєР° С‡РµСЂРµР· +

    Р’РѕР·РІСЂР°С‰Р°РµС‚ СЃРїРёСЃРѕРє, СЃРѕРІРјРµСЃС‚РёРјС‹Р№ СЃ ctx.render().
    """
    raw = raw.strip()

    # РЁР°Р±Р»РѕРЅ РІРёРґР° "РџСЂРёРІРµС‚ {РёРјСЏ}!" вЂ” СЃС‚СЂРѕРєР° СЃ {} РІРЅСѓС‚СЂРё
    stripped_quote = None
    if (raw.startswith('"') and raw.endswith('"')) or (raw.startswith("'") and raw.endswith("'")):
        stripped_quote = raw[1:-1].replace('\\n', '\n')
    if stripped_quote and '{' in stripped_quote:
        parts = []
        pattern = r'\{([^}]+)\}'
        last_end = 0
        for match in re.finditer(pattern, stripped_quote):
            if match.start() > last_end:
                parts.append(stripped_quote[last_end:match.start()])
            # РІРЅСѓС‚СЂРё {} РјРѕР¶РµС‚ Р±С‹С‚СЊ Р»СЋР±РѕРµ РІС‹СЂР°Р¶РµРЅРёРµ
            inner = match.group(1).strip()
            try:
                parts.append(parse_expr(inner))
            except SyntaxError:
                parts.append(Variable(inner))
            last_end = match.end()
        if last_end < len(stripped_quote):
            parts.append(stripped_quote[last_end:])
        return parts if parts else [""]

    # РџР°СЂСЃРёРј РєР°Рє РїРѕР»РЅРѕРµ РІС‹СЂР°Р¶РµРЅРёРµ С‡РµСЂРµР· Expression AST
    try:
        node = parse_expr(raw)
        # Р•СЃР»Рё СЌС‚Рѕ РїСЂРѕСЃС‚Рѕ СЃС‚СЂРѕРєРѕРІС‹Р№ Literal вЂ” РІРѕР·РІСЂР°С‰Р°РµРј РЅР°РїСЂСЏРјСѓСЋ
        if isinstance(node, Literal) and isinstance(node.value, str):
            return [node.value]
        # Р•СЃР»Рё СЌС‚Рѕ BinaryOp(+) РЅР° РІРµСЂС…РЅРµРј СѓСЂРѕРІРЅРµ вЂ” СЂР°СЃРєР»Р°РґС‹РІР°РµРј РІ СЃРїРёСЃРѕРє
        return _flatten_concat(node)
    except SyntaxError:
        # Р¤РѕР»Р»Р±СЌРє: РІРµСЂРЅСѓС‚СЊ РєР°Рє СЃС‚СЂРѕРєСѓ
        return [raw]


def _flatten_concat(node) -> list:
    """Р Р°Р·РІРѕСЂР°С‡РёРІР°РµС‚ С†РµРїРѕС‡РєСѓ BinaryOp('+') РІ РїР»РѕСЃРєРёР№ СЃРїРёСЃРѕРє С‡Р°СЃС‚РµР№."""
    if isinstance(node, BinaryOp) and node.op == "+":
        return _flatten_concat(node.left) + _flatten_concat(node.right)
    if isinstance(node, Literal) and isinstance(node.value, str):
        return [node.value]
    if isinstance(node, Literal):
        return [str(node.value)]
    # Variable Рё РІСЃС‘ РѕСЃС‚Р°Р»СЊРЅРѕРµ вЂ” РѕСЃС‚Р°РІР»СЏРµРј РєР°Рє РµСЃС‚СЊ (executor РІС‹С‡РёСЃР»РёС‚)
    return [node]


def _unwrap_literal(node):
    """Р Р°Р·РІРѕСЂР°С‡РёРІР°РµС‚ Literal РІ РїСЂРёРјРёС‚РёРІРЅРѕРµ Р·РЅР°С‡РµРЅРёРµ (РґР»СЏ РєРЅРѕРїРѕРє, globals Рё С‚.Рґ.)"""
    if isinstance(node, Literal):
        return node.value
    return node


def parse_value(raw: str):
    """РћР±С‘СЂС‚РєР° РґР»СЏ РѕР±СЂР°С‚РЅРѕР№ СЃРѕРІРјРµСЃС‚РёРјРѕСЃС‚Рё вЂ” РґРµР»РµРіРёСЂСѓРµС‚ РІ parse_expr."""
    raw = raw.strip()
    if raw.startswith(("[", "{")) and raw.endswith(("]", "}")):
        try:
            return _json.loads(raw)
        except _json.JSONDecodeError:
            pass
    # РњР°СЃСЃРёРІ: ["A", "B", "C"] вЂ” РЅРµ РїРѕРґРґРµСЂР¶РёРІР°РµС‚СЃСЏ expression-РїР°СЂСЃРµСЂРѕРј
    if raw.startswith('[') and raw.endswith(']'):
        items_str = raw[1:-1].strip()
        if not items_str:
            return []
        items = []
        for item in re.split(r',\s*', items_str):
            items.append(parse_value(item.strip()))
        return items
    try:
        node = parse_expr(raw)
        # Р”Р»СЏ РїСЂРѕСЃС‚С‹С… Р»РёС‚РµСЂР°Р»РѕРІ СЃСЂР°Р·Сѓ РІРѕР·РІСЂР°С‰Р°РµРј Р·РЅР°С‡РµРЅРёРµ (РЅРµ Literal-РѕР±С‘СЂС‚РєСѓ)
        # С‡С‚РѕР±С‹ РѕРЅРё РЅРµ Р»РѕРјР°Р»Рё JSON-СЃРµСЂРёР°Р»РёР·Р°С†РёСЋ РІ РєРЅРѕРїРєР°С… Рё globals
        return _unwrap_literal(node)
    except SyntaxError:
        return VarRef(raw)  # СЃРѕРІРјРµСЃС‚РёРјРѕСЃС‚СЊ: РЅРµСЂР°СЃРїРѕР·РЅР°РЅРЅРѕРµ в†’ VarRef


def _parse_inline_button_row_labels(rest: str) -> list:
    """
    РЎРїРёСЃРѕРє РїРѕРґРїРёСЃРµР№ РґР»СЏ РѕРґРЅРѕРіРѕ СЂСЏРґР° РєРЅРѕРїРѕРє РїРѕСЃР»Рµ СЃР»РѕРІР° В«РєРЅРѕРїРєРёВ».
    РџРѕРґРґРµСЂР¶РєР°:
      РєРЅРѕРїРєРё "A" "B" "C"
      РєРЅРѕРїРєРё "A|B|C"     вЂ” РѕРґРёРЅ СЂСЏРґ РёР· С‚СЂС‘С… РєРЅРѕРїРѕРє (С‡Р°СЃС‚С‹Р№ С„РѕСЂРјР°С‚ РёР· РґРѕРєСѓРјРµРЅС‚Р°С†РёРё DSL)
    """
    rest = rest.strip()
    labels = re.findall(r'"([^"]+)"', rest)
    if len(labels) == 1 and "|" in labels[0]:
        return [part.strip() for part in labels[0].split("|") if part.strip()]
    return labels


def parse_simple_condition(raw: str) -> "BinaryOp | UnaryOp | Variable | Literal":
    """РџР°СЂСЃРёС‚ РѕРґРЅРѕ СѓСЃР»РѕРІРёРµ С‡РµСЂРµР· Expression AST.

    Р’РѕР·РІСЂР°С‰Р°РµС‚ Expression-СѓР·РµР», РєРѕС‚РѕСЂС‹Р№ executor РІС‹С‡РёСЃР»РёС‚ С‡РµСЂРµР· eval_expr().
    Р”Р»СЏ СЃРѕРІРјРµСЃС‚РёРјРѕСЃС‚Рё РјРѕР¶РµС‚ РІРµСЂРЅСѓС‚СЊ Condition (СЃС‚Р°СЂС‹Р№ РїСѓС‚СЊ) РµСЃР»Рё parse_expr РЅРµ СЃРїСЂР°РІРёР»СЃСЏ.
    """
    raw = raw.strip()
    try:
        return parse_expr(raw)
    except SyntaxError:
        # Р¤РѕР»Р»Р±СЌРє РЅР° СЃС‚Р°СЂС‹Р№ РїР°СЂСЃРµСЂ СѓСЃР»РѕРІРёР№
        negate = False
        if raw.startswith("РЅРµ "):
            negate = True
            raw = raw[3:].strip()
        for op in ("==", "!=", ">=", "<=", ">", "<", "СЃРѕРґРµСЂР¶РёС‚"):
            if op in raw:
                left, right = raw.split(op, 1)
                return Condition(VarRef(left.strip()), op, VarRef(right.strip()), negate)
        return Condition(VarRef(raw), "!=", "", negate)


def parse_condition(raw: str):
    """РџР°СЂСЃРёС‚ СѓСЃР»РѕРІРёРµ (РїСЂРѕСЃС‚РѕРµ РёР»Рё СЃР»РѕР¶РЅРѕРµ) С‡РµСЂРµР· Expression AST."""
    raw = raw.strip()
    try:
        return parse_expr(raw)
    except SyntaxError:
        # Р¤РѕР»Р»Р±СЌРє РЅР° СЃС‚Р°СЂС‹Р№ РїР°СЂСЃРµСЂ РґР»СЏ СЃРѕРІРјРµСЃС‚РёРјРѕСЃС‚Рё
        or_parts = re.split(r'\s+РёР»Рё\s+', raw)
        if len(or_parts) > 1:
            conditions = [parse_simple_condition(p) for p in or_parts]
            return ComplexCondition(conditions, ["РёР»Рё"] * (len(conditions) - 1))
        and_parts = re.split(r'\s+Рё\s+', raw)
        if len(and_parts) > 1:
            conditions = [parse_simple_condition(p) for p in and_parts]
            return ComplexCondition(conditions, ["Рё"] * (len(conditions) - 1))
        return parse_simple_condition(raw)




# в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ Parser в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ

class Parser:
    def __init__(self, source: str, base_path: str = ""):
        self.lines = tokenise(source)
        self.pos = 0
        self.base_path = base_path  # РґР»СЏ СЂР°Р·СЂРµС€РµРЅРёСЏ РёРјРїРѕСЂС‚РѕРІ

    def peek(self):
        if self.pos < len(self.lines):
            return self.lines[self.pos]
        return None

    def consume(self):
        line = self.lines[self.pos]
        self.pos += 1
        return line

    def parse(self) -> Program:
        prog = Program()

        while self.pos < len(self.lines):
            line = self.peek().strip()

            # в”Ђв”Ђ РІРµСЂСЃРёСЏ "1.0" в”Ђв”Ђ
            m = re.match(r'^РІРµСЂСЃРёСЏ\s+"([^"]+)"$', line)
            if m:
                prog.config["version"] = m.group(1)
                self.consume()
                continue

            # в”Ђв”Ђ РєРѕРјР°РЅРґС‹: (РјРµРЅСЋ ботР°) в”Ђв”Ђ
            if line == "РєРѕРјР°РЅРґС‹:" or line == "РєРѕРјР°РЅРґС‹":
                self.consume()
                commands = self._parse_commands_block()
                prog.config["commands"] = commands
                continue

            # в”Ђв”Ђ РіР»РѕР±Р°Р»СЊРЅРѕ РїРµСЂРµРјРµРЅРЅР°СЏ = Р·РЅР°С‡РµРЅРёРµ в”Ђв”Ђ
            m = re.match(r'^РіР»РѕР±Р°Р»СЊРЅРѕ\s+(\w+)\s*=\s*(.+)$', line)
            if m:
                self.consume()
                prog.globals[m.group(1)] = parse_value(m.group(2))
                continue

            # в”Ђв”Ђ бот "TOKEN" в”Ђв”Ђ
            m = re.match(r'^бот\s+"([^"]+)"$', line)
            if m:
                prog.config["token"] = m.group(1)
                self.consume()
                continue

            # в”Ђв”Ђ РёРјРїРѕСЂС‚ "С„Р°Р№Р».ccd" РёР»Рё РёРјРїРѕСЂС‚ "cicada.shop" в”Ђв”Ђ
            m = re.match(r'^РёРјРїРѕСЂС‚\s+"([^"]+)"$', line)
            if m:
                import_path = m.group(1)
                self.consume()
                # Р—Р°РіСЂСѓР¶Р°РµРј Рё РїР°СЂСЃРёРј РёРјРїРѕСЂС‚РёСЂРѕРІР°РЅРЅС‹Р№ С„Р°Р№Р»
                try:
                    import os
                    # РџР°РєРµС‚РЅР°СЏ СЃРёСЃС‚РµРјР°: cicada.shop -> cicada_modules/shop/index.ccd
                    if import_path.startswith("cicada."):
                        package_parts = import_path.split(".")
                        package_path = os.path.join("cicada_modules", *package_parts[1:], "index.ccd")
                        full_path = os.path.join(self.base_path, package_path)
                        # Р•СЃР»Рё РЅРµ РЅР°Р№РґРµРЅ РєР°Рє РїР°РєРµС‚, РїСЂРѕР±СѓРµРј РєР°Рє РѕР±С‹С‡РЅС‹Р№ РїСѓС‚СЊ
                        if not os.path.exists(full_path):
                            alt_path = os.path.join(self.base_path, *package_parts[1:]) + ".ccd"
                            if os.path.exists(alt_path):
                                full_path = alt_path
                    else:
                        full_path = os.path.join(self.base_path, import_path)
                    
                    with open(full_path, "r", encoding="utf-8") as f:
                        import_source = f.read()
                    import_dir = os.path.dirname(full_path)
                    import_parser = Parser(import_source, import_dir)
                    import_prog = import_parser.parse()
                    # РћР±СЉРµРґРёРЅСЏРµРј РјРѕРґСѓР»СЊ С†РµР»РёРєРѕРј: config, globals, blocks, handlers, scenarios
                    merge_programs(prog, import_prog)
                except FileNotFoundError:
                    raise SyntaxError(f"РРјРїРѕСЂС‚ РЅРµ РЅР°Р№РґРµРЅ: {import_path}")
                except Exception as e:
                    raise SyntaxError(f"РћС€РёР±РєР° РёРјРїРѕСЂС‚Р° {import_path}: {e}")
                continue

            # в”Ђв”Ђ РєРЅРѕРїРєРё: (Р±Р»РѕС‡РЅС‹Р№ С„РѕСЂРјР°С‚ СЃ РјР°С‚СЂРёС†РµР№) в”Ђв”Ђ
            if line == "РєРЅРѕРїРєРё:" or line == "РєРЅРѕРїРєРё":
                self.consume()
                matrix = []
                base_indent = None
                while self.pos < len(self.lines):
                    row_line = self.lines[self.pos]
                    stripped = row_line.strip()
                    if not stripped:
                        self.consume()
                        continue
                    # РћРїСЂРµРґРµР»СЏРµРј Р±Р°Р·РѕРІС‹Р№ РѕС‚СЃС‚СѓРї
                    if base_indent is None and row_line.startswith(" "):
                        base_indent = len(row_line) - len(row_line.lstrip())
                    current_indent = len(row_line) - len(row_line.lstrip()) if row_line.startswith(" ") else 0
                    # Р•СЃР»Рё РѕС‚СЃС‚СѓРї СѓРјРµРЅСЊС€РёР»СЃСЏ Рё СЃС‚СЂРѕРєР° РЅРµ РїСѓСЃС‚Р°СЏ - РєРѕРЅРµС† Р±Р»РѕРєР°
                    if base_indent and current_indent < base_indent and stripped:
                        break
                    # РџР°СЂСЃРёРј СЃС‚СЂРѕРєСѓ РєР°Рє РјР°СЃСЃРёРІ
                    if stripped.startswith("[") and stripped.endswith("]"):
                        self.consume()
                        row = parse_value(stripped)
                        if isinstance(row, list):
                            matrix.append(row)
                    else:
                        # РќРµРёР·РІРµСЃС‚РЅР°СЏ СЃС‚СЂРѕРєР° - РІС‹С…РѕРґРёРј
                        break
                if matrix:
                    prog.handlers.append(Handler("reply", None, [Buttons(matrix)]))
                continue

            # в”Ђв”Ђ РґРѕ РєР°Р¶РґРѕРіРѕ: (middleware) в”Ђв”Ђ
            if line.startswith("РґРѕ РєР°Р¶РґРѕРіРѕ:") or line == "РґРѕ РєР°Р¶РґРѕРіРѕ":
                self.consume()
                body = self._parse_block()
                prog.handlers.append(Handler("before_each", None, body))
                continue

            # в”Ђв”Ђ РїРѕСЃР»Рµ РєР°Р¶РґРѕРіРѕ: (middleware) в”Ђв”Ђ
            if line.startswith("РїРѕСЃР»Рµ РєР°Р¶РґРѕРіРѕ:") or line == "РїРѕСЃР»Рµ РєР°Р¶РґРѕРіРѕ":
                self.consume()
                body = self._parse_block()
                prog.handlers.append(Handler("after_each", None, body))
                continue

            # в”Ђв”Ђ РїСЂРё СЃС‚Р°СЂС‚Рµ: РёР»Рё СЃС‚Р°СЂС‚: в”Ђв”Ђ
            if line.startswith("РїСЂРё СЃС‚Р°СЂС‚Рµ:") or line == "РїСЂРё СЃС‚Р°СЂС‚Рµ" or line.startswith("СЃС‚Р°СЂС‚:") or line == "СЃС‚Р°СЂС‚":
                self.consume()
                body = self._parse_block()
                prog.handlers.append(Handler("start", None, body))
                continue

            # в”Ђв”Ђ РїСЂРё РєРѕРјР°РЅРґРµ "/cmd": РёР»Рё РєРѕРјР°РЅРґР° "/cmd": в”Ђв”Ђ
            m = re.match(r'^РїСЂРё РєРѕРјР°РЅРґРµ\s+"(/\w+)"\s*:', line)
            if not m:
                m = re.match(r'^РєРѕРјР°РЅРґР°\s+"(/\w+)"\s*:', line)
            if m:
                cmd = m.group(1)
                self.consume()
                body = self._parse_block()
                prog.handlers.append(Handler("command", cmd, body))
                continue

            # в”Ђв”Ђ РїСЂРё С‚РµРєСЃС‚Рµ "СЃР»РѕРІРѕ": вЂ” С…РµРЅРґР»РµСЂ РЅР° РєРѕРЅРєСЂРµС‚РЅС‹Р№ С‚РµРєСЃС‚ в”Ђв”Ђ
            m = re.match(r'^РїСЂРё С‚РµРєСЃС‚Рµ\s+"([^"]+)"\s*:', line)
            if m:
                self.consume()
                body = self._parse_block()
                prog.handlers.append(Handler("text", m.group(1), body))
                continue

            # в”Ђв”Ђ РїСЂРё С‚РµРєСЃС‚Рµ: вЂ” С…РµРЅРґР»РµСЂ РЅР° Р»СЋР±РѕР№ С‚РµРєСЃС‚ в”Ђв”Ђ
            if line.startswith("РїСЂРё С‚РµРєСЃС‚Рµ:") or line == "РїСЂРё С‚РµРєСЃС‚Рµ":
                self.consume()
                body = self._parse_block()
                prog.handlers.append(Handler("text", None, body))
                continue

            # в”Ђв”Ђ РїСЂРё РЅР°Р¶Р°С‚РёРё "callback": РёР»Рё РїСЂРё РЅР°Р¶Р°С‚РёРё: в”Ђв”Ђ
            m = re.match(r'^РїСЂРё РЅР°Р¶Р°С‚РёРё\s+"([^"]+)"\s*:', line)
            if m:
                callback = m.group(1)
                self.consume()
                body = self._parse_block()
                prog.handlers.append(Handler("callback", callback, body))
                continue
            
            if line.startswith("РїСЂРё РЅР°Р¶Р°С‚РёРё:") or line == "РїСЂРё РЅР°Р¶Р°С‚РёРё":
                self.consume()
                body = self._parse_block()
                prog.handlers.append(Handler("callback", None, body))
                continue

            # в”Ђв”Ђ РёРЅР°С‡Рµ: (РІРµСЂС…РЅРµСѓСЂРѕРІРЅРµРІС‹Р№) в”Ђв”Ђ
            if line.startswith("РёРЅР°С‡Рµ:") or line == "РёРЅР°С‡Рµ":
                self.consume()
                body = self._parse_block()
                prog.handlers.append(Handler("else", None, body))
                continue

            # в”Ђв”Ђ РµСЃР»Рё СѓСЃР»РѕРІРёРµ: в”Ђв”Ђ
            m = re.match(r'^РµСЃР»Рё\s+(.+):\s*$', line)
            if m:
                self.consume()
                cond = parse_condition(m.group(1))
                then_body = self._parse_block()
                prog.handlers.append(
                    Handler("text", None, [If(cond, then_body, [])])
                )
                continue

            # в”Ђв”Ђ РїСЂРё РїРѕР»СѓС‡РµРЅРёРё С„РѕС‚Рѕ: в”Ђв”Ђ
            if line.startswith("РїСЂРё С„РѕС‚Рѕ:") or line == "РїСЂРё С„РѕС‚Рѕ":
                self.consume()
                body = self._parse_block()
                prog.handlers.append(Handler("photo_received", None, body))
                continue

            # в”Ђв”Ђ РїСЂРё РїРѕР»СѓС‡РµРЅРёРё РґРѕРєСѓРјРµРЅС‚Р°: в”Ђв”Ђ
            # README Рё СЃС†РµРЅР°СЂРёРё С‡Р°СЃС‚Рѕ РїРёС€СѓС‚ В«РїСЂРё РґРѕРєСѓРјРµРЅС‚:В» вЂ” РїРѕРґРґРµСЂР¶РёРІР°РµРј РЅР°СЂСЏРґСѓ СЃ В«РїСЂРё РґРѕРєСѓРјРµРЅС‚Рµ:В»
            if (
                line.startswith("РїСЂРё РґРѕРєСѓРјРµРЅС‚Рµ:")
                or line == "РїСЂРё РґРѕРєСѓРјРµРЅС‚Рµ"
                or line.startswith("РїСЂРё РґРѕРєСѓРјРµРЅС‚:")
                or line == "РїСЂРё РґРѕРєСѓРјРµРЅС‚"
            ):
                self.consume()
                body = self._parse_block()
                prog.handlers.append(Handler("document_received", None, body))
                continue

            # в”Ђв”Ђ РїСЂРё РїРѕР»СѓС‡РµРЅРёРё РіРѕР»РѕСЃРѕРІРѕРіРѕ: в”Ђв”Ђ
            if line.startswith("РїСЂРё РіРѕР»РѕСЃРѕРІРѕРј:") or line == "РїСЂРё РіРѕР»РѕСЃРѕРІРѕРј":
                self.consume()
                body = self._parse_block()
                prog.handlers.append(Handler("voice_received", None, body))
                continue

            # в”Ђв”Ђ РїСЂРё РїРѕР»СѓС‡РµРЅРёРё СЃС‚РёРєРµСЂР°: в”Ђв”Ђ
            if line.startswith("РїСЂРё СЃС‚РёРєРµСЂРµ:") or line == "РїСЂРё СЃС‚РёРєРµСЂРµ":
                self.consume()
                body = self._parse_block()
                prog.handlers.append(Handler("sticker_received", None, body))
                continue

            # в”Ђв”Ђ РїСЂРё РіРµРѕР»РѕРєР°С†РёРё: в”Ђв”Ђ
            if line.startswith("РїСЂРё РіРµРѕР»РѕРєР°С†РёРё:") or line == "РїСЂРё РіРµРѕР»РѕРєР°С†РёРё":
                self.consume()
                body = self._parse_block()
                prog.handlers.append(Handler("location_received", None, body))
                continue

            # в”Ђв”Ђ РїСЂРё РєРѕРЅС‚Р°РєС‚Рµ: в”Ђв”Ђ
            if line.startswith("РїСЂРё РєРѕРЅС‚Р°РєС‚Рµ:") or line == "РїСЂРё РєРѕРЅС‚Р°РєС‚Рµ":
                self.consume()
                body = self._parse_block()
                prog.handlers.append(Handler("contact_received", None, body))
                continue

            # в”Ђв”Ђ СЃС†РµРЅР°СЂРёР№ РёРјСЏ: в”Ђв”Ђ
            m = re.match(r'^СЃС†РµРЅР°СЂРёР№\s+(\w+)\s*:', line)
            if m:
                name = m.group(1)
                self.consume()
                steps = self._parse_block()
                prog.scenarios[name] = steps
                continue

            # в”Ђв”Ђ Р±Р»РѕРє РёРјСЏ: в”Ђв”Ђ
            m = re.match(r'^Р±Р»РѕРє\s+(\w+)\s*:', line)
            if m:
                name = m.group(1)
                self.consume()
                body = self._parse_block()
                prog.blocks[name] = Block(name, body)
                continue

            # Р»СЋР±С‹Рµ РґСЂСѓРіРёРµ РІРµСЂС…РЅРµСѓСЂРѕРІРЅРµРІС‹Рµ РёРЅСЃС‚СЂСѓРєС†РёРё в†’ РІ РґРµС„РѕР»С‚РЅС‹Р№ РѕР±СЂР°ботС‡РёРє
            stmt = self._parse_stmt(self.consume())
            if stmt:
                prog.handlers.append(Handler("any", None, [stmt]))

        return prog

    def _parse_block(self) -> list:
        """Р§РёС‚Р°РµС‚ СЃ РѕС‚СЃС‚СѓРїРѕРј Р±Р»РѕРє РёРЅСЃС‚СЂСѓРєС†РёР№."""
        stmts = []
        base = None
        while self.pos < len(self.lines):
            line = self.peek()
            ind = indent_of(line)
            stripped = line.strip()

            if base is None:
                if ind == 0:
                    break
                base = ind
            else:
                if ind < base:
                    break

            # РІР»РѕР¶РµРЅРЅС‹Рµ РµСЃР»Рё
            m = re.match(r'^РµСЃР»Рё\s+(.+):\s*$', stripped)
            if m:
                self.consume()
                cond = parse_condition(m.group(1))
                then_body = self._parse_block()
                else_body = []
                if self.peek() and self.peek().strip().startswith("РёРЅР°С‡Рµ"):
                    self.consume()
                    else_body = self._parse_block()
                stmts.append(If(cond, then_body, else_body))
                continue

            # С€Р°Рі РІ СЃС†РµРЅР°СЂРёРё
            m = re.match(r'^С€Р°Рі\s+(\w+):\s*$', stripped)
            if m:
                self.consume()
                step_name = m.group(1)
                step_body = self._parse_block()
                stmts.append(Step(step_name, step_body))
                continue

            # РґР»СЏ РєР°Р¶РґРѕРіРѕ VAR РІ COLLECTION:
            m = re.match(r'^РґР»СЏ РєР°Р¶РґРѕРіРѕ\s+(\w+)\s+РІ\s+(.+):\s*$', stripped)
            if m:
                self.consume()
                var_name = m.group(1)
                collection = parse_value(m.group(2).strip())
                body = self._parse_block()
                stmts.append(ForEach(variable=var_name, collection=collection, body=body))
                continue

            # РїРѕРєР° СѓСЃР»РѕРІРёРµ: (С†РёРєР» while вЂ” РЅР°СЃС‚РѕСЏС‰РёР№)
            m = re.match(r'^РїРѕРєР°\s+(.+):\s*$', stripped)
            if m:
                self.consume()
                cond = parse_condition(m.group(1))
                body = self._parse_block()
                stmts.append(WhileLoop(condition=cond, body=body))
                continue

            # РїСЂРµСЂРІР°С‚СЊ вЂ” break
            if stripped == "РїСЂРµСЂРІР°С‚СЊ":
                self.consume()
                stmts.append(BreakLoop())
                continue

            # РїСЂРѕРґРѕР»Р¶РёС‚СЊ вЂ” continue
            if stripped == "РїСЂРѕРґРѕР»Р¶РёС‚СЊ":
                self.consume()
                stmts.append(ContinueLoop())
                continue

            # С‚Р°Р№РјР°СѓС‚ N СЃРµРєСѓРЅРґ: С‚РµР»Рѕ
            m = re.match(r'^С‚Р°Р№РјР°СѓС‚\s+([\d.]+)\s*(?:СЃРµРєСѓРЅРґ|СЃ)?\s*:\s*$', stripped)
            if m:
                self.consume()
                body = self._parse_block()
                stmts.append(Timeout(seconds=float(m.group(1)), body=body))
                continue

            # РїРѕРІС‚РѕСЂСЏС‚СЊ N СЂР°Р·: (С‚РµРїРµСЂСЊ СЂРµР°Р»СЊРЅС‹Р№ С†РёРєР» С‡РµСЂРµР· ForEach)
            m = re.match(r'^РїРѕРІС‚РѕСЂСЏС‚СЊ\s+([\d]+)\s+СЂР°Р·:\s*$', stripped)
            if m:
                self.consume()
                n = int(m.group(1))
                body = self._parse_block()
                stmts.append(ForEach(
                    variable="_",
                    collection=[i for i in range(n)],
                    body=body,
                ))
                continue

            # СЂР°РЅРґРѕРј: (Р±Р»РѕРє СЃР»СѓС‡Р°Р№РЅРѕРіРѕ РѕС‚РІРµС‚Р°)
            if stripped == "СЂР°РЅРґРѕРј:" or stripped == "СЂР°РЅРґРѕРј":
                self.consume()
                variants = []
                while self.pos < len(self.lines):
                    row_line = self.lines[self.pos]
                    row_stripped = row_line.strip()
                    if not row_stripped:
                        self.consume()
                        continue
                    row_ind = len(row_line) - len(row_line.lstrip()) if row_line.startswith(" ") else 0
                    if row_ind <= base:
                        break
                    # СЃС‚СЂРѕРєРё РІРёРґР° "С‚РµРєСЃС‚"
                    m2 = re.match(r'^"([^"]+)"$', row_stripped)
                    if m2:
                        variants.append(m2.group(1))
                        self.consume()
                    else:
                        break
                if variants:
                    stmts.append(RandomReply(variants))
                continue

            # inline-РєРЅРѕРїРєРё: (Р±Р»РѕРє inline РєРЅРѕРїРѕРє)
            # Р’СЃРµ СЂСЏРґС‹ [...] СЃРѕР±РёСЂР°СЋС‚СЃСЏ РІ РѕРґРёРЅ InlineKeyboard вЂ” РѕРґРЅРѕ СЃРѕРѕР±С‰РµРЅРёРµ СЃ InlineKeyboardMarkup
            if stripped.startswith("inline-РєРЅРѕРїРєРё:") or stripped == "inline-РєРЅРѕРїРєРё":
                dyn_match = re.match(r'^inline-РєРЅРѕРїРєРё:\s*РёР·\s+(.+?)\s+РїРѕ\s+([A-Za-z_][\w]*)\s*/\s*([A-Za-z_][\w]*)(?:\s+callback=([^\s]+))?(?:\s+columns=(\d+))?(?:\s+append_back=(true|false))?$', stripped)
                if dyn_match:
                    self.consume()
                    stmts.append(InlineKeyboardFromList(
                        items_expr=parse_expr(dyn_match.group(1)),
                        text_field=dyn_match.group(2),
                        id_field=dyn_match.group(3),
                        callback_prefix=dyn_match.group(4) or "С‚РѕРІР°СЂ_",
                        columns=int(dyn_match.group(5) or "1"),
                        append_back=(dyn_match.group(6) or "true") == "true",
                    ))
                    continue

                self.consume()
                keyboard_rows = []
                while self.pos < len(self.lines):
                    row_line = self.lines[self.pos]
                    row_stripped = row_line.strip()
                    if not row_stripped:
                        self.consume()
                        continue
                    row_ind = len(row_line) - len(row_line.lstrip()) if row_line.startswith(" ") else 0
                    if row_ind <= base:
                        break
                    # СЃС‚СЂРѕРєРё РІРёРґР° ["РўРµРєСЃС‚" в†’ "cb", "РўРµРєСЃС‚2" в†’ "cb2"]
                    if row_stripped.startswith("[") and row_stripped.endswith("]"):
                        self.consume()
                        inner = row_stripped[1:-1]
                        row_btns = []
                        for btn_str in re.split(r',\s*', inner):
                            btn_str = btn_str.strip()
                            # "РўРµРєСЃС‚" в†’ "callback"
                            bm = re.match(r'"([^"]+)"\s*[в†’>-]+\s*"([^"]+)"', btn_str)
                            if bm:
                                row_btns.append(InlineButton(text=bm.group(1), callback=bm.group(2)))
                                continue
                            # "РўРµРєСЃС‚" в†’ url "https://..."
                            bmu = re.match(r'"([^"]+)"\s*[в†’>-]+\s*url\s+"([^"]+)"', btn_str)
                            if bmu:
                                row_btns.append(InlineButton(text=bmu.group(1), url=bmu.group(2)))
                        if row_btns:
                            keyboard_rows.append(row_btns)
                    else:
                        break
                if keyboard_rows:
                    stmts.append(InlineKeyboard(rows=keyboard_rows))
                continue

            # РєРЅРѕРїРєРё: (Р±Р»РѕС‡РЅС‹Р№ С„РѕСЂРјР°С‚ СЃ РјР°С‚СЂРёС†РµР№)
            if stripped == "РєРЅРѕРїРєРё:" or stripped == "РєРЅРѕРїРєРё":
                self.consume()
                matrix = []
                while self.pos < len(self.lines):
                    row_line = self.lines[self.pos]
                    row_stripped = row_line.strip()
                    if not row_stripped:
                        self.consume()
                        continue
                    row_ind = len(row_line) - len(row_line.lstrip()) if row_line.startswith(" ") else 0
                    # РџСЂРѕРІРµСЂСЏРµРј РѕС‚СЃС‚СѓРї - РґРѕР»Р¶РµРЅ Р±С‹С‚СЊ Р±РѕР»СЊС€Рµ base
                    if row_ind <= base:
                        break
                    if row_stripped.startswith("[") and row_stripped.endswith("]"):
                        self.consume()
                        row = parse_value(row_stripped)
                        if isinstance(row, list):
                            matrix.append(row)
                    else:
                        break
                if matrix:
                    stmts.append(Buttons(matrix))
                continue

            self.consume()
            stmt = self._parse_stmt(stripped)
            if stmt:
                stmts.append(stmt)

        return stmts

    def _parse_stmt(self, line: str):
        line = line.strip()

        # РѕС‚РІРµС‚ "С‚РµРєСЃС‚" / РѕС‚РІРµС‚ "С‚РµРєСЃС‚" + РїРµСЂРµРјРµРЅРЅР°СЏ
        m = re.match(r'^РѕС‚РІРµС‚\s+(.+)$', line)
        if m:
            return Reply(parse_string_expr(m.group(1)))

        # СЃРїСЂРѕСЃРёС‚СЊ "РІРѕРїСЂРѕСЃ" в†’ РїРµСЂРµРјРµРЅРЅР°СЏ  (РїРѕРґРґРµСЂР¶РєР° в†’ Рё ->)
        m = re.match(r'^СЃРїСЂРѕСЃРёС‚СЊ\s+"([^"]+)"\s*(?:в†’|->)\s*(\w+)$', line)
        if m:
            return Ask(m.group(1), m.group(2))
        # СЃРїСЂРѕСЃРёС‚СЊ "РІРѕРїСЂРѕСЃ" Р±РµР· РїРµСЂРµРјРµРЅРЅРѕР№ вЂ” РїРѕРєР°Р·С‹РІР°РµРј РІРѕРїСЂРѕСЃ РєР°Рє РѕС‚РІРµС‚
        m = re.match(r'^СЃРїСЂРѕСЃРёС‚СЊ\s+"([^"]+)"$', line)
        if m:
            return Ask(m.group(1), "_last_answer")

        # Р·Р°РїРѕРјРЅРё РїРµСЂРµРјРµРЅРЅР°СЏ = Р·РЅР°С‡РµРЅРёРµ
        m = re.match(r'^Р·Р°РїРѕРјРЅРё\s+(\w+)\s*=\s*(.+)$', line)
        if m:
            return Remember(m.group(1), parse_value(m.group(2)))

        # РїСѓСЃС‚СЊ РїРµСЂРµРјРµРЅРЅР°СЏ = Р·РЅР°С‡РµРЅРёРµ (С‚РёРїРёР·РёСЂРѕРІР°РЅРЅРѕРµ РѕР±СЉСЏРІР»РµРЅРёРµ)
        m = re.match(r'^РїСѓСЃС‚СЊ\s+(\w+)\s*=\s*(.+)$', line)
        if m:
            return Remember(m.group(1), parse_value(m.group(2)))

        # РєРЅРѕРїРєРё "A" "B" - РѕРґРЅР° СЃС‚СЂРѕРєР°
        # РєРЅРѕРїРєРё:
        #     ["A", "B"]
        #     ["C"]
        m = re.match(r'^РєРЅРѕРїРєРё\s+(.+)$', line)
        if m:
            rest = m.group(1).strip()
            # РџСЂРѕРІРµСЂСЏРµРј, РЅР°С‡РёРЅР°РµС‚СЃСЏ Р»Рё СЃ [ - Р·РЅР°С‡РёС‚ СЌС‚Рѕ РјР°С‚СЂРёС†Р°
            if rest.startswith('['):
                # РџР°СЂСЃРёРј РєР°Рє Р·РЅР°С‡РµРЅРёРµ (СЃРїРёСЃРѕРє СЃРїРёСЃРєРѕРІ)
                matrix = parse_value(rest)
                if isinstance(matrix, list) and all(isinstance(row, list) for row in matrix):
                    return Buttons(matrix)
                else:
                    return Buttons([matrix])
            else:
                # РћРґРёРЅ СЂСЏРґ РєРЅРѕРїРѕРє
                labels = _parse_inline_button_row_labels(rest)
                return Buttons([labels])  # РѕР±РѕСЂР°С‡РёРІР°РµРј РІ СЃРїРёСЃРѕРє РґР»СЏ РµРґРёРЅРѕРѕР±СЂР°Р·РёСЏ

        # РєРЅРѕРїРєР° "РўРµРєСЃС‚" -> "callback"
        m = re.match(r'^РєРЅРѕРїРєР°\s+"([^"]+)"\s*->\s*"([^"]+)"$', line)
        if m:
            return InlineButton(text=m.group(1), callback=m.group(2))

        # РєРЅРѕРїРєР° "РўРµРєСЃС‚" -> url "https://..."
        m = re.match(r'^РєРЅРѕРїРєР°\s+"([^"]+)"\s*->\s*url\s+"([^"]+)"$', line)
        if m:
            return InlineButton(text=m.group(1), url=m.group(2))

        # inline РёР· Р±Рґ "РєР»СЋС‡" [С‚РµРєСЃС‚ "name"] [id "id"] [callback "prefix"] [columns=2] [РЅР°Р·Р°Рґ "РќР°Р·Р°Рґ" в†’ "cb"]
        m = re.match(r'^(?:inline|inline-РєРЅРѕРїРєРё)\s+РёР·\s+Р±Рґ\s+(.+)$', line)
        if m:
            rest = m.group(1).strip()
            key_match = re.match(r'^("[^"]+"|\w+)', rest)
            if not key_match:
                raise SyntaxError(f"РќРµ РїРѕРЅРёРјР°СЋ РєР»СЋС‡ Р‘Р” РІ inline РёР· Р±Рґ: {line}")
            key_raw = key_match.group(1)
            options = rest[key_match.end():].strip()

            text_field = "name"
            id_field = "id"
            callback_prefix = ""
            columns = 1
            back_text = ""
            back_callback = ""

            opt = re.search(r'\bС‚РµРєСЃС‚\s+"([^"]+)"', options)
            if opt:
                text_field = opt.group(1)
            opt = re.search(r'\bid\s+"([^"]+)"', options)
            if opt:
                id_field = opt.group(1)
            opt = re.search(r'\bcallback\s+"([^"]*)"', options)
            if opt:
                callback_prefix = opt.group(1)
            opt = re.search(r'\bcolumns\s*=?\s*(\d+)', options)
            if opt:
                columns = int(opt.group(1))
            opt = re.search(r'\bРєРѕР»РѕРЅРєРё\s+(\d+)', options)
            if opt:
                columns = int(opt.group(1))
            opt = re.search(r'\bРЅР°Р·Р°Рґ\s+"([^"]+)"\s*(?:в†’|->)\s*"([^"]+)"', options)
            if opt:
                back_text = opt.group(1)
                back_callback = opt.group(2)

            return InlineKeyboardFromDB(
                key=parse_value(key_raw),
                text_field=text_field,
                id_field=id_field,
                callback_prefix=callback_prefix,
                columns=columns,
                back_text=back_text,
                back_callback=back_callback,
            )

        # РєР°СЂС‚РёРЅРєР°/С„РѕС‚Рѕ "url" РёР»Рё РєР°СЂС‚РёРЅРєР°/С„РѕС‚Рѕ РїРµСЂРµРјРµРЅРЅР°СЏ
        m = re.match(r'^(?:РєР°СЂС‚РёРЅРєР°|С„РѕС‚Рѕ)\s+"([^"]+)"$', line)
        if m:
            return Photo(m.group(1))
        m = re.match(r'^(?:РєР°СЂС‚РёРЅРєР°|С„РѕС‚Рѕ)\s+(\w+)$', line)
        if m:
            return PhotoVar(m.group(1))

        # СЃС‚РёРєРµСЂ "file_id"
        m = re.match(r'^СЃС‚РёРєРµСЂ\s+"([^"]+)"$', line)
        if m:
            return Sticker(m.group(1))

        # РїРµСЂРµСЃР»Р°С‚СЊ С„РѕС‚Рѕ (СЃ РїРѕРґРїРёСЃСЊСЋ РёР»Рё Р±РµР·)
        m = re.match(r'^РїРµСЂРµСЃР»Р°С‚СЊ С„РѕС‚Рѕ\s*"([^"]*)"$', line)
        if m:
            return ForwardPhoto(m.group(1))
        if line == "РїРµСЂРµСЃР»Р°С‚СЊ С„РѕС‚Рѕ":
            return ForwardPhoto()

        # РїРµСЂРµСЃР»Р°С‚СЊ РґРѕРєСѓРјРµРЅС‚ вЂ” Р°Р»РёР°СЃ РґР»СЏ РѕС‚РїСЂР°РІРєРё С‚РµРєСѓС‰РµРіРѕ document file_id РѕР±СЂР°С‚РЅРѕ
        m = re.match(r'^РїРµСЂРµСЃР»Р°С‚СЊ РґРѕРєСѓРјРµРЅС‚\s*"([^"]*)"$', line)
        if m:
            return SendDocument(Variable("С„Р°Р№Р»_id"), m.group(1))
        if line == "РїРµСЂРµСЃР»Р°С‚СЊ РґРѕРєСѓРјРµРЅС‚":
            return SendDocument(Variable("С„Р°Р№Р»_id"), "")

        # РїРµСЂРµСЃР»Р°С‚СЊ РіРѕР»РѕСЃРѕРІРѕРµ/СЃС‚РёРєРµСЂ вЂ” РѕС‚РїСЂР°РІР»СЏРµС‚ РїРѕР»СѓС‡РµРЅРЅС‹Р№ file_id РѕР±СЂР°С‚РЅРѕ РІ С‡Р°С‚
        if line in ("РїРµСЂРµСЃР»Р°С‚СЊ РіРѕР»РѕСЃРѕРІРѕРµ", "РїРµСЂРµСЃР»Р°С‚СЊ РіРѕР»РѕСЃ"):
            return SendVoice(Variable("С„Р°Р№Р»_id"), "")
        if line == "РїРµСЂРµСЃР»Р°С‚СЊ СЃС‚РёРєРµСЂ":
            return Sticker(Variable("С„Р°Р№Р»_id"))

        # Р·Р°РїРѕРјРЅРё С„Р°Р№Р» в†’ РїРµСЂРµРјРµРЅРЅР°СЏ
        m = re.match(r'^Р·Р°РїРѕРјРЅРё С„Р°Р№Р»\s*в†’\s*(\w+)$', line)
        if m:
            return SaveFile(m.group(1))

        # Р·Р°РїСѓСЃС‚РёС‚СЊ СЃС†РµРЅР°СЂРёР№
        m = re.match(r'^Р·Р°РїСѓСЃС‚РёС‚СЊ\s+(\w+)$', line)
        if m:
            return StartScenario(m.group(1))

        # РѕС‚РІРµС‚_md "С‚РµРєСЃС‚" вЂ” Telegram legacy Markdown
        m = re.match(r'^РѕС‚РІРµС‚_md\s+(.+)$', line)
        if m:
            return SendMarkdown(parse_string_expr(m.group(1)))

        # РѕС‚РІРµС‚_html "С‚РµРєСЃС‚" вЂ” Telegram HTML
        m = re.match(r'^РѕС‚РІРµС‚_html\s+(.+)$', line)
        if m:
            return SendHTML(parse_string_expr(m.group(1)))

        # РѕС‚РІРµС‚_md2 / РѕС‚РІРµС‚_markdown_v2 "С‚РµРєСЃС‚" вЂ” Telegram MarkdownV2
        m = re.match(r'^(?:РѕС‚РІРµС‚_md2|РѕС‚РІРµС‚_markdown_v2)\s+(.+)$', line)
        if m:
            return SendMarkdownV2(parse_string_expr(m.group(1)))

        # РґРѕРєСѓРјРµРЅС‚ "РїСѓС‚СЊ" / РґРѕРєСѓРјРµРЅС‚ "РїСѓС‚СЊ" "РїРѕРґРїРёСЃСЊ" / РґРѕРєСѓРјРµРЅС‚ "РїСѓС‚СЊ" РёРјСЏ="name" / РґРѕРєСѓРјРµРЅС‚ РїРµСЂРµРјРµРЅРЅР°СЏ
        m = re.match(r'^РґРѕРєСѓРјРµРЅС‚\s+"([^"]+)"(?:\s+РёРјСЏ="[^"]*")?(?:\s+"([^"]*)")?$', line)
        if m:
            return SendDocument(m.group(1), m.group(2) or "")
        m = re.match(r'^РґРѕРєСѓРјРµРЅС‚\s+(\w+)$', line)
        if m:
            return SendDocument(Variable(m.group(1)), "")

        # РѕС‚РїСЂР°РІРёС‚СЊ С„Р°Р№Р» вЂ¦ вЂ” Р°Р»РёР°СЃ В«РґРѕРєСѓРјРµРЅС‚В» (РёРЅР°С‡Рµ СЃС‚СЂРѕРєР° РЅРµ РїРѕРїР°РґР°РµС‚ РІ AST Рё РјРѕР»С‡Р° РїСЂРѕРїСѓСЃРєР°РµС‚СЃСЏ)
        m = re.match(r'^РѕС‚РїСЂР°РІРёС‚СЊ С„Р°Р№Р»\s+"([^"]+)"(?:\s+РёРјСЏ="[^"]*")?(?:\s+"([^"]*)")?$', line)
        if m:
            return SendDocument(m.group(1), m.group(2) or "")
        m = re.match(r'^РѕС‚РїСЂР°РІРёС‚СЊ С„Р°Р№Р»\s+(\w+)$', line)
        if m:
            return SendDocument(Variable(m.group(1)), "")

        # Р°СѓРґРёРѕ "РїСѓС‚СЊ" / Р°СѓРґРёРѕ "РїСѓС‚СЊ" "РїРѕРґРїРёСЃСЊ" / Р°СѓРґРёРѕ РїРµСЂРµРјРµРЅРЅР°СЏ
        m = re.match(r'^Р°СѓРґРёРѕ\s+"([^"]+)"\s*(?:"([^"]*)")?$', line)
        if m:
            return SendAudio(m.group(1), m.group(2) or "")
        m = re.match(r'^Р°СѓРґРёРѕ\s+(\w+)$', line)
        if m:
            return SendAudio(Variable(m.group(1)), "")

        # РІРёРґРµРѕ "РїСѓС‚СЊ" / РІРёРґРµРѕ "РїСѓС‚СЊ" "РїРѕРґРїРёСЃСЊ" / РІРёРґРµРѕ РїРµСЂРµРјРµРЅРЅР°СЏ
        m = re.match(r'^РІРёРґРµРѕ\s+"([^"]+)"\s*(?:"([^"]*)")?$', line)
        if m:
            return SendVideo(m.group(1), m.group(2) or "")
        m = re.match(r'^РІРёРґРµРѕ\s+(\w+)$', line)
        if m:
            return SendVideo(Variable(m.group(1)), "")

        # РіРѕР»РѕСЃ "РїСѓС‚СЊ" / РіРѕР»РѕСЃ РїРµСЂРµРјРµРЅРЅР°СЏ
        m = re.match(r'^РіРѕР»РѕСЃ\s+"([^"]+)"\s*(?:"([^"]*)")?$', line)
        if m:
            return SendVoice(m.group(1), m.group(2) or "")
        m = re.match(r'^РіРѕР»РѕСЃ\s+(\w+)$', line)
        if m:
            return SendVoice(Variable(m.group(1)), "")

        # Р»РѕРєР°С†РёСЏ С€РёСЂРѕС‚Р° РґРѕР»РіРѕС‚Р°
        m = re.match(r'^Р»РѕРєР°С†РёСЏ\s+([\d.\-]+)\s+([\d.\-]+)$', line)
        if m:
            return SendLocation(float(m.group(1)), float(m.group(2)))

        # РєРѕРЅС‚Р°РєС‚ "+С‚РµР»РµС„РѕРЅ" "РРјСЏ"
        m = re.match(r'^РєРѕРЅС‚Р°РєС‚\s+"([^"]+)"\s+"([^"]+)"$', line)
        if m:
            return SendContact(m.group(1), m.group(2))

        # РѕРїСЂРѕСЃ "РІРѕРїСЂРѕСЃ" "РІР°СЂРёР°РЅС‚1" "РІР°СЂРёР°РЅС‚2" ...
        m = re.match(r'^РѕРїСЂРѕСЃ\s+"([^"]+)"\s+(.+)$', line)
        if m:
            options = re.findall(r'"([^"]+)"', m.group(2))
            return SendPoll(m.group(1), options)

        # СЃС‡С‘С‚ "РЅР°Р·РІР°РЅРёРµ" "РѕРїРёСЃР°РЅРёРµ" СЃСѓРјРјР°
        m = re.match(r'^СЃС‡С‘С‚\s+"([^"]+)"\s+"([^"]+)"\s+(\d+)$', line)
        if m:
            return SendInvoice(m.group(1), m.group(2), int(m.group(3)))

        # РёРіСЂР° "short_name"
        m = re.match(r'^РёРіСЂР°\s+"([^"]+)"$', line)
        if m:
            return SendGame(m.group(1))

        # СЃРєР°С‡Р°С‚СЊ С„Р°Р№Р» в†’ РїСѓС‚СЊ
        m = re.match(r'^СЃРєР°С‡Р°С‚СЊ\s+С„Р°Р№Р»\s*в†’\s*"([^"]+)"$', line)
        if m:
            return DownloadFile("С„Р°Р№Р»_id", m.group(1))

        # fetch/http_get URL в†’ РїРµСЂРµРјРµРЅРЅР°СЏ
        m = re.match(r'^(?:fetch|http_get)\s+(.+?)\s*в†’\s*(\w+)$', line)
        if m:
            return HttpGet(url=parse_value(m.group(1)), variable=m.group(2))

        # fetch_json URL в†’ РїРµСЂРµРјРµРЅРЅР°СЏ (GET + JSON.parse)
        m = re.match(r'^fetch_json\s+(.+?)\s*в†’\s*(\w+)$', line)
        if m:
            return FetchJson(url=parse_value(m.group(1)), variable=m.group(2))

        # http_post URL json body в†’ РїРµСЂРµРјРµРЅРЅР°СЏ
        m = re.match(r'^http_post\s+(.+?)\s+json\s+(.+?)\s*в†’\s*(\w+)$', line)
        if m:
            return HttpPost(url=parse_value(m.group(1)), data=parse_value(m.group(2)), variable=m.group(3))

        # http_post URL СЃ data в†’ РїРµСЂРµРјРµРЅРЅР°СЏ
        m = re.match(r'^http_post\s+(.+?)\s+СЃ\s+(.+?)\s*в†’\s*(\w+)$', line)
        if m:
            return HttpPost(url=parse_value(m.group(1)), data=parse_value(m.group(2)), variable=m.group(3))

        # Р»РѕРі "СЃРѕРѕР±С‰РµРЅРёРµ" / Р»РѕРі[level] "СЃРѕРѕР±С‰РµРЅРёРµ"
        m = re.match(r'^Р»РѕРі(?:\[[^\]]*\])?\s+(.+)$', line)
        if m:
            return Log(parse_string_expr(m.group(1)))

        # РїРѕРґРѕР¶РґР°С‚СЊ X / РїР°СѓР·Р° XСЃ / РїР°СѓР·Р° X
        m = re.match(r'^(?:РїРѕРґРѕР¶РґР°С‚СЊ|РїР°СѓР·Р°)\s+([\d.]+)СЃ?$', line)
        if m:
            return Sleep(float(m.group(1)))

        # РїРµС‡Р°С‚Р°РµС‚ XСЃ вЂ” typing action (СЂРµР°Р»РёР·СѓРµРј РєР°Рє Sleep)
        m = re.match(r'^РїРµС‡Р°С‚Р°РµС‚\s+([\d.]+)СЃ?$', line)
        if m:
            return Sleep(float(m.group(1)))

        # tg "sendMessage", {chat_id: С‡Р°С‚, text: "..."}
        m = re.match(r'^tg\s+"([^"]+)"\s*,\s*(.+)$', line)
        if m:
            method = m.group(1)
            params_str = m.group(2)
            # РџСЂРѕСЃС‚РѕР№ РїР°СЂСЃРёРЅРі JSON-РїРѕРґРѕР±РЅРѕРіРѕ РѕР±СЉРµРєС‚Р°
            params = {}
            # РР·РІР»РµРєР°РµРј РїР°СЂС‹ РєР»СЋС‡: Р·РЅР°С‡РµРЅРёРµ
            for match in re.finditer(r'(\w+)\s*:\s*([^,}]+)', params_str):
                key = match.group(1)
                val = match.group(2).strip().strip('"').strip("'")
                params[key] = val
            return TelegramAPI(method, params)

        # Р·Р°РїСЂРѕСЃ GET url в†’ var  /  Р·Р°РїСЂРѕСЃ POST url в†’ var
        m = re.match(r'^Р·Р°РїСЂРѕСЃ\s+(GET|POST|get|post)\s+(.+?)\s*в†’\s*(\w+)$', line)
        if m:
            method = m.group(1).upper()
            url = parse_value(m.group(2))
            var = m.group(3)
            if method == "GET":
                return HttpGet(url=url, variable=var)
            else:
                return HttpPost(url=url, data={}, variable=var)

        # СѓРІРµРґРѕРјР»РµРЅРёРµ в†’ target "С‚РµРєСЃС‚"
        m = re.match(r'^СѓРІРµРґРѕРјР»РµРЅРёРµ\s*в†’\s*(\S+)\s+"([^"]+)"$', line)
        if m:
            return Log([f"[СѓРІРµРґРѕРјР»РµРЅРёРµ в†’ {m.group(1)}] {m.group(2)}"])

        # Р·Р°РїСЂРѕСЃ_Р±Рґ "sql" в†’ var
        m = re.match(r'^Р·Р°РїСЂРѕСЃ_Р±Рґ\s+"([^"]+)"\s*в†’\s*(\w+)$', line)
        if m:
            return Log([f"[Р·Р°РїСЂРѕСЃ_Р±Рґ] {m.group(1)} в†’ {m.group(2)}"])

        # РєР»Р°СЃСЃРёС„РёС†РёСЂРѕРІР°С‚СЊ [...] в†’ var
        m = re.match(r'^РєР»Р°СЃСЃРёС„РёС†РёСЂРѕРІР°С‚СЊ\s+\[([^\]]+)\]\s*в†’\s*(\w+)$', line)
        if m:
            return Log([f"[РєР»Р°СЃСЃРёС„РёС†РёСЂРѕРІР°С‚СЊ] {m.group(1)} в†’ {m.group(2)}"])

        # СЃРѕР±С‹С‚РёРµ "name" { params }  /  СЃРѕР±С‹С‚РёРµ "name"
        m = re.match(r'^СЃРѕР±С‹С‚РёРµ\s+"([^"]+)"', line)
        if m:
            return Log([f"[СЃРѕР±С‹С‚РёРµ] {m.group(1)}"])

        # РѕРїР»Р°С‚Р° provider amount currency "title"
        m = re.match(r'^РѕРїР»Р°С‚Р°\s+(\S+)\s+(\S+)\s+(\S+)\s+"([^"]+)"$', line)
        if m:
            return SendInvoice(title=m.group(4), description="", amount=int(float(m.group(2)) * 100))

        # РјРµРЅСЋ "title": (РЅРµС‚ РїРѕРґРґРµСЂР¶РєРё РІ СЏРґСЂРµ вЂ” РїСЂРѕРїСѓСЃРєР°РµРј С‚РµР»Рѕ, С€Р»С‘Рј РѕС‚РІРµС‚)
        m = re.match(r'^РјРµРЅСЋ\s+"([^"]+)"\s*:', line)
        if m:
            return Reply([m.group(1)])

        # СЃС‚РѕРї вЂ” Р·Р°РІРµСЂС€РёС‚СЊ СЃС†РµРЅР°СЂРёР№ (Р°Р»РёР°СЃ)
        if line == "СЃС‚РѕРї":
            return EndScenario()

        # Р·Р°РІРµСЂС€РёС‚СЊ СЃС†РµРЅР°СЂРёР№
        if line == "Р·Р°РІРµСЂС€РёС‚СЊ СЃС†РµРЅР°СЂРёР№":
            return EndScenario()

        # РІРµСЂРЅСѓС‚СЊ (РёР· С‚РµРєСѓС‰РµРіРѕ С€Р°РіР° СЃС†РµРЅР°СЂРёСЏ)
        if line == "РІРµСЂРЅСѓС‚СЊ":
            return ReturnFromScenario()

        # РїРѕРІС‚РѕСЂРёС‚СЊ С€Р°Рі
        if line == "РїРѕРІС‚РѕСЂРёС‚СЊ С€Р°Рі":
            return RepeatStep()

        # РїРµСЂРµР№С‚Рё Рє С€Р°Рі РёРјСЏ  (РёР»Рё СЃРѕРєСЂР°С‰С‘РЅРЅРѕ: РїРµСЂРµР№С‚Рё РёРјСЏ / РїРµСЂРµР№С‚Рё "РёРјСЏ")
        m = re.match(r'^РїРµСЂРµР№С‚Рё Рє С€Р°Рі\s+(\w+)$', line)
        if m:
            return GotoStep(m.group(1))
        m = re.match(r'^РїРµСЂРµР№С‚Рё\s+"([^"]+)"$', line)
        if m:
            return GotoStep(m.group(1))
        m = re.match(r'^РїРµСЂРµР№С‚Рё\s+(\w+)$', line)
        if m:
            return GotoStep(m.group(1))

        # СЃРѕС…СЂР°РЅРёС‚СЊ "РєР»СЋС‡" = Р·РЅР°С‡РµРЅРёРµ
        m = re.match(r'^СЃРѕС…СЂР°РЅРёС‚СЊ\s+"([^"]+)"\s*=\s*(.+)$', line)
        if m:
            return SaveToDB(m.group(1), parse_value(m.group(2)))

        # РїРѕР»СѓС‡РёС‚СЊ "РєР»СЋС‡" в†’ РїРµСЂРµРјРµРЅРЅР°СЏ
        m = re.match(r'^РїРѕР»СѓС‡РёС‚СЊ\s+"([^"]+)"\s*в†’\s*(\w+)$', line)
        if m:
            return LoadFromDB(m.group(2), m.group(1))

        # РёСЃРїРѕР»СЊР·РѕРІР°С‚СЊ Р±Р»РѕРє
        m = re.match(r'^РёСЃРїРѕР»СЊР·РѕРІР°С‚СЊ\s+(\w+)$', line)
        if m:
            return UseBlock(m.group(1))

        # РІС‹Р·РІР°С‚СЊ "Р±Р»РѕРє" в†’ РїРµСЂРµРјРµРЅРЅР°СЏ
        m = re.match(r'^РІС‹Р·РІР°С‚СЊ\s+"([^"]+)"\s*в†’\s*(\w+)$', line)
        if m:
            return CallBlock(name=m.group(1), variable=m.group(2))
        m = re.match(r'^РІС‹Р·РІР°С‚СЊ\s+"([^"]+)"$', line)
        if m:
            return CallBlock(name=m.group(1), variable="")

        # РіР»РѕР±Р°Р»СЊРЅРѕ РїРµСЂРµРјРµРЅРЅР°СЏ = Р·РЅР°С‡РµРЅРёРµ (РІРЅСѓС‚СЂРё С…РµРЅРґР»РµСЂР°)
        m = re.match(r'^РіР»РѕР±Р°Р»СЊРЅРѕ\s+(\w+)\s*=\s*(.+)$', line)
        if m:
            return GlobalVar(m.group(1), parse_value(m.group(2)))

        # в”Ђв”Ђ РЈРІРµРґРѕРјР»РµРЅРёСЏ в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ

        # СѓРІРµРґРѕРјРёС‚СЊ EXPR "С‚РµРєСЃС‚..." РёР»Рё СѓРІРµРґРѕРјРёС‚СЊ EXPR: "С‚РµРєСЃС‚"
        m = re.match(r'^СѓРІРµРґРѕРјРёС‚СЊ\s+(.+?):\s*"(.+)"$', line)
        if not m:
            m = re.match(r'^СѓРІРµРґРѕРјРёС‚СЊ\s+(.+?)\s+"(.+)"$', line)
        if m:
            return Notify(user_id=parse_value(m.group(1).strip()),
                          parts=parse_string_expr(f'"{m.group(2)}"'))

        # СЂР°СЃСЃС‹Р»РєР° РІСЃРµРј: "С‚РµРєСЃС‚"
        m = re.match(r'^СЂР°СЃСЃС‹Р»РєР° РІСЃРµРј:\s*(.+)$', line)
        if m:
            return Broadcast(parts=parse_string_expr(m.group(1)), segment="")

        # СЂР°СЃСЃС‹Р»РєР° РіСЂСѓРїРїРµ TAG: "С‚РµРєСЃС‚"
        m = re.match(r'^СЂР°СЃСЃС‹Р»РєР° РіСЂСѓРїРїРµ\s+(\S+):\s*(.+)$', line)
        if m:
            return Broadcast(parts=parse_string_expr(m.group(2)), segment=m.group(1))

        # в”Ђв”Ђ Telegram-СЃРїРµС†РёС„РёРєР° в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ

        # РїСЂРѕРІРµСЂРёС‚СЊ РїРѕРґРїРёСЃРєСѓ @РєР°РЅР°Р» в†’ РїРµСЂРµРјРµРЅРЅР°СЏ
        m = re.match(r'^РїСЂРѕРІРµСЂРёС‚СЊ РїРѕРґРїРёСЃРєСѓ\s+(@\S+)\s*в†’\s*(\w+)$', line)
        if m:
            return CheckSubscription(channel=m.group(1), variable=m.group(2))

        # СЂРѕР»СЊ @РєР°РЅР°Р» USER_ID в†’ РїРµСЂРµРјРµРЅРЅР°СЏ
        m = re.match(r'^СЂРѕР»СЊ\s+(@?\S+)\s+(.+?)\s*в†’\s*(\w+)$', line)
        if m:
            return GetChatMemberRole(chat=m.group(1), user_id=parse_value(m.group(2)),
                                     variable=m.group(3))

        # РїРµСЂРµСЃР»Р°С‚СЊ СЃРѕРѕР±С‰РµРЅРёРµ USER_ID
        m = re.match(r'^РїРµСЂРµСЃР»Р°С‚СЊ СЃРѕРѕР±С‰РµРЅРёРµ\s+(.+)$', line)
        if m:
            return ForwardMsg(to_user_id=parse_value(m.group(1).strip()))

        # в”Ђв”Ђ Р Р°ботР° СЃ С„Р°Р№Р»Р°РјРё Рё JSON в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ

        # json_С„Р°Р№Р» "РїСѓС‚СЊ" в†’ РїРµСЂРµРјРµРЅРЅР°СЏ
        m = re.match(r'^json_С„Р°Р№Р»\s+"([^"]+)"\s*в†’\s*(\w+)$', line)
        if m:
            return LoadJson(path=m.group(1), variable=m.group(2))
        m = re.match(r'^json_С„Р°Р№Р»\s+(\w+)\s*в†’\s*(\w+)$', line)
        if m:
            return LoadJson(path=parse_value(m.group(1)), variable=m.group(2))

        # СЂР°Р·РѕР±СЂР°С‚СЊ_json РёСЃС‚РѕС‡РЅРёРє в†’ РїРµСЂРµРјРµРЅРЅР°СЏ
        m = re.match(r'^СЂР°Р·РѕР±СЂР°С‚СЊ_json\s+(.+?)\s*в†’\s*(\w+)$', line)
        if m:
            return ParseJson(source=parse_value(m.group(1)), variable=m.group(2))

        # СЃРѕС…СЂР°РЅРёС‚СЊ_json "РїСѓС‚СЊ" = РїРµСЂРµРјРµРЅРЅР°СЏ
        m = re.match(r'^СЃРѕС…СЂР°РЅРёС‚СЊ_json\s+"([^"]+)"\s*=\s*(\w+)$', line)
        if m:
            return SaveJson(path=m.group(1), source_var=m.group(2))

        # СѓРґР°Р»РёС‚СЊ_С„Р°Р№Р» "РїСѓС‚СЊ"
        m = re.match(r'^СѓРґР°Р»РёС‚СЊ_С„Р°Р№Р»\s+"([^"]+)"$', line)
        if m:
            return DeleteFile(path=m.group(1))
        m = re.match(r'^СѓРґР°Р»РёС‚СЊ_С„Р°Р№Р»\s+(\w+)$', line)
        if m:
            return DeleteFile(path=parse_value(m.group(1)))

        # СѓРґР°Р»РёС‚СЊ РѕР±СЉРµРєС‚["РєР»СЋС‡"] вЂ” СѓРґР°Р»РµРЅРёРµ РїРѕР»СЏ dict (РїРµСЂРµРґ РѕР±С‰РёРј 'СѓРґР°Р»РёС‚СЊ "РєР»СЋС‡"')
        m = re.match(r'^СѓРґР°Р»РёС‚СЊ\s+(\w+)\["([^"]+)"\]$', line)
        if m:
            return DeleteDictKey(target=m.group(1), key=m.group(2))
        m = re.match(r'^СѓРґР°Р»РёС‚СЊ\s+(\w+)\[(\w+)\]$', line)
        if m:
            return DeleteDictKey(target=m.group(1), key=parse_value(m.group(2)))

        # РѕР±СЉРµРєС‚["РєР»СЋС‡"] = Р·РЅР°С‡РµРЅРёРµ вЂ” РїСЂРёСЃРІР°РёРІР°РЅРёРµ РїРѕР»СЏ dict
        m = re.match(r'^(\w+)\["([^"]+)"\]\s*=\s*(.+)$', line)
        if m:
            return SetDictKey(target=m.group(1), key=m.group(2), value=parse_value(m.group(3)))
        m = re.match(r'^(\w+)\[(\w+)\]\s*=\s*(.+)$', line)
        if m:
            return SetDictKey(target=m.group(1), key=parse_value(m.group(2)),
                              value=parse_value(m.group(3)))

        # в”Ђв”Ђ HTTP СЂР°СЃС€РёСЂРµРЅРёСЏ в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ

        # http_patch url СЃ data в†’ var  /  http_patch url json body в†’ var
        m = re.match(r'^http_patch\s+(.+?)\s+json\s+(.+?)\s*в†’\s*(\w+)$', line)
        if m:
            return HttpPatch(url=parse_value(m.group(1)), data=parse_value(m.group(2)), variable=m.group(3))
        m = re.match(r'^http_patch\s+(.+?)\s+СЃ\s+(.+?)\s*в†’\s*(\w+)$', line)
        if m:
            return HttpPatch(url=parse_value(m.group(1)), data=parse_value(m.group(2)), variable=m.group(3))

        # http_put url СЃ data в†’ var  /  http_put url json body в†’ var
        m = re.match(r'^http_put\s+(.+?)\s+json\s+(.+?)\s*в†’\s*(\w+)$', line)
        if m:
            return HttpPut(url=parse_value(m.group(1)), data=parse_value(m.group(2)), variable=m.group(3))
        m = re.match(r'^http_put\s+(.+?)\s+СЃ\s+(.+?)\s*в†’\s*(\w+)$', line)
        if m:
            return HttpPut(url=parse_value(m.group(1)), data=parse_value(m.group(2)), variable=m.group(3))

        # http_delete url в†’ var
        m = re.match(r'^http_delete\s+(.+?)\s*в†’\s*(\w+)$', line)
        if m:
            return HttpDelete(url=parse_value(m.group(1)), variable=m.group(2))

        # http_Р·Р°РіРѕР»РѕРІРєРё РїРµСЂРµРјРµРЅРЅР°СЏ вЂ” СѓСЃС‚Р°РЅР°РІР»РёРІР°РµС‚ Р·Р°РіРѕР»РѕРІРєРё РґР»СЏ HTTP-РІС‹Р·РѕРІРѕРІ
        m = re.match(r'^http_Р·Р°РіРѕР»РѕРІРєРё\s+(\w+)$', line)
        if m:
            return SetHttpHeaders(variable=m.group(1))

        # в”Ђв”Ђ Р‘Р°Р·Р° РґР°РЅРЅС‹С… СЂР°СЃС€РёСЂРµРЅРёСЏ в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ

        # СѓРґР°Р»РёС‚СЊ "РєР»СЋС‡" вЂ” СѓРґР°Р»РµРЅРёРµ РєР»СЋС‡Р° РёР· Р‘Р” (РїРѕСЃР»Рµ РїСЂРѕРІРµСЂРєРё СѓРґР°Р»РёС‚СЊ РѕР±СЉРµРєС‚["РєР»СЋС‡"])
        m = re.match(r'^СѓРґР°Р»РёС‚СЊ\s+"([^"]+)"$', line)
        if m:
            return DeleteFromDB(key=m.group(1))

        # РІСЃРµ_РєР»СЋС‡Рё в†’ СЃРїРёСЃРѕРє
        m = re.match(r'^РІСЃРµ_РєР»СЋС‡Рё\s*в†’\s*(\w+)$', line)
        if m:
            return GetAllDBKeys(variable=m.group(1))

        # СЃРѕС…СЂР°РЅРёС‚СЊ_РіР»РѕР±Р°Р»СЊРЅРѕ "РєР»СЋС‡" = Р·РЅР°С‡РµРЅРёРµ
        m = re.match(r'^СЃРѕС…СЂР°РЅРёС‚СЊ_РіР»РѕР±Р°Р»СЊРЅРѕ\s+"([^"]+)"\s*=\s*(.+)$', line)
        if m:
            return SaveGlobalDB(key=m.group(1), value=parse_value(m.group(2)))

        # РїРѕР»СѓС‡РёС‚СЊ РѕС‚ USER_ID "РєР»СЋС‡" в†’ РїРµСЂРµРјРµРЅРЅР°СЏ
        m = re.match(r'^РїРѕР»СѓС‡РёС‚СЊ РѕС‚\s+(.+?)\s+"([^"]+)"\s*в†’\s*(\w+)$', line)
        if m:
            return LoadFromUserDB(user_id=parse_value(m.group(1).strip()),
                                  key=m.group(2), variable=m.group(3))

        # в”Ђв”Ђ РЈРїСЂР°РІР»РµРЅРёРµ РїРѕС‚РѕРєРѕРј СЂР°СЃС€РёСЂРµРЅРёСЏ в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ

        # РІРµСЂРЅСѓС‚СЊ Р·РЅР°С‡РµРЅРёРµ
        m = re.match(r'^РІРµСЂРЅСѓС‚СЊ\s+(.+)$', line)
        if m:
            return ReturnValue(value=parse_value(m.group(1)))

        # РёРЅР°С‡Рµ / РїСЂРё СЃС‚Р°СЂС‚Рµ / etc вЂ” РїСЂРѕРїСѓСЃС‚РёРј РЅР° РІРµСЂС…РЅРµРј СѓСЂРѕРІРЅРµ
        return None

    def _parse_commands_block(self) -> list:
        """РџР°СЂСЃРёС‚ Р±Р»РѕРє РєРѕРјР°РЅРґ ботР° РґР»СЏ РјРµРЅСЋ.
        
        РєРѕРјР°РЅРґС‹:
            "/start" - "Р—Р°РїСѓСЃРє"
            "/help" - "РџРѕРјРѕС‰СЊ"
        """
        commands = []
        while self.pos < len(self.lines):
            line = self.peek()
            if line is None:
                break
            
            # РџСЂРѕРІРµСЂСЏРµРј РѕС‚СЃС‚СѓРї - РґРѕР»Р¶РµРЅ Р±С‹С‚СЊ Р±РѕР»СЊС€Рµ Р±Р°Р·РѕРІРѕРіРѕ
            ind = indent_of(line)
            if ind < 4:  # РЅРµ СЃ РѕС‚СЃС‚СѓРїРѕРј - РІС‹С…РѕРґРёРј
                break
            
            stripped = line.strip()
            if not stripped:
                self.consume()
                continue
            
            # РџР°СЂСЃРёРј: "/РєРѕРјР°РЅРґР°" - "РћРїРёСЃР°РЅРёРµ" РёР»Рё /РєРѕРјР°РЅРґР° - РћРїРёСЃР°РЅРёРµ
            m = re.match(r'^[\s]*"([^"]+)"\s*-\s*"([^"]+)"$', stripped)
            if not m:
                m = re.match(r'^[\s]*"([^"]+)"\s*-\s*(.+)$', stripped)
            if m:
                commands.append({"command": m.group(1), "description": m.group(2)})
            self.consume()
        
        return commands
