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

def ltr(text: str) -> str:
    return "\u200e" + text

def format_list(items):
    return "\n".join(
        f"{i}. {ltr(u['name'])}{' ✅' if u.get('done') else ''}"
        for i, u in enumerate(items, start=1)
    )

def get_group(chat_id):
    if chat_id not in groups:
        groups[chat_id] = {
            "participants": [],
            "listeners": [],
            "active": False,
            "message_id": None
        }
    return groups[chat_id]

def build_text(group):
    text = "*🔸🔶🔸 İTKAN | Kur’an Akademisi 🔸🔶🔸*\n\n"
    text += "*✋ Katılımcılar:*\n"
    text += format_list(group["participants"]) if group["participants"] else "Henüz kimse yok"
    text += "\n\n*🎧 Dinleyiciler:*\n"
    text += "\n".join(ltr(name) for name in group["listeners"]) if group["listeners"] else "Yok"
    text += (
        "\n\n*📖 Kur’an kalplere şifa, hayata nurdur.*\n"
        "👇 Durumunu aşağıdan seç"
    )
    return text

def build_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✋ Katılıyorum", callback_data="join"),
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

    if not group["active"]:
        group["participants"].clear()
        group["listeners"].clear()
        group["active"] = True

    if group["message_id"]:
        try:
            await context.bot.delete_message(chat_id, group["message_id"])
        except:
            pass

    msg = await context.bot.send_message(
        chat_id=chat_id,
        text=build_text(group),
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
    user = query.from_user.full_name

    if query.data == "stop":
        if not await is_admin(update, context):
            await query.answer("Sadece yöneticiler", show_alert=True)
            return
        group["active"] = False
        await query.edit_message_reply_markup(None)
        await query.answer("İlan durduruldu", show_alert=True)
        return

    if not group["active"]:
        await query.answer("Kayıt kapalı", show_alert=True)
        return

    if query.data == "join":
        if not any(u["name"] == user for u in group["participants"]):
            group["participants"].append({"name": user, "done": False})
        group["listeners"] = [l for l in group["listeners"] if l != user]

    elif query.data == "listen":
        if user not in group["listeners"]:
            group["listeners"].append(user)
        group["participants"] = [u for u in group["participants"] if u["name"] != user]

    elif query.data == "done":
        participant = next(
            (u for u in group["participants"] if u["name"] == user),
            None
        )

        if participant:
            if participant["done"]:
                await query.answer("Zaten işaretlendi", show_alert=False)
                return
            participant["done"] = True
            await query.answer("Allah kabul etsin 🌸", show_alert=False)

        elif user in group["listeners"]:
            await query.answer("Dinleyicisiniz", show_alert=True)
            return

        else:
            await query.answer("Henüz sıra almadınız", show_alert=True)
            return

    elif query.data == "alert":
        if not await is_admin(update, context):
            await query.answer("Sadece yöneticiler", show_alert=True)
            return
        await query.answer("Ders başladı bildirimi gönderildi", show_alert=False)

    await query.edit_message_text(
        build_text(group),
        reply_markup=build_keyboard(),
        parse_mode="Markdown"
    )

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
