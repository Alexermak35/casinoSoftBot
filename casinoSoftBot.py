import json
import time
import logging
from pathlib import Path
from telegram import (
    Update, InlineKeyboardButton,
    InlineKeyboardMarkup, ReplyKeyboardRemove
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, ConversationHandler, filters
)

# ====== НАСТРОЙКИ ======
TOKEN = "8385917871:AAETCv5iNDhLRle2RusknPd4ebnc_KpTfzE"  # вставь свой
REG_LINK = "https://1whecs.life/v3/lucky-jet-updated?p=yahu"
CHANNEL_LINK = "https://t.me/AIJetAnalyzer_bot"
DB_PATH = Path(__file__).parent / "users_db.json"
WAIT_ID = 1
# =======================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Если файла базы нет — создаём пустой
if not DB_PATH.exists():
    DB_PATH.write_text("{}", encoding="utf-8")

def load_db():
    try:
        return json.loads(DB_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}

def save_db(db):
    try:
        DB_PATH.write_text(json.dumps(db, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        logger.error(f"Ошибка сохранения базы: {e}")

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = (
        f"Привет, {user.first_name}! 🚀\n\n"
        "⚠️ Бот работает только если вы зарегистрируетесь по нашей партнёрской ссылке.\n"
        "Регистрируйся прямо сейчас и получи бесплатно софт для абуза казино!\n\n"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔗 Регистрация", url=REG_LINK)],
        [InlineKeyboardButton("✅ Я зарегистрировался", callback_data="registered")]
    ])
    await update.message.reply_text(text, reply_markup=kb)

# Нажал «Я зарегистрировался»
async def registered_pressed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        "Отлично! Напиши сюда свой ID, "
        "который появился у тебя после регистрации на сайте.",
        reply_markup=ReplyKeyboardRemove()
    )
    return WAIT_ID

# Приём ID
async def receive_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    entered_id = update.message.text.strip()

    # Проверка: только цифры и длина от 7 до 10
    if not (7 <= len(entered_id) <= 10 and entered_id.isdigit()):
        await update.message.reply_text("❌ ID неправильный. Попробуй снова.")
        return WAIT_ID

    db = load_db()
    db[str(user.id)] = {
        "tg_username": user.username,
        "first_name": user.first_name,
        "partner_id": entered_id,
        "ts": int(time.time())
    }
    save_db(db)

    await update.message.reply_text(
        "✅ ID получен и подтверждён!\n\n"
        f"Ссылка на наш закрытый канал с софтом:\n{CHANNEL_LINK}"
    )
    return ConversationHandler.END

# /check — если юзер потерял ссылку
async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_db()
    if str(update.effective_user.id) in db:
        await update.message.reply_text(f"Ваш доступ: {CHANNEL_LINK}")
    else:
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 Регистрация", url=REG_LINK)],
            [InlineKeyboardButton("✅ Я зарегистрировался", callback_data="registered")]
        ])
        await update.message.reply_text(
            "Вы ещё не прислали ID. Зарегистрируйтесь по ссылке и вернитесь сюда.",
            reply_markup=kb
        )

# /cancel — выход из диалога
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Окей, отмена. Нажми /start, чтобы начать заново.")
    return ConversationHandler.END

def main():
    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CallbackQueryHandler(registered_pressed, pattern="^registered$"),
        ],
        states={
            WAIT_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_id)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )

    app.add_handler(conv)
    app.add_handler(CommandHandler("check", check))

    logger.info("Bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
