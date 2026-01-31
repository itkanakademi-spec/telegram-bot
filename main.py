import os
import threading
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.getenv("TELEGRAM_TOKEN")

groups = {}

# --------------------------
# Dummy HTTP Server for Railway
# --------------------------
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")

def run_server():
    port = 1551  # الرقم الذي اخترته
    server = HTTPServer(("0.0.0.0", port), DummyHandler)
    print(f"Dummy HTTP server running on port {port}")
    server.serve_forever()

# --------------------------
# Telegram Bot Functions
# --------------------------
async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user:
        user_id = update.effective_user.id
        admins = await context.bot.get_chat_administrators(update.effective_chat.id)
        return any(admin.user and admin.user.id == user_id for admin in admins)
    if update.message and update.message.sender_chat:
        if update.message.sender_chat.id == update.effective_chat.id:
            return True
    return False

def ltr(text: str) -> str:
    return "\u200e" + text

def format_list(items):
    return "\n".join(f"{i}. {ltr(name)}" for i, name in enumerate(items, start=1))

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
    text += "*🔸 Katılımcılar:*\n"
    text += format_list(group["participants"]) if group["participants"] else "Henüz kimse yok"
    text += "\n\n*🔸 Dinleyiciler:*\n"
    text += format_list(group["listeners"]) if group["listeners"] else "Henüz kimse yok"
    text += (
        "\n\n*📖 Kur’an kalplere şifa, hayata nurdur.*\n"
        "Niyet et, adım at, Allah kolaylaştırsın 🤲🏻🧡\n\n"
        "👇 Lütfen aşağıdan durumunu seç"
    )
    return text

def build_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Katılıyorum", callback_data="join"),
            InlineKeyboardButton("🎧 Dinleyici", callback_data="listen"),
        ],
        [
            InlineKeyboardButton("❌ Kaydı İptal Et", callback_data="cancel"),
        ],
        [
            InlineKeyboardButton("⛔️ İlanı Durdur", callback_data="stop"),
            InlineKeyboardButton("🔔 Ders Başladı", callback_data="alert"),
        ]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.delete()
    except:
        pass

    if not await is_admin(update, context):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ Bu komutu sadece yöneticiler kullanabilir."
        )
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

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.message.chat.id
    group = get_group(chat_id)

    user = query.from_user.full_name if query.from_user else "Unknown"

    if query.data == "stop":
        if not await is_admin(update, context):
            await query.answer("❌ Sadece yöneticiler", show_alert=True)
            return
        group["active"] = False
        group["message_id"] = None
        await query.edit_message_reply_markup(None)
        await query.answer("✅ İlan durduruldu", show_alert=True)
        return

    if not group["active"]:
        await query.answer("⛔️ Kayıt kapalı", show_alert=True)
        return

    if query.data == "join":
        if user not in group["participants"]:
            group["participants"].append(user)
        if user in group["listeners"]:
            group["listeners"].remove(user)
    elif query.data == "listen":
        if user not in group["listeners"]:
            group["listeners"].append(user)
        if user in group["participants"]:
            group["participants"].remove(user)
    elif query.data == "cancel":
        if user in group["participants"]:
            group["participants"].remove(user)
        if user in group["listeners"]:
            group["listeners"].remove(user)
    elif query.data == "alert":
        if not await is_admin(update, context):
            await query.answer("❌ Sadece yöneticiler", show_alert=True)
            return
        if group["participants"]:
            mentions = ", ".join(f"[{name}](tg://user?id={query.from_user.id})" for name in group["participants"])
            alert_msg = f"🔔 Ders Başladı! {mentions}"
            sent = await context.bot.send_message(chat_id=chat_id, text=alert_msg, parse_mode="Markdown")
            # حذف التاغ بعد 5 دقائق
            async def remove_alert():
                await asyncio.sleep(300)  # 5 دقائق
                try:
                    await sent.delete()
                except:
                    pass
            asyncio.create_task(remove_alert())
        await query.answer("🔔 الدرس بدأ وتم إرسال التنبيه", show_alert=True)

    await query.edit_message_text(
        build_text(group),
        reply_markup=build_keyboard(),
        parse_mode="Markdown"
    )

# --------------------------
# Main Function
# --------------------------
def main():
    threading.Thread(target=run_server, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.run_polling()

if __name__ == "__main__":
    main()
