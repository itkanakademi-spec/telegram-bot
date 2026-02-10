import os
import threading
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
            "participants": [],
            "active": False,
            "message_id": None
        }
    return groups[chat_id]

def build_text(group):
    lines = []
    for i, u in enumerate(group["participants"], start=1):
        mark = " ✅" if u["done"] else ""
        lines.append(f"{i}. {u['name']}{mark}")

    text = "*🔸🔶🔸 İTKAN KURAN AKADEMİSİ 🔸🔶🔸*\n\n"
    text += "*✋🏻 Katılımcılar:*\n"
    text += "\n".join(lines) if lines else "Henüz kimse yok"
    text += "\n\n👇 Okuduysan aşağıdan işaretle"
    return text

def build_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Okudum", callback_data="done")],
        [InlineKeyboardButton("⛔️ İlanı Durdur", callback_data="stop")]
    ])

# --------------------------
# Start Command
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

    # Yeni ilan → tamamen sıfır
    group["participants"].clear()
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
    name = query.from_user.full_name

    if query.data == "stop":
        if not await is_admin(update, context):
            return
        group["active"] = False
        await query.edit_message_reply_markup(None)
        return

    if not group["active"]:
        await query.answer("Kayıt kapalı", show_alert=True)
        return

    if query.data == "done":
        user = next((u for u in group["participants"] if u["name"] == name), None)

        if not user:
            group["participants"].append({"name": name, "done": True})
        elif user["done"]:
            await query.answer("Zaten işaretlendi", show_alert=False)
            return
        else:
            user["done"] = True

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
