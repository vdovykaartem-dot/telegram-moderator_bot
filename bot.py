import os
import re
import logging
from telegram import Update, ChatPermissions
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    filters,
)

# ===== НАЛАШТУВАННЯ =====
BOT_TOKEN = os.getenv("BOT_TOKEN")

BAD_WORDS = [
    r"(?i)лох",
    r"(?i)дурень",
]

AD_WORDS = [
    r"http",
    r"www",
    r"@",
]

# ===== ЛОГИ =====
logging.basicConfig(level=logging.INFO)

# ===== ПЕРЕВІРКА ПРАВ =====
async def is_admin_with_rights(bot, chat_id, user_id):
    member = await bot.get_chat_member(chat_id, user_id)
    if member.status not in ("administrator", "creator"):
        return False
    return member.can_change_info or member.status == "creator"


# ===== /start =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Модератор-бот работает")


# ===== МОДЕРАЦІЯ =====
async def moderate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.text:
        return

    chat = message.chat
    user = message.from_user
    text = message.text

    # перевіряємо що БОТ має права
    if not await is_admin_with_rights(context.bot, chat.id, context.bot.id):
        return

    # перевіряємо порушення
    violated = False
    for pattern in BAD_WORDS + AD_WORDS:
        if re.search(pattern, text):
            violated = True
            break

    if not violated:
        return

    # знайти адмінів з потрібним правом
    admins = await chat.get_administrators()
    for admin in admins:
        if admin.user.is_bot:
            continue

        if not await is_admin_with_rights(context.bot, chat.id, admin.user.id):
            continue

        link = f"https://t.me/{user.username}" if user.username else f"tg://user?id={user.id}"

        await context.bot.send_message(
            chat_id=admin.user.id,
            text=(
                "🚨 Нарушение\n\n"
                f"👤 Пользователь: {user.full_name}\n"
                f"🔗 Профиль: {link}\n\n"
                f"💬 Сообщение:\n{text}"
            ),
        )


# ===== /mute =====
async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    if not await is_admin_with_rights(context.bot, chat.id, user.id):
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("Отвечай командой на сообщение")
        return

    target = update.message.reply_to_message.from_user

    await context.bot.restrict_chat_member(
        chat.id,
        target.id,
        ChatPermissions(can_send_messages=False),
    )

    await update.message.reply_text(f"🔇 {target.full_name} Замучен")


# ===== /unmute =====
async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    if not await is_admin_with_rights(context.bot, chat.id, user.id):
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("Отвечай командой на сообщение")
        return

    target = update.message.reply_to_message.from_user

    await context.bot.restrict_chat_member(
        chat.id,
        target.id,
        ChatPermissions(can_send_messages=True),
    )

    await update.message.reply_text(f"🔊 {target.full_name} Размучен")


# ===== MAIN =====
def main():
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN не задан")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("mute", mute))
    app.add_handler(CommandHandler("unmute", unmute))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, moderate))

    print("🤖 Бот запущен")
    app.run_polling()


if __name__ == "__main__":
    main()
    # deploy
