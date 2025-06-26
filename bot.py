from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = "8006836827:AAFQl8eVBBfI07CuHWh_oqxbFX5rYUyB-XE"  # Replace with your bot token

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is alive and working!")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()  # ❌ Don't use await, just call it

if __name__ == "__main__":
    main()
