import os
import json
import logging
import time
from web3 import Web3
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ContextTypes, ApplicationBuilder, CommandHandler, MessageHandler, filters, Application

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s'
)

logger = logging.getLogger(__name__)

load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

class TelegramBot:
    def __init__(self):
        self.alchemy_http_url = os.getenv("ALCHEMY_HTTP_URL")
        self.contract_address = os.getenv('CONTRACT_ADDRESS')
        self.contract_abi_path = os.getenv('CONTRACT_ABI_PATH')
        self.private_key = os.getenv('CONTRACT_OWNER_PRIVATE_KEY')
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.username = os.getenv('TELEGRAM_BOT_USERNAME')
        self.app = None

        self.http_w3 = None
        self.contract = None

    def validate_env_vars(self):
        missing_vars = []
        if not self.alchemy_http_url:
            missing_vars.append("ALCHEMY_HTTP_URL")
        if not self.contract_address:
            missing_vars.append("CONTRACT_ADDRESS")
        if not self.contract_abi_path:
            missing_vars.append("CONTRACT_ABI_PATH")
        if not self.private_key:
            missing_vars.append("CONTRACT_OWNER_PRIVATE_KEY")
        if not self.token:
            missing_vars.append("TELEGRAM_BOT_TOKEN")
        if not self.username:
            missing_vars.append("TELEGRAM_BOT_USERNAME")
        
        if missing_vars:
            raise ValueError(f"Missing environment variables: {', '.join(missing_vars)}")
        
    def load_contract_abi(self):
        try:
            with open(self.contract_abi_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"ABI file not found at {self.contract_abi_path}")
            raise
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in ABI file at {self.contract_abi_path}")
            raise

    def initialize_web3_connections(self):
        self.validate_env_vars()
        self.http_w3 = Web3(Web3.HTTPProvider(self.alchemy_http_url))
        contract_abi = self.load_contract_abi()
        self.contract = self.http_w3.eth.contract(
            address=self.http_w3.to_checksum_address(self.contract_address),
            abi=contract_abi
        )
        print('Web3 connections initialized')
        print(self.contract)

    def send_eth(self, recipient: str, amount: float) -> str:
        if not self.http_w3:
            self.initialize_web3_connections()

        account = self.http_w3.eth.account.from_key(self.private_key)
        txn = self.contract.functions.sendETH(
            recipient
        ).build_transaction({
            'from': account.address,
            'nonce': self.http_w3.eth.get_transaction_count(account.address),
            'gas': 200000,
            'gasPrice': self.http_w3.eth.gas_price,
            'value': self.http_w3.to_wei(amount, 'ether'),
            'chainId': 84532
        })
        signed_txn = self.http_w3.eth.account.sign_transaction(txn, self.private_key)
        tx_hash = self.http_w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        print(f"Create Pool sent: {tx_hash.hex()}")
        return {'tx_hash': tx_hash.hex(), 'status': 'pending'}

    def transfer(self, to_address: str, amount: float) -> str:
        default_account = self.http_w3.eth.default_account
        print(f"Default account: {default_account}")
        print(type(default_account))
        print(f"Sending {amount} ETH to {to_address}")
        nonce = self.http_w3.eth.get_transaction_count('0x58bd94230B41353D73A899C061A80F3205de87f0')
        gas_price = self.http_w3.eth.gas_price
        transaction = {
            'to': to_address,
            'value': self.http_w3.to_wei(amount, 'ether'),
            'gas': 2000000,
            'gasPrice': gas_price,
            'nonce': nonce,
            'chainId': 11155111
        }
        
        signed_txn = self.http_w3.eth.account.sign_transaction(transaction, private_key=self.private_key)
        txn_hash = self.http_w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        return txn_hash.hex()

    def setup_app(self):
        self.app = ApplicationBuilder().token(self.token).build()
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("custom", self.custom_command))
        self.app.add_handler(CommandHandler("send", self.send_command))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        self.app.add_error_handler(self.error)
        print('Telegram bot setup complete')
        self.app.run_polling(poll_interval=3, timeout=10, drop_pending_updates=True)

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text("Hello! I'm your base transaction bot. How can I assist you today?")
        # update.effective_user.first_name
        # await context.bot.send_message(chat_id=update.effective_chat.id, text="Hello! I'm your bot. How can I assist you today?")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text("Here are some commands you can use:\n/start - Start the bot\n/help - Get help\n/custom - Custom command\n/send - Send ETH to an address")

    async def custom_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text("Use the following custom message to send ETH to an address.\nFormat: /send <address> <amount>")

    async def send_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if len(context.args) != 2:
            await update.message.reply_text("Usage: /send <address> <amount>")
            return

        recipient = context.args[0]
        try:
            amount = float(context.args[1])
        except ValueError:
            await update.message.reply_text("Invalid amount. Please enter a valid number.")
            return

        try:
            tx_hash = self.send_eth(recipient, amount)
            await update.message.reply_text(f"Transaction sent! Hash: {tx_hash}")
        except Exception as e:
            await update.message.reply_text(f"Error: {str(e)}")

    def handle_response(self, text: str) -> str:
        if 'hello' in text.lower():
            return "Hello! How can I help you?"
        elif 'bye' in text.lower():
            return "Goodbye! Have a great day!"
        else:
            return "I'm not sure how to respond to that."

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
            if self.username in text:
                new_text = text.replace(self.username, '').strip()
                response = self.handle_response(new_text)
            else:
                return
        else:
            response = self.handle_response(text)

        #response = handle_response(text)
        print('Bot:', response)
        await update.message.reply_text(response)

    async def error(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        print(f"Update {update} caused error {context.error}")

    def transferFunds(self):
        self.transfer('0xa38062B76617585a6DB4AF9759ef3A850B35Ed9a', 0.002)
    