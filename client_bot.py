import os
import json
import random
import time
import threading
import requests
from flask import Flask

app = Flask(__name__)

# ================= НАСТРОЙКИ БОТА =================
CLIENT_NAME = "piar_bot"         # Имя проекта
GROUP_ID = 243637441             # ID твоей группы ВК
VK_TOKEN = "vk1.a.SsRc8RadTRg3g-U1vUzsUJbSJ8XYmC2tI4NzO0LAKAw8RXllZUsn_zPxm8SKei7rApNKmeZBGDW2fqIRk3oHPqxg-jA_KW4rQBRP3sCNZWiddcuOCy3F9-wJP73O9OImizsD6XN5AgYoED6kVshZj7j5yrB_7u7OOVNK6d8FkAoMBU-sGZovulDjTftb9K0ieLcMZLiU0oCvNWHGbjlT0w"

# Твой ID — ты сразу главный Владелец в коде!
MY_OWNER_ID = 897082738
SECOND_ADMIN_ID = 1108641965  # Второй со-админ

@app.route("/")
def index():
    return f"Bot {CLIENT_NAME} is running 24/7!"

DATA_FILE = f"data_{CLIENT_NAME}.json"
VK_API_URL = "https://api.vk.com/method/"
API_VERSION = "5.199"

DEFAULT_PIAR_TEXT = (
    "💎 NEBULA STUDIO — ЭКСКЛЮЗИВНЫЕ ПРОЕКТЫ И ПРЕМИУМ-СЛИВЫ ДЛЯ CRMP MOBILE\n\n"
    "Мы не делаем дёшево и наспех — мы создаём качественный фундамент для серьёзных проектов. 🚀\n\n"
    "👑 Что мы предлагаем:\n"
    "• 📱 Моды Mobile (Black Russia, Матрёшка РП)\n"
    "• 💻 ПК Сборки (Radmir RP 8.4)\n"
    "• 💬 Форумы XenForo под ключ\n"
    "• 🌐 Сайты и лендинги\n\n"
    "🔗 Telegram: https://t.me/NEBULASTUDIO\n"
    "📩 VK: vk.com/nebulastudio0"
)

DEFAULT_PRICE_TEXT = (
    "🛒 ПРАЙС-ЛИСТ И ТОВАРЫ:\n\n"
    "1️⃣ Моды Mobile (Black Russia / Матрёшка РП)\n"
    "2️⃣ ПК Сборки (Radmir RP 8.4)\n"
    "3️⃣ Форумы XenForo под ключ\n"
    "4️⃣ Сайты, лендинги и боты\n\n"
    "⚠️ Работаем строго по 100% предоплате!\n"
    "👇 Нажми «📩 Вызвать администратора», чтобы сделать заказ:"
)

DEFAULT_WELCOME_TEXT = "🌌 Добро пожаловать! Выбери нужный раздел в меню ниже:"
DEFAULT_HELPER_TEXT = "📘 ПРАВИЛА ПОКУПКИ:\n1️⃣ Выбери товар.\n2️⃣ Нажми «Вызвать администратора».\n3️⃣ Оплата строго 100% перед началом работы."

# ================= БАЗА ДАННЫХ =================
def load_data():
    if not os.path.exists(DATA_FILE):
        default_data = {
            "owner": MY_OWNER_ID,
            "admins": [MY_OWNER_ID, SECOND_ADMIN_ID],
            "piar_text": DEFAULT_PIAR_TEXT,
            "price_text": DEFAULT_PRICE_TEXT,
            "welcome_text": DEFAULT_WELCOME_TEXT,
            "helper_text": DEFAULT_HELPER_TEXT,
            "is_active": True,
            "users": [],
            "chats": []
        }
        save_data(default_data)
        return default_data
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        if data.get("owner") != MY_OWNER_ID:
            data["owner"] = MY_OWNER_ID
        if MY_OWNER_ID not in data["admins"]:
            data["admins"].append(MY_OWNER_ID)
        return data

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def parse_user_id(text):
    clean = text.strip().replace("https://", "").replace("http://", "").replace("vk.com/", "").replace("vk.ru/", "").replace("@", "")
    if clean.startswith("id") and clean[2:].isdigit():
        return int(clean[2:])
    if clean.isdigit():
        return int(clean)
    return None

def send_message(peer_id, text, keyboard=None):
    params = {
        "peer_id": peer_id,
        "message": text,
        "random_id": random.randint(1, 2147483647),
        "access_token": VK_TOKEN,
        "v": API_VERSION
    }
    if keyboard:
        params["keyboard"] = json.dumps(keyboard, ensure_ascii=False)
    try:
        res = requests.post(VK_API_URL + "messages.send", data=params, timeout=10).json()
        if "error" in res and res["error"].get("error_code") in [901, 902, 917, 7, 936]:
            return False
    except:
        pass
    return True

def get_admin_keyboard(is_active, is_owner=False):
    status_text = "🔴 Остановить автопиар" if is_active else "🟢 Запустить автопиар"
    buttons = [
        [{"action": {"type": "text", "label": status_text}, "color": "negative" if is_active else "positive"}],
        [
            {"action": {"type": "text", "label": "✏️ Текст автопиара"}, "color": "primary"},
            {"action": {"type": "text", "label": "✏️ Изменить прайс-лист"}, "color": "primary"}
        ],
        [
            {"action": {"type": "text", "label": "✏️ Автоответ в ЛС"}, "color": "primary"},
            {"action": {"type": "text", "label": "✏️ Текст хелпера"}, "color": "primary"}
        ],
        [
            {"action": {"type": "text", "label": "📊 Статистика"}, "color": "secondary"},
            {"action": {"type": "text", "label": "📢 Рассылка в ЛС"}, "color": "secondary"}
        ]
    ]
    if is_owner:
        buttons.append([
            {"action": {"type": "text", "label": "➕ Выдать админа"}, "color": "positive"},
            {"action": {"type": "text", "label": "➖ Снять админа"}, "color": "negative"}
        ])
        buttons.append([
            {"action": {"type": "text", "label": "👑 Передать владельца"}, "color": "negative"},
            {"action": {"type": "text", "label": "👥 Список админов"}, "color": "secondary"}
        ])
    buttons.append([{"action": {"type": "text", "label": "🛒 Меню покупателя"}, "color": "positive"}])
    return {"one_time": False, "buttons": buttons}

def get_user_keyboard(is_admin=False):
    buttons = [
        [{"action": {"type": "text", "label": "🛒 Прайс-лист / Товары"}, "color": "primary"}],
        [{"action": {"type": "text", "label": "❓ Как купить / Правила"}, "color": "secondary"}],
        [{"action": {"type": "text", "label": "📩 Вызвать администратора"}, "color": "negative"}]
    ]
    if is_admin:
        buttons.append([{"action": {"type": "text", "label": "⚙️ Админ-панель"}, "color": "secondary"}])
    return {"one_time": False, "buttons": buttons}

def background_autopyar():
    while True:
        time.sleep(30)
        try:
            db = load_data()
            if not db.get("is_active", True) or not db.get("chats"):
                continue
            active_chats = [cid for cid in db["chats"] if send_message(cid, db["piar_text"]) and not time.sleep(0.25)]
            if len(active_chats) != len(db["chats"]):
                db["chats"] = active_chats
                save_data(db)
        except Exception as e:
            print(f"[{CLIENT_NAME}] Ошибка автопиара: {e}")

def get_long_poll_server():
    res = requests.post(VK_API_URL + "groups.getLongPollServer", data={
        "access_token": VK_TOKEN, "v": API_VERSION, "group_id": GROUP_ID
    }).json()
    return res.get("response")

def main():
    server_data = get_long_poll_server()
    if not server_data:
        print(f"❌ Ошибка Long Poll! Проверь токен и ID группы.")
        return
    server, key, ts = server_data["server"], server_data["key"], server_data["ts"]
    admin_states = {}

    while True:
        try:
            response = requests.get(f"{server}?act=a_check&key={key}&ts={ts}&wait=25", timeout=30).json()
            if "failed" in response:
                server_data = get_long_poll_server()
                if server_data:
                    server, key, ts = server_data["server"], server_data["key"], server_data["ts"]
                continue
            ts = response.get("updates_ts", response.get("ts", ts))

            for event in response.get("updates", []):
                if event.get("type") == "chat_invite_user":
                    db = load_data()
                    pid = event["object"].get("peer_id")
                    if pid and pid not in db["chats"]:
                        db["chats"].append(pid)
                        save_data(db)
                    continue

                if event.get("type") == "message_new":
                    msg = event["object"]["message"]
                    from_id, peer_id = msg["from_id"], msg["peer_id"]
                    text = msg.get("text", "").strip()
                    text_lower = text.lower()
                    if from_id < 0:
                        continue

                    db = load_data()
                    if peer_id > 2000000000 or peer_id != from_id:
                        if peer_id not in db["chats"]:
                            db["chats"].append(peer_id)
                            save_data(db)
                        continue

                    if peer_id not in db["users"]:
                        db["users"].append(peer_id)
                        save_data(db)

                    is_owner = (from_id == db["owner"])
                    is_admin = is_owner or (from_id in db["admins"])

                    if is_admin and from_id in admin_states:
                        state = admin_states.pop(from_id)
                        if text_lower == "отмена":
                            send_message(peer_id, "❌ Отменено.", get_admin_keyboard(db["is_active"], is_owner))
                            continue
                        if state == "edit_piar":
                            db["piar_text"] = text
                            save_data(db)
                            send_message(peer_id, "✅ Текст пиара успешно обновлён!", get_admin_keyboard(db["is_active"], is_owner))
                        elif state == "edit_price":
                            db["price_text"] = text
                            save_data(db)
                            send_message(peer_id, "✅ Прайс-лист успешно обновлён!", get_admin_keyboard(db["is_active"], is_owner))
                        elif state == "edit_welcome":
                            db["welcome_text"] = text
                            save_data(db)
                            send_message(peer_id, "✅ Автоответ в ЛС обновлён!", get_admin_keyboard(db["is_active"], is_owner))
                        elif state == "edit_helper":
                            db["helper_text"] = text
                            save_data(db)
                            send_message(peer_id, "✅ Правила / хелпер обновлены!", get_admin_keyboard(db["is_active"], is_owner))
                        elif state == "broadcast":
                            cnt = sum(1 for uid in db["users"] if send_message(uid, text))
                            send_message(peer_id, f"✅ Рассылка отправлена {cnt} пользователям.", get_admin_keyboard(db["is_active"], is_owner))
                        elif state == "add_admin" and is_owner:
                            tid = parse_user_id(text)
                            if tid and tid not in db["admins"]:
                                db["admins"].append(tid)
                                save_data(db)
                                send_message(peer_id, f"✅ Администратор vk.com/id{tid} успешно добавлен!", get_admin_keyboard(db["is_active"], is_owner))
                            else:
                                send_message(peer_id, "❌ Неверный ID или пользователь уже админ.", get_admin_keyboard(db["is_active"], is_owner))
                        elif state == "remove_admin" and is_owner:
                            tid = parse_user_id(text)
                            if tid and tid in db["admins"] and tid != db["owner"]:
                                db["admins"].remove(tid)
                                save_data(db)
                                send_message(peer_id, f"✅ Администратор vk.com/id{tid} снят.", get_admin_keyboard(db["is_active"], is_owner))
                            else:
                                send_message(peer_id, "❌ Нельзя снять владельца или неверный ID.", get_admin_keyboard(db["is_active"], is_owner))
                        elif state == "transfer_owner" and is_owner:
                            tid = parse_user_id(text)
                            if tid:
                                db["owner"] = tid
                                if tid not in db["admins"]:
                                    db["admins"].append(tid)
                                save_data(db)
                                new_is_owner = (from_id == tid)
                                send_message(peer_id, f"👑 Права владельца переданы пользователю vk.com/id{tid}!", get_admin_keyboard(db["is_active"], new_is_owner))
                            else:
                                send_message(peer_id, "❌ Неверный ID.", get_admin_keyboard(db["is_active"], is_owner))
                        continue

                    if is_admin:
                        if text == "⚙️ Админ-панель" or text_lower in ["админ", "меню"]:
                            send_message(peer_id, f"⚙️ АДМИН-ПАНЕЛЬ\n\n💬 Чатов с пиаром: {len(db['chats'])}\n👥 Юзеров в ЛС: {len(db['users'])}\n⚡ Статус пиара: {'🟢 Вкл' if db['is_active'] else '🔴 Выкл'}", get_admin_keyboard(db["is_active"], is_owner))
                            continue
                        elif text == "🔴 Остановить автопиар":
                            db["is_active"] = False
                            save_data(db)
                            send_message(peer_id, "🔴 Автопиар остановлен.", get_admin_keyboard(False, is_owner))
                            continue
                        elif text == "🟢 Запустить автопиар":
                            db["is_active"] = True
                            save_data(db)
                            send_message(peer_id, "🟢 Запущен автопиар!", get_admin_keyboard(True, is_owner))
                            continue
                        elif text == "📊 Статистика":
                            send_message(peer_id, f"📊 Статистика:\n• Владелец: vk.com/id{db['owner']}\n• Чатов: {len(db['chats'])}\n• Юзеров в ЛС: {len(db['users'])}", get_admin_keyboard(db["is_active"], is_owner))
                            continue
                        elif text == "✏️ Текст автопиара":
                            admin_states[from_id] = "edit_piar"
                            send_message(peer_id, "✍️ Отправь новый текст автопиара для чатов (или 'Отмена'):")
                            continue
                        elif text == "✏️ Изменить прайс-лист":
                            admin_states[from_id] = "edit_price"
                            send_message(peer_id, "✍️ Отправь новый текст прайс-листа для ЛС (или 'Отмена'):")
                            continue
                        elif text == "✏️ Автоответ в ЛС":
                            admin_states[from_id] = "edit_welcome"
                            send_message(peer_id, "✍️ Отправь новый текст приветствия в ЛС (или 'Отмена'):")
                            continue
                        elif text == "✏️ Текст хелпера":
                            admin_states[from_id] = "edit_helper"
                            send_message(peer_id, "✍️ Отправь новый текст правил покупки / хелпера (или 'Отмена'):")
                            continue
                        elif text == "📢 Рассылка в ЛС":
                            admin_states[from_id] = "broadcast"
                            send_message(peer_id, "📣 Напиши текст рассылки для всех в ЛС (или 'Отмена'):")
                            continue
                        elif text == "🛒 Меню покупателя":
                            send_message(peer_id, db["welcome_text"], get_user_keyboard(True))
                            continue
                        elif is_owner:
                            if text == "➕ Выдать админа":
                                admin_states[from_id] = "add_admin"
                                send_message(peer_id, "👤 Отправь ID или ссылку нового администратора (или 'Отмена'):")
                                continue
                            elif text == "➖ Снять админа":
                                admin_states[from_id] = "remove_admin"
                                send_message(peer_id, "👤 Отправь ID или ссылку админа для снятия (или 'Отмена'):")
                                continue
                            elif text == "👑 Передать владельца":
                                admin_states[from_id] = "transfer_owner"
                                send_message(peer_id, "👑 ВНИМАНИЕ! Отправь ID или ссылку нового ВЛАДЕЛЬЦА (или 'Отмена'):")
                                continue
                            elif text == "👥 Список админов":
                                lst = "\n".join([f"• vk.com/id{a}" for a in db["admins"]])
                                send_message(peer_id, f"👑 Владелец: vk.com/id{db['owner']}\n\n🛡 Администраторы:\n{lst}", get_admin_keyboard(db["is_active"], is_owner))
                                continue

                    if text == "🛒 Прайс-лист / Товары":
                        send_message(peer_id, db["price_text"], get_user_keyboard(is_admin))
                    elif text == "❓ Как купить / Правила":
                        send_message(peer_id, db["helper_text"], get_user_keyboard(is_admin))
                    elif text == "📩 Вызвать администратора":
                        send_message(peer_id, "📩 Запрос отправлен администраторам! Ожидайте ответа.\n⚠️ Работаем строго по 100% предоплате.", get_user_keyboard(is_admin))
                        for aid in db["admins"]:
                            send_message(aid, f"🚨 ВЫЗОВ АДМИНА!\nПокупатель: vk.com/id{peer_id}")
                    else:
                        send_message(peer_id, db["welcome_text"], get_user_keyboard(is_admin))
        except Exception as e:
            time.sleep(3)

if __name__ == "__main__":
    threading.Thread(target=background_autopyar, daemon=True).start()
    threading.Thread(target=main, daemon=True).start()

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
