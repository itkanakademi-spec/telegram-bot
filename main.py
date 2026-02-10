import os
import threading
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.getenv("TELEGRAM_TOKEN")

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
# Helpers
# --------------------------
async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admins = await context.bot.get_chat_administrators(update.effective_chat.id)
    return any(a.user.id == user_id for a in admins)

def get_group(chat_id):
    if chat_id not in groups:
        groups[chat_id] = {
            "participants": {},  # name: done(bool)
            "listeners": set(),
            "active": False,
            "message_id": None
        }
    return groups[chat_id]

def build_text(group):
    text = "*🔸🔶🔸 İTKAN | Kur’an Akademisi 🔸🔶🔸*\n\n"

    text += "*🔸 Katılımcılar:*\n"
    if group["participants"]:
        for i, (name, done) in enumerate(group["participants"].items(), start=1):
            mark = " ✅" if done else ""
            text += f"{i}. {name}{mark}\n"
    else:
        text += "Henüz kimse yok\n"

    text += "\n*🔸 Dinleyiciler:*\n"
    if group["listeners"]:
        for i, name in enumerate(group["listeners"], start=1):
            text += f"{i}. {name}\n"
    else:
        text += "Henüz kimse yok\n"

    text += (
        "\n*📖 Kur’an kalplere şifa, hayata nurdur.*\n"
        "*Niyet et, adım at, Allah muvaffak eylesin 🤲🏻*\n\n"
        "👇 Lütfen aşağıdan durumunu seç"
    )
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
            InlineKeyboardButton("🔔 Ders Başladı", callback_data="alert"),
        ]
    ])

# --------------------------
# Start
# --------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.delete()
    except:
        pass

    if not await is_admin(update, context):
        return

    chat_id = update.effective_chat.id
    group = get_group(chat_id)

    group["participants"].clear()
    group["listeners"].clear()
    group["active"] = True

    if group["message_id"]:
        try:
            await context.bot.delete_message(chat_id, group["message_id"])
        except:
            pass

    msg = await context.bot.send_message(
        chat_id,
        build_text(group),
        reply_markup=build_keyboard(),
        parse_mode="Markdown"
    )

    group["message_id"] = msg.message_id

# --------------------------
# Buttons
# --------------------------
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.message.chat.id
    group = get_group(chat_id)
    name = query.from_user.full_name

    if query.data == "stop":
        if not await is_admin(update, context):
            await query.answer("❌ Sadece yöneticiler")
            return
        group["active"] = False
        await query.edit_message_reply_markup(None)
        return

    if not group["active"]:
        await query.answer("⛔️ Kayıt kapalı")
        return

    # Katılıyorum
    if query.data == "join":
        if name in group["participants"]:
            await query.answer("Zaten katılımcısın")
            return
        group["listeners"].discard(name)
        group["participants"][name] = False
        await query.answer("🌸 Niyetin çok güzel !!")

    # Dinleyici
    elif query.data == "listen":
        if name in group["participants"] and group["participants"][name]:
            await query.answer("Okuduktan sonra değiştirilemez")
            return
        group["participants"].pop(name, None)
        group["listeners"].add(name)
        await query.answer("🌷 İnşaAllah istifade edersin")

    # Okudum
    elif query.data == "done":
        if name not in group["participants"]:
            await query.answer("Önce katılmalısın")
            return
        if group["participants"][name]:
            await query.answer("Zaten işaretlendi")
            return
        group["participants"][name] = True
        await query.answer("✅ MaşaAllah , Allah muvaffak eylesin 🤲🏻")

    # Ders başladı
    elif query.data == "alert":
        if not await is_admin(update, context):
            await query.answer("❌ Sadece yöneticiler")
            return
        if group["participants"]:
            mentions = " ".join(group["participants"].keys())
            msg = await context.bot.send_message(
                chat_id,
                f"🔔 Ders Başladı!\n{mentions}"
            )
            asyncio.create_task(auto_delete(msg))

    await query.edit_message_text(
        build_text(group),
        reply_markup=build_keyboard(),
        parse_mode="Markdown"
    )

async def auto_delete(msg):
    await asyncio.sleep(300)
    try:
        await msg.delete()
    except:
        pass

# --------------------------
# Main
# --------------------------
def main():
    threading.Thread(target=run_server, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.run_polling()

if __name__ == "__main__":
    main()
