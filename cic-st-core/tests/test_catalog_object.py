from cicada.adapters.mock_telegram import MockTelegramAdapter
from cicada.executor import Executor
from cicada.parser import Parser


def callback(data: str, chat_id: int = 1):
    return {
        "callback_query": {
            "id": "cb1",
            "from": {"id": chat_id, "first_name": "Tester"},
            "message": {"message_id": 2, "chat": {"id": chat_id, "type": "private"}},
            "data": data,
        }
    }


def test_catalog_object_inline_from_array():
    src = '''# Cicada3301
бот "TOKEN"
глобально catalog = {
    "Пицца": [{"id": 1, "name": "Маргарита", "price": 250}],
    "Суши": [{"id": 3, "name": "Филадельфия", "price": 450}]
}
при старте:
    ответ "🏠"
    кнопки "📦 Каталог"
при нажатии "📦 Каталог":
    категории = ключи(catalog)
    ответ "Выберите:"
    inline из массива категории callback "cat:{item}" назад "⬅️" → "home" колонки 2
    стоп
при callback начинается_с "cat:":
    category = срез(callback, 4)
    товары = catalog[category]
    ответ "📦 {category}"
    inline из массива товары
        текст "{item.name} - {item.price}₽"
        callback "product:{item.id}"
        колонки 1
    стоп
'''
    program = Parser(src).parse()
    assert "Пицца" in program.globals["catalog"]
    tg = MockTelegramAdapter()
    ex = Executor(program, tg)

    ex.handle(callback("📦 Каталог"))
    cat_kb = [e for e in tg.outbound if e["type"] == "inline_keyboard"][-1]["keyboard"]
    assert cat_kb[0][0]["callback_data"] == "cat:Пицца"

    ex.handle(callback("cat:Пицца"))
    prod_kb = [e for e in tg.outbound if e["type"] == "inline_keyboard"][-1]["keyboard"]
    assert prod_kb[0][0]["text"] == "Маргарита - 250₽"
    assert prod_kb[0][0]["callback_data"] == "product:1"
