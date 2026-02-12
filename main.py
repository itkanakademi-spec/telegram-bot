import os
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.getenv("TELEGRAM_TOKEN")
STATE_FILE = "state.json"

groups = {}

# --------------------------
# Dummy HTTP Server (Railway)
# --------------------------
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_server():
    HTTPServer(("0.0.0.0", 1551), DummyHandler).serve_forever()

# --------------------------
# State Persistence
# --------------------------
def save_state():
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(groups, f, ensure_ascii=False)

def load_state():
    global groups
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            groups = json.load(f)
    except:
        groups = {}

# --------------------------
# Helpers
# --------------------------
async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admins = await context.bot.get_chat_administrators(update.effective_chat.id)
    return any(a.user.id == user_id for a in admins)

def ltr(text: str) -> str:
    return "\u200e" + text

def get_group(chat_id):
    chat_id = str(chat_id)
    if chat_id not in groups:
        groups[chat_id] = {
            "participants": {},
            "listeners": [],
            "active": False,
            "message_id": None
        }
    return groups[chat_id]

# --------------------------
# UI Builders
# --------------------------
def build_text(group):
    text = "*🔸🔶🌙⭐️ İTKAN | Kur’an Akademisi 🌙⭐️🔶🔸*\n\n"

    text += "*🔸 Katılımcılar:*\n"
    if group["participants"]:
        for i, (name, done) in enumerate(group["participants"].items(), start=1):
            mark = " ✅" if done else ""
            text += f"{i}. {ltr(name)}{mark}\n"
    else:
        text += "Henüz kimse yok\n"

    text += "\n*🔸 Dinleyiciler:*\n"
    if group["listeners"]:
        for i, name in enumerate(group["listeners"], start=1):
            text += f"{i}. {ltr(name)}\n"
    else:
        text += "Henüz kimse yok\n"

    text += "\n*📖 Kur’an kalplere şifa, hayata nurdur.*\n\n"
    "*Niyet et, adım at, Allah muvaffak eylesin 🤲🏻*\n"
    
    "*🌙⭐️ Ramazan berekettir, rahmettir, mağfirettir. Bu ayı en güzel şekilde değerlendirelim! ⭐️🌙*\n\n" )

    if group["active"]:
        text += "👇 Lütfen aşağıdan durumunu seç"
    else:
        text += "📕 *Ders bitti*"

    return text

def build_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✋🏻 Katılıyorum", callback_data="join"),
            InlineKeyboardButton("🎧 Dinleyici", callback_data="listen"),
        ],
        [
            InlineKeyboardButton("✅ Okudum", callback_data="done"),
        ],
        [
            InlineKeyboardButton("⛔️ İlanı Durdur", callback_data="stop"),
        ]
    ])

# --------------------------
# /start
# --------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.delete()
    except:
        pass

    if not await is_admin(update, context):
        return

    chat_id = str(update.effective_chat.id)
    group = get_group(chat_id)

    # ==========================
    # الحالة A: الجلسة نشطة
    # ==========================
    if group["active"]:

        if group["message_id"]:
            try:
                await context.bot.delete_message(
                    chat_id=chat_id,
                    message_id=group["message_id"]
                )
            except:
                pass

        msg = await context.bot.send_message(
            chat_id=chat_id,
            text=build_text(group),
            reply_markup=build_keyboard(),
            parse_mode="Markdown"
        )

        group["message_id"] = msg.message_id
        save_state()
        return

    # ==========================
    # الحالة B: كانت متوقفة
    # ==========================

    group["participants"] = {}
    group["listeners"] = []
    group["active"] = True

    msg = await context.bot.send_message(
        chat_id=chat_id,
        text=build_text(group),
        reply_markup=build_keyboard(),
        parse_mode="Markdown"
    )

    group["message_id"] = msg.message_id
    save_state()

# --------------------------
# Buttons
# --------------------------
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chat_id = str(query.message.chat.id)
    group = get_group(chat_id)
    name = query.from_user.full_name

    # STOP
    if query.data == "stop":
        if not await is_admin(update, context):
            return

        group["active"] = False
        save_state()

        await query.edit_message_text(
            build_text(group),
            reply_markup=None,
            parse_mode="Markdown"
        )
        return

    if not group["active"]:
        await query.answer("⛔️ Kayıt kapalı")
        return

    if query.data == "join":
        if name in group["participants"]:
            await query.answer("Zaten katılımcısın 🌸")
            return

        if name in group["listeners"]:
            group["listeners"].remove(name)

        group["participants"][name] = False
        await query.answer("🌸 Niyetin çok güzel !!")

    elif query.data == "listen":
        if name in group["participants"]:
            await query.answer("Zaten katılımcısın")
            return

        if name not in group["listeners"]:
            group["listeners"].append(name)
            await query.answer("İnşaAllah istifade edersin 🌷")

    elif query.data == "done":
        if name not in group["participants"]:
            await query.answer("Henüz sıraya girmedin")
            return

        if group["participants"][name]:
            await query.answer("Zaten işaretlendi")
            return

        group["participants"][name] = True
        await query.answer("✅ MaşaAllah, Allah muvaffak eylesin 🤲🏻")

    save_state()

    await query.edit_message_text(
        build_text(group),
        reply_markup=build_keyboard(),
        parse_mode="Markdown"
    )

# --------------------------
# Main
# --------------------------
def main():
    load_state()
    threading.Thread(target=run_server, daemon=True).start()

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))

    app.run_polling()

if __name__ == "__main__":
    main()
