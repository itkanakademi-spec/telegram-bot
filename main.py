def build_text(group):
    text = "*🔸🔶🔸 İTKAN | Kur’an Akademisi 🔸🔶🔸*\n\n"

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
        "*Niyet et, adım at, Allah muvaffak eylesin 🤲🏻*\n\n"
    )

    if group["active"]:
        text += "👇 Lütfen aşağıdan durumunu seç"
    else:
        text += "📕 *Ders bitti*"

    return text
