import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from datetime import datetime, timedelta
import json
import os
from apscheduler.schedulers.background import BackgroundScheduler

TOKEN = 'TU_TOKEN_DE_BOT_AQUÍ'  # <-- reemplaza con tu token

# Diccionario para guardar respuestas temporales
RESPUESTAS_PATH = "respuestas.json"
if os.path.exists(RESPUESTAS_PATH):
    with open(RESPUESTAS_PATH, "r") as f:
        tareas_guardadas = json.load(f)
else:
    tareas_guardadas = {}

logging.basicConfig(level=logging.INFO)

# Guardar respuesta del usuario
async def guardar_respuesta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    mensaje = update.message.text
    fecha = datetime.now().strftime("%Y-%m-%d")
    tareas_guardadas[user_id] = tareas_guardadas.get(user_id, {})
    tareas_guardadas[user_id][fecha] = mensaje
    with open(RESPUESTAS_PATH, "w") as f:
        json.dump(tareas_guardadas, f)
    await update.message.reply_text("✅ Guardado. Te lo recordaré mañana a las 7 a.m.")

# Enviar la pregunta a las 5:00 p.m.
async def preguntar_tareas(context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    for user_id in tareas_guardadas.keys():
        await bot.send_message(chat_id=user_id, text="🕔 ¿Qué necesitas hacer mañana a las 7 a.m.? Escribe tus pendientes:")

# Enviar la respuesta guardada a las 7:00 a.m.
async def recordar_tareas(context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    fecha_ayer = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    for user_id, tareas_por_fecha in tareas_guardadas.items():
        tarea = tareas_por_fecha.get(fecha_ayer)
        if tarea:
            await bot.send_message(chat_id=user_id, text=f"📋 Este es tu recordatorio de hoy:\n\n{tarea}")
        else:
            await bot.send_message(chat_id=user_id, text="📋 No registraste tareas ayer.")

# Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Hola, recibirás un mensaje todos los días a las 5 p.m. para planificar tus tareas.\nResponde ahí, y te lo recordaré a las 7 a.m. del día siguiente.")

# Función principal
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Comandos
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, guardar_respuesta))

    # Scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: app.create_task(preguntar_tareas(ContextTypes.DEFAULT_TYPE(bot=app.bot))),
                      trigger='cron', hour=17, minute=0)
    scheduler.add_job(lambda: app.create_task(recordar_tareas(ContextTypes.DEFAULT_TYPE(bot=app.bot))),
                      trigger='cron', hour=7, minute=0)
    scheduler.start()

    print("Bot corriendo...")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
