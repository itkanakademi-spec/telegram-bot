import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# جلب التوكن من متغيرات Railway
TOKEN = os.getenv("BOT_TOKEN")

# بيانات مؤقتة للمجموعة
group_data = {
    "participants": {},
    "listeners": [],
    "active": True
}


# دالة لضبط اتجاه النص (يمكن تعديلها لاحقاً)
def ltr(text):
    return text


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

    text += (
        "\n*📖 Kur’an kalplere şifa, hayata nurdur.*\n"
        "*Niyet et, adım at, Allah muvaffak eylesin 🤲🏻*\n"
        "*🌙⭐️ Ramazan berekettir, rahmettir, mağfirettir. Bu ayı en güzel şekilde değerlendirelim! ⭐️🌙*\n\n"
    )

    if group["active"]:
        text += "👇 Lütfen aşağıdan durumunu seç"
    else:
        text += "📕 *Ders bitti*"

    return text


# أمر /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Bot çalışıyor ✅\n\n/start yazarak metni görüntüleyebilirsin.",
        parse_mode="Markdown"
    )


# أمر /show لعرض النص
async def show(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = build_text(group_data)
    await update.message.reply_text(text, parse_mode="Markdown")


def main():
    if not TOKEN:
        print("BOT_TOKEN not found!")
        return

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("show", show))

    print("Bot started successfully...")
    app.run_polling()


if __name__ == "__main__":
    main()
