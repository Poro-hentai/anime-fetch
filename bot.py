from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = "8006836827:AAFQl8eVBBfI07CuHWh_oqxbFX5rYUyB-XE"  # <-- yahan apna bot token daalein

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is working! Welcome to FX Bot.")

async def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
