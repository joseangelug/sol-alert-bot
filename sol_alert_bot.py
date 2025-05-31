import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

# === CONFIG PERSONAL ===
TOKEN = '7863844580:AAEg_uVGeHouo2h0sLo58Qa1WnmpK3XPG5s'
AUTHORIZED_USER_ID = 8147195702  # solo tú puedes usarlo

# === ALERTAS ACTIVAS ===
alerts = []

# === LOGS ===
logging.basicConfig(level=logging.INFO)

# === FUNCIONES BASE ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != AUTHORIZED_USER_ID:
        return
    await update.message.reply_text("👋 Bienvenido, escribe /crearalerta para configurar una nueva.\nUsa /misalertas para ver activas o /cancelaralertas para eliminarlas.")

async def crear_alerta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != AUTHORIZED_USER_ID:
        return
    keyboard = [
        [InlineKeyboardButton(">", callback_data=">"), InlineKeyboardButton("<", callback_data="<")],
        [InlineKeyboardButton(">=", callback_data=">="), InlineKeyboardButton("<=", callback_data="<=")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("¿Qué condición deseas usar para la alerta?", reply_markup=reply_markup)

async def handle_operator(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.from_user.id != AUTHORIZED_USER_ID:
        return
    await query.answer()
    context.user_data['operator'] = query.data
    await query.edit_message_text("✅ Ahora escribe el precio objetivo (ej. 160):")

async def handle_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != AUTHORIZED_USER_ID:
        return
    try:
        operator = context.user_data.get('operator')
        price = float(update.message.text)
        alerts.append({'operator': operator, 'price': price})
        await update.message.reply_text(f"✅ Alerta agregada: cuando SOL/USDC {operator} {price}")
    except:
        await update.message.reply_text("❌ Precio inválido. Intenta otra vez con un número.")

def get_sol_price():
    try:
        res = requests.get("https://api.coingecko.com/api/v3/simple/price", params={"ids": "solana", "vs_currencies": "usd"})
        return res.json()["solana"]["usd"]
    except:
        return None

async def check_alerts(context: ContextTypes.DEFAULT_TYPE):
    if not alerts:
        return
    price = get_sol_price()
    if price is None:
        return

    to_remove = []
    for alert in alerts:
        op = alert["operator"]
        val = alert["price"]
        if (
            (op == ">" and price > val) or
            (op == "<" and price < val) or
            (op == ">=" and price >= val) or
            (op == "<=" and price <= val)
        ):
            await context.bot.send_message(
                chat_id=AUTHORIZED_USER_ID,
                text=f"🚨 ALERTA: SOL/USDC está en ${price:.2f} (condición: {op} {val})"
            )
            to_remove.append(alert)

    for alert in to_remove:
        alerts.remove(alert)

async def mis_alertas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != AUTHORIZED_USER_ID:
        return
    if not alerts:
        await update.message.reply_text("📭 No tienes alertas activas.")
        return
    msg = "📌 Alertas activas:\n"
    for i, a in enumerate(alerts, start=1):
        msg += f"{i}. SOL {a['operator']} {a['price']}\n"
    await update.message.reply_text(msg)

async def cancelar_alertas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != AUTHORIZED_USER_ID:
        return
    alerts.clear()
    await update.message.reply_text("❌ Todas las alertas fueron eliminadas.")

# === MAIN ===
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("crearalerta", crear_alerta))
    app.add_handler(CommandHandler("misalertas", mis_alertas))
    app.add_handler(CommandHandler("cancelaralertas", cancelar_alertas))
    app.add_handler(CallbackQueryHandler(handle_operator))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_price))

    app.job_queue.run_repeating(check_alerts, interval=60, first=5)

    print("🤖 Bot corriendo...")
    app.run_polling()
