import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
import requests

TOKEN = '7863844580:AAEg_uVGeHouo2h0sLo58Qa1WnmpK3XPG5s'
CHAT_ID = 8147195702

user_alert = {
    'operator': None,
    'price': None
}

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Bienvenido, escribe /crearalerta para configurar tu alerta de precio.")

async def crear_alerta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(">", callback_data=">"), InlineKeyboardButton("<", callback_data="<")],
        [InlineKeyboardButton(">=", callback_data=">="), InlineKeyboardButton("<=", callback_data="<=")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("¿Qué condición deseas usar para el precio de SOL/USDC?", reply_markup=reply_markup)

async def handle_operator(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_alert['operator'] = query.data
    await query.edit_message_text(f"Elegiste: {query.data}\nAhora escribe el precio objetivo (ej. 158.5):")

async def handle_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_alert['price'] = float(update.message.text)
        await update.message.reply_text(f"✅ Alerta configurada: cuando SOL/USDC {user_alert['operator']} {user_alert['price']}")
    except ValueError:
        await update.message.reply_text("❌ Ingresa un número válido para el precio.")

def get_sol_price():
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price", params={"ids": "solana", "vs_currencies": "usd"})
        return r.json()["solana"]["usd"]
    except:
        return None

async def check_alert(context: ContextTypes.DEFAULT_TYPE):
    if not user_alert['operator'] or not user_alert['price']:
        return

    current_price = get_sol_price()
    if current_price is None:
        return

    op = user_alert['operator']
    target = user_alert['price']
    cumple = (
        (op == ">" and current_price > target) or
        (op == "<" and current_price < target) or
        (op == ">=" and current_price >= target) or
        (op == "<=" and current_price <= target)
    )

    if cumple:
        await context.bot.send_message(
            chat_id=CHAT_ID,
            text=f"🚨 ALERTA: El precio de SOL/USDC es ${current_price:.2f} (cumple condición: {op} {target})"
        )
        user_alert['operator'] = None
        user_alert['price'] = None

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("crearalerta", crear_alerta))
    app.add_handler(CallbackQueryHandler(handle_operator))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_price))

    app.job_queue.run_repeating(check_alert, interval=60, first=10)

    print("🤖 Bot corriendo...")
    app.run_polling()