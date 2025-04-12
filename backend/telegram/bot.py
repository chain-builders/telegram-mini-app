from telegram import Update
from telegram.ext import ContextTypes, ApplicationBuilder, CommandHandler, MessageHandler, filters

TOKEN = ''
USERNAME = ''

def activator():
    print("activator initialized")
    async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text("Hello! I'm your bot. How can I assist you today?")

    async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text("Here are some commands you can use:\n/start - Start the bot\n/help - Get help")

    async def custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text("This is a custom command!")

    def handle_response(text: str) -> str:
        if 'hello' in text.lower():
            return "Hello! How can I help you?"
        elif 'bye' in text.lower():
            return "Goodbye! Have a great day!"
        else:
            return "I'm not sure how to respond to that."

    async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        message_type = update.message.chat.type
        '''if message_type == 'private':
            await update.message.reply_text("This is a private chat.")
        elif message_type == 'group':
            await update.message.reply_text("This is a group chat.")
        elif message_type == 'channel':
            await update.message.reply_text("This is a channel.")'''
        text = update.message.text
        print(f"Received message: {text}")
        print(f'User ({update.message.chat.id}) in {message_type}: "{text}"')
        if message_type == 'group':
            if USERNAME in text:
                new_text = text.replace(USERNAME, '').strip()
                response = handle_response(new_text)
            else:
                return
        else:
            response = handle_response(text)

        #response = handle_response(text)
        print('Bot:', response)
        await update.message.reply_text(response)

    async def error(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        print(f"Update {update} caused error {context.error}")


    app = ApplicationBuilder().token(TOKEN).build()
    # commands
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("custom", custom_command))
    # messages
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    # errors
    app.add_error_handler(error)

    app.run_polling(poll_interal=3.0, timeout=10)
    print("activator finished")