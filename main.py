import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.getenv("TELEGRAM_TOKEN")

# تخزين البيانات لكل مجموعة
groups = {}


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
    return "\n".join(
        f"**{i}.** {ltr(name)}"
        for i, name in enumerate(items, start=1)
    )


def get_group(chat_id):
    if chat_id not in groups:
        groups[chat_id] = {
            "participants": [],
            "listeners": [],
            "active": False
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
            InlineKeyboardButton("⛔ İlanı Durdur", callback_data="stop"),
        ]
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text(
            "❌ Bu komutu sadece yöneticiler kullanabilir."
        )
        return

    chat_id = update.effective_chat.id
    group = get_group(chat_id)

    group["participants"].clear()
    group["listeners"].clear()
    group["active"] = True

    await context.bot.send_message(
        chat_id=chat_id,
        text=build_text(group),
        reply_markup=build_keyboard(),
        parse_mode="Markdown"
    )


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
        await query.edit_message_reply_markup(None)
        await query.answer("✅ İlan durduruldu", show_alert=True)
        return

    if not group["active"]:
        await query.answer("⛔ Kayıt kapalı", show_alert=True)
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

    await query.edit_message_text(
        build_text(group),
        reply_markup=build_keyboard(),
        parse_mode="Markdown"
    )


def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.run_polling()


if __name__ == "__main__":
    main()
