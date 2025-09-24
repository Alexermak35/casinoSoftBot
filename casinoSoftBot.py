import json
import time
import random
import logging
from pathlib import Path
from telegram import (
    Update, InlineKeyboardButton,
    InlineKeyboardMarkup, ReplyKeyboardRemove, BotCommand
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, ConversationHandler, filters
)

# ====== CONFIG ======
TOKEN = "8486417293:AAHtCmgZ33kqDf3Pr1RCxgyqlnUKMKa5rMk"
REG_LINK = "https://1whecs.life/v3/lucky-jet-updated?p=yahu"
CHANNEL_LINK = "https://t.me/AIJetAnalyzer_bot"
DB_PATH = Path(__file__).parent / "users_db.json"

WAIT_ID, WAIT_AMOUNT = range(2)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if not DB_PATH.exists():
    DB_PATH.write_text("{}", encoding="utf-8")

# ====== DB ======
def load_db():
    try:
        return json.loads(DB_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}

def save_db(db):
    try:
        DB_PATH.write_text(json.dumps(db, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        logger.error(f"DB save error: {e}")

# ---- START ----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db = load_db()

    if str(user.id) not in db:
        text = (
            f"Привет, {user.first_name}! 🚀\n\n"
            "⚠️ Бот работает только если вы зарегистрируетесь по нашей партнёрской ссылке.\n"
            "Регистрируйся прямо сейчас и получи доступ!\n\n"
        )
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 Регистрация", url=REG_LINK)],
            [InlineKeyboardButton("✅ Я зарегистрировался", callback_data="registered")]
        ])
        await update.message.reply_text(text, reply_markup=kb)
        # 👇 Keep the conversation open — wait for button press
        return WAIT_ID
    else:
        await update.message.reply_text("✅ Ты уже зарегистрирован. Используй меню ниже.")
        return ConversationHandler.END


# ---- REGISTERED BUTTON ----
async def registered_pressed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.message.reply_text(
        "Отлично! Напиши сюда свой ID, "
        "который появился у тебя после регистрации на сайте.",
        reply_markup=ReplyKeyboardRemove()
    )
    return WAIT_ID


# ---- RECEIVE ID ----
async def receive_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    entered_id = (update.message.text or "").strip()

    if not (7 <= len(entered_id) <= 10 and entered_id.isdigit()):
        await update.message.reply_text("❌ ID неправильный. Попробуй снова.")
        return WAIT_ID

    db = load_db()
    db[str(user.id)] = {
        "tg_username": user.username,
        "first_name": user.first_name,
        "partner_id": entered_id,
        "currency": "UAH",
        "signals": [],
        "ts": int(time.time())
    }
    save_db(db)

    await update.message.reply_text(
        "✅ ID получен и подтверждён!\n\n"
        "Теперь можешь использовать команды: /signal, /history, /profile, /instruction"
    )
    return ConversationHandler.END

# ====== SIGNAL SYSTEM ======
async def signal_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_db()
    if str(update.effective_user.id) not in db:
        await update.message.reply_text("⛔ Сначала зарегистрируйся через /start")
        return ConversationHandler.END

    keyboard = [
        [InlineKeyboardButton("🎯 10₴", callback_data="amt:10"),
         InlineKeyboardButton("🎯 50₴", callback_data="amt:50")],
        [InlineKeyboardButton("🎯 100₴", callback_data="amt:100"),
         InlineKeyboardButton("✍ Ввести сумму", callback_data="amt:custom")]
    ]
    await update.message.reply_text("Выбери сумму ставки:", reply_markup=InlineKeyboardMarkup(keyboard))


async def amount_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_db()
    if str(update.effective_user.id) not in db:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text("⛔ Сначала зарегистрируйся через /start")
        return ConversationHandler.END

    q = update.callback_query
    await q.answer()

    if q.data == "amt:custom":
        await q.message.reply_text("Введи сумму в гривнах:")
        return WAIT_AMOUNT

    amount = int(q.data.split(":")[1])
    await send_signal(update, context, amount)
    return ConversationHandler.END


async def amount_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_db()
    if str(update.effective_user.id) not in db:
        await update.message.reply_text("⛔ Сначала зарегистрируйся через /start")
        return ConversationHandler.END

    text = (update.message.text or "").strip()
    if not text.isdigit():
        await update.message.reply_text("❌ Введи сумму числом.")
        return WAIT_AMOUNT

    amount = int(text)
    await send_signal(update, context, amount)
    return ConversationHandler.END


async def send_signal(update: Update, context: ContextTypes.DEFAULT_TYPE, amount: int):
    user = update.effective_user
    db = load_db()
    user_data = db.get(str(user.id))

    if not user_data:
        # fallback protection
        if update.callback_query:
            await update.callback_query.message.reply_text("⛔ Сначала зарегистрируйся через /start")
        else:
            await update.message.reply_text("⛔ Сначала зарегистрируйся через /start")
        return

    rnd = random.random()
    if rnd < 0.75:
        coef = round(random.uniform(1.2, 2.9), 2)
    elif rnd < 0.95:
        coef = round(random.uniform(3.0, 4.5), 2)
    else:
        coef = round(random.uniform(4.6, 7.0), 2)

    signal = f"🎲 Ставка: {amount}₴ | Коэффициент: {coef}x"
    user_data["signals"].append(signal)
    user_data["signals"] = user_data["signals"][-10:]
    save_db(db)

    keyboard = [[InlineKeyboardButton("✍ Изменить сумму", callback_data="change_amount")]]
    if update.callback_query:
        await update.callback_query.message.reply_text(signal, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(signal, reply_markup=InlineKeyboardMarkup(keyboard))


async def change_amount_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.message.reply_text("Введи сумму в гривнах:")
    return WAIT_AMOUNT


# ====== OTHER COMMANDS ======
async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_db()
    signals = db.get(str(update.effective_user.id), {}).get("signals", [])
    if not signals:
        await update.message.reply_text("История пуста.")
    else:
        await update.message.reply_text("📜 История:\n" + "\n".join(signals))

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_db()
    u = db.get(str(update.effective_user.id))
    if not u:
        await update.message.reply_text("❌ Сначала зарегистрируйся через /start")
        return
    msg = f"👤 Твой ID: {u['partner_id']}\n💱 Валюта: гривны (₴)"
    await update.message.reply_text(msg)

async def instruction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "📖 Инструкция:\n\n"
        "1️⃣ Зарегистрируйся через нашу ссылку.\n"
        "2️⃣ Введи свой ID.\n"
        "3️⃣ Все ставки указываются в гривнах (₴).\n\n"
        "Команды:\n"
        "/signal — получить сигнал\n"
        "/history — история\n"
        "/profile — мой профиль\n"
        "/instruction — инструкция\n"

    )
    await update.message.reply_text(msg)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Works both for messages and callback queries
    if update.message:
        await update.message.reply_text(
            "🚫 Действие отменено. Нажми /start, чтобы начать заново.",
            reply_markup=ReplyKeyboardRemove()
        )
    elif update.callback_query:
        q = update.callback_query
        await q.answer()
        await q.message.reply_text(
            "🚫 Действие отменено. Нажми /start, чтобы начать заново.",
            reply_markup=ReplyKeyboardRemove()
        )
    return ConversationHandler.END

# ====== MAIN ======
async def post_init(app: Application):
    await app.bot.set_my_commands([
        BotCommand("start", "Начать"),
        BotCommand("signal", "Получить сигнал"),
        BotCommand("history", "История сигналов"),
        BotCommand("profile", "Мой профиль"),
        BotCommand("instruction", "Подробная инструкция"),
        BotCommand("cancel", "Отмена"),
    ])

def main():
    app = Application.builder().token(TOKEN).post_init(post_init).build()


    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            WAIT_ID: [
                CallbackQueryHandler(registered_pressed, pattern="^registered$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_id),
            ],
            WAIT_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, amount_text)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )

    app.add_handler(conv)

    app.add_handler(CommandHandler("signal", signal_cmd))
    app.add_handler(CommandHandler("history", history))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(CommandHandler("instruction", instruction))


    app.add_handler(CallbackQueryHandler(amount_button, pattern=r"^amt:"))
    app.add_handler(CallbackQueryHandler(change_amount_callback, pattern=r"^change_amount$"))

    logger.info("Bot is running...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
