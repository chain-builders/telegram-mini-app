import os
import json
import logging
import time
import datetime
from collections import defaultdict
from functools import wraps
from web3 import Web3
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, 
    ApplicationBuilder, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler,
    ConversationHandler,
    filters, 
    Application
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s'
)

logger = logging.getLogger(__name__)

load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))
# States for conversation handling
AMOUNT, ADDRESS, CONFIRMATION = range(3)

# Rate limiting
RATE_LIMIT = 5  # Maximum number of commands per minute
RATE_WINDOW = 60  # Window in seconds

# Define security levels
class SecurityLevel:
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

def restricted(security_level=SecurityLevel.LOW):
    """Decorator to restrict command access based on security level"""
    def decorator(func):
        @wraps(func)
        async def wrapped(self, update, context, *args, **kwargs):
            user_id = update.effective_user.id
            # Check if user is authorized
            if not self.is_user_authorized(user_id, security_level):
                await update.message.reply_text("You don't have permission to use this command.")
                return
            # Apply rate limiting
            if not self.check_rate_limit(user_id):
                await update.message.reply_text("Rate limit exceeded. Please try again later.")
                return
            return await func(self, update, context, *args, **kwargs)
        return wrapped
    return decorator

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
        
        # Track transaction history
        self.transaction_history = defaultdict(list)
        
        # Security and rate limiting
        self.authorized_users = {}  # user_id: security_level
        self.command_timestamps = defaultdict(list)  # user_id: [timestamps]
        
        # User wallets
        self.user_wallets = {}  # user_id: {"address": address, "balance": balance}
        
        # Active conversations
        self.active_transfers = {}

    def validate_env_vars(self):
        print(self.alchemy_http_url)
        print(self.contract_address)
        print(self.contract_abi_path)
        print(self.private_key)
        print(self.token)
        print(self.username)
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
                return json.load(f)['abi']
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

    def transfer(self, to_address: str, amount: float) -> str:
        nonce = self.http_w3.eth.get_transaction_count(self.http_w3.eth.default_account)
        gas_price = self.http_w3.eth.gas_price
        transaction = {
            'to': to_address,
            'value': self.http_w3.to_wei(amount, 'ether'),
            'gas': 2000000,
            'gasPrice': gas_price,
            'nonce': nonce,
            'chainId': 1  # Mainnet
        }
        
        signed_txn = self.http_w3.eth.account.sign_transaction(transaction, private_key=self.private_key)
        txn_hash = self.http_w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        return txn_hash.hex()
    # Security Methods
    def is_user_authorized(self, user_id, required_level=SecurityLevel.LOW):
        """Check if a user is authorized for a specific security level"""
        if user_id not in self.authorized_users:
            # If not registered, give basic access
            self.authorized_users[user_id] = SecurityLevel.LOW
            
        user_level = self.authorized_users[user_id]
        
        if required_level == SecurityLevel.LOW:
            return True
        elif required_level == SecurityLevel.MEDIUM:
            return user_level in [SecurityLevel.MEDIUM, SecurityLevel.HIGH]
        elif required_level == SecurityLevel.HIGH:
            return user_level == SecurityLevel.HIGH
        
        return False
    
    def check_rate_limit(self, user_id):
        """Check if user has exceeded rate limit"""
        current_time = time.time()
        timestamps = self.command_timestamps[user_id]
        
        # Remove timestamps older than the window
        timestamps = [ts for ts in timestamps if current_time - ts < RATE_WINDOW]
        self.command_timestamps[user_id] = timestamps
        
        # Add current timestamp
        timestamps.append(current_time)
        
        # Check if rate limit is exceeded
        return len(timestamps) <= RATE_LIMIT
    
    # Wallet Helper Methods
    def get_wallet_balance(self, address):
        """Get balance for a wallet address"""
        try:
            wei_balance = self.http_w3.eth.get_balance(address)
            eth_balance = self.http_w3.from_wei(wei_balance, 'ether')
            return eth_balance
        except Exception as e:
            logger.error(f"Error getting balance: {str(e)}")
            return None
            
    def record_transaction(self, user_id, tx_hash, from_address, to_address, amount, status="pending"):
        """Record a transaction in history"""
        tx_record = {
            "tx_hash": tx_hash,
            "from": from_address,
            "to": to_address,
            "amount": amount,
            "timestamp": datetime.datetime.now().isoformat(),
            "status": status
        }
        self.transaction_history[user_id].append(tx_record)
        return tx_record
        
    def validate_address(self, address):
        """Validate Ethereum address"""
        try:
            return self.http_w3.is_address(address) and self.http_w3.is_checksum_address(address)
        except:
            return False
            
    def validate_amount(self, amount_str):
        """Validate amount is a positive number"""
        try:
            amount = float(amount_str)
            return amount > 0
        except:
            return False
    
    def setup_app(self):
        self.app = ApplicationBuilder().token(self.token).build()
        print('Telegram app initialized')
        
        # Basic commands
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("custom", self.custom_command))
        
        # Wallet commands
        self.app.add_handler(CommandHandler("wallet", self.wallet_command))
        self.app.add_handler(CommandHandler("balance", self.balance_command))
        self.app.add_handler(CommandHandler("history", self.history_command))
        self.app.add_handler(CommandHandler("menu", self.menu_command))
        
        # Setup send conversation handler
        send_conv_handler = ConversationHandler(
            entry_points=[CommandHandler("send", self.send_command)],
            states={
                AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.send_amount)],
                ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.send_address)],
                CONFIRMATION: [
                    CallbackQueryHandler(self.send_confirm, pattern='^confirm$'),
                    CallbackQueryHandler(self.send_cancel, pattern='^cancel$')
                ],
            },
            fallbacks=[CommandHandler("cancel", self.send_cancel_command)],
        )
        self.app.add_handler(send_conv_handler)
        
        # Handle callback queries from inline keyboards
        self.app.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Message handler
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Error handler
        self.app.add_error_handler(self.error)
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        user_id = user.id
        
        # Register user with basic security level if not registered
        if user_id not in self.authorized_users:
            self.authorized_users[user_id] = SecurityLevel.LOW
        
        welcome_text = (
            f"Hello {user.first_name}! I'm your Telegram crypto wallet bot.\n\n"
            "I can help you manage your crypto transactions and check your wallet status.\n"
            "Use /help to see available commands or /menu for an interactive menu."
        )
        
        await update.message.reply_text(welcome_text)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        help_text = (
            "📋 *Available Commands:*\n\n"
            "🌟 *Basic Commands:*\n"
            "/start - Start the bot\n"
            "/help - Display this help message\n"
            "/menu - Show interactive menu\n\n"
            "💰 *Wallet Commands:*\n"
            "/wallet - View your wallet information\n"
            "/balance - Check your wallet balance\n"
            "/send - Send crypto to an address\n"
            "/history - View your transaction history\n\n"
            "⚙️ *Other Commands:*\n"
            "/custom - Execute a predefined transaction\n"
        )
        await update.message.reply_text(help_text, parse_mode="Markdown")

    @restricted(SecurityLevel.MEDIUM)
    async def custom_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        try:
            # This is a restricted command that requires medium security level
            tx_hash = self.transfer('0xRecipientAddress', 0.01)  # Replace with actual recipient address and amount
            
            user_id = update.effective_user.id
            self.record_transaction(
                user_id, 
                tx_hash, 
                self.http_w3.eth.default_account, 
                '0xRecipientAddress', 
                0.01
            )
            
            await update.message.reply_text(
                "✅ Transaction executed successfully!\n\n"
                f"Transaction hash: `{tx_hash}`",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Error in custom command: {str(e)}")
            await update.message.reply_text(f"❌ Error executing transaction: {str(e)}")
            
    @restricted(SecurityLevel.LOW)
    async def wallet_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_id = update.effective_user.id
        
        if user_id in self.user_wallets:
            wallet = self.user_wallets[user_id]
            balance = self.get_wallet_balance(wallet["address"])
            
            wallet_text = (
                "🏦 *Your Wallet Information:*\n\n"
                f"🔑 Address: `{wallet['address']}`\n"
                f"💰 Balance: `{balance} ETH`\n\n"
                "Use /send to make a transaction."
            )
        else:
            wallet_text = (
                "You don't have a wallet yet. Would you like to create one?"
            )
            # Create inline keyboard for wallet creation
            keyboard = [
                [
                    InlineKeyboardButton("Create Wallet", callback_data="create_wallet"),
                    InlineKeyboardButton("Import Wallet", callback_data="import_wallet")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(wallet_text, reply_markup=reply_markup)
            return
            
        await update.message.reply_text(wallet_text, parse_mode="Markdown")
    
    @restricted(SecurityLevel.LOW)
    async def balance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_id = update.effective_user.id
        
        if user_id in self.user_wallets:
            wallet = self.user_wallets[user_id]
            balance = self.get_wallet_balance(wallet["address"])
            
            balance_text = (
                "💰 *Your Current Balance:*\n\n"
                f"`{balance} ETH`"
            )
        else:
            balance_text = "You don't have a wallet yet. Use /wallet to create one."
            
        await update.message.reply_text(balance_text, parse_mode="Markdown")
    
    @restricted(SecurityLevel.LOW)
    async def history_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_id = update.effective_user.id
        
        if user_id in self.transaction_history and self.transaction_history[user_id]:
            history = self.transaction_history[user_id]
            
            # Format the transaction history
            history_text = "📜 *Your Transaction History:*\n\n"
            
            # Display the last 5 transactions (or fewer if there are less)
            for i, tx in enumerate(history[-5:], 1):
                history_text += (
                    f"*{i}. Transaction:* `{tx['tx_hash'][:8]}...`\n"
                    f"   *From:* `{tx['from'][:10]}...`\n"
                    f"   *To:* `{tx['to'][:10]}...`\n"
                    f"   *Amount:* `{tx['amount']} ETH`\n"
                    f"   *Status:* `{tx['status']}`\n"
                    f"   *Date:* `{tx['timestamp'][:10]}`\n\n"
                )
                
            history_text += "Use /send to make a new transaction."
        else:
            history_text = "You don't have any transaction history yet. Use /send to make your first transaction."
            
        await update.message.reply_text(history_text, parse_mode="Markdown")
    
    @restricted(SecurityLevel.LOW)
    async def menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Display interactive menu with main bot functions"""
        keyboard = [
            [
                InlineKeyboardButton("💰 Check Balance", callback_data="check_balance"),
                InlineKeyboardButton("📜 Transaction History", callback_data="view_history")
            ],
            [
                InlineKeyboardButton("💸 Send Funds", callback_data="send_funds"),
                InlineKeyboardButton("🏦 Wallet Info", callback_data="wallet_info")
            ],
            [
                InlineKeyboardButton("❓ Help", callback_data="show_help")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🤖 *Welcome to the Botfather Menu*\n\n"
            "Please select an option from the menu below:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle callback queries from inline keyboard buttons"""
        query = update.callback_query
        await query.answer()  # Answer the callback query to stop the loading indicator
        
        user_id = update.effective_user.id
        callback_data = query.data
        
        # Handle different callback actions
        if callback_data == "check_balance":
            if user_id in self.user_wallets:
                wallet = self.user_wallets[user_id]
                balance = self.get_wallet_balance(wallet["address"])
                await query.message.reply_text(
                    f"💰 Your current balance: *{balance} ETH*",
                    parse_mode="Markdown"
                )
            else:
                await query.message.reply_text("You don't have a wallet yet. Use /wallet to create one.")
                
        elif callback_data == "view_history":
            await self.history_command(update, context)
            
        elif callback_data == "send_funds":
            await query.message.reply_text("Please use /send command to start a new transaction.")
            
        elif callback_data == "wallet_info":
            await self.wallet_command(update, context)
            
        elif callback_data == "show_help":
            await self.help_command(update, context)
            
        elif callback_data == "create_wallet":
            # Generate a new wallet for the user
            try:
                account = self.http_w3.eth.account.create()
                self.user_wallets[user_id] = {
                    "address": account.address,
                    "private_key": account.key.hex()  # In a real app, encrypt this!
                }
                
                await query.message.reply_text(
                    "✅ Wallet created successfully!\n\n"
                    f"🔑 Your wallet address: `{account.address}`\n\n"
                    "⚠️ IMPORTANT: Please store your private key securely!\n"
                    f"🔐 Private key: `{account.key.hex()}`\n\n"
                    "Use /wallet to view your wallet information.",
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Error creating wallet: {str(e)}")
                await query.message.reply_text(f"❌ Error creating wallet: {str(e)}")
                
        elif callback_data == "import_wallet":
            await query.message.reply_text(
                "To import a wallet, please enter your private key.\n\n"
                "⚠️ Note: Never share your private key with anyone!"
            )
            # In a real app, you would set up a conversation handler for this
            
        elif callback_data == "confirm":
            await self.send_confirm(update, context)
            
        elif callback_data == "cancel":
            await self.send_cancel(update, context)
    
    @restricted(SecurityLevel.LOW)
    async def send_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start the send conversation."""
        user_id = update.effective_user.id
        
        if user_id not in self.user_wallets:
            await update.message.reply_text(
                "You don't have a wallet yet. Use /wallet to create one first."
            )
            return ConversationHandler.END
        
        # Initialize a new transfer in the active_transfers dictionary
        self.active_transfers[user_id] = {}
        
        await update.message.reply_text(
            "💸 *Send Transaction*\n\n"
            "Please enter the amount of ETH you want to send:",
            parse_mode="Markdown"
        )
        
        return AMOUNT
    
    async def send_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Process the amount and ask for address."""
        user_id = update.effective_user.id
        amount_text = update.message.text
        
        # Validate amount
        if not self.validate_amount(amount_text):
            await update.message.reply_text(
                "❌ Invalid amount. Please enter a positive number."
            )
            return AMOUNT
        
        # Store the amount in active_transfers
        self.active_transfers[user_id]["amount"] = float(amount_text)
        
        await update.message.reply_text(
            "Please enter the recipient's Ethereum address:"
        )
        
        return ADDRESS
    
    async def send_address(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Process the address and ask for confirmation."""
        user_id = update.effective_user.id
        address = update.message.text
        
        # Validate address
        if not self.validate_address(address):
            await update.message.reply_text(
                "❌ Invalid Ethereum address. Please enter a valid address."
            )
            return ADDRESS
        
        # Store the address in active_transfers
        self.active_transfers[user_id]["to_address"] = address
        amount = self.active_transfers[user_id]["amount"]
        
        # Create confirmation keyboard
        keyboard = [
            [
                InlineKeyboardButton("✅ Confirm", callback_data="confirm"),
                InlineKeyboardButton("❌ Cancel", callback_data="cancel")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"📝 *Transaction Summary*\n\n"
            f"Amount: *{amount} ETH*\n"
            f"To: `{address}`\n\n"
            f"Please confirm this transaction:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        return CONFIRMATION
    
    async def send_confirm(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Execute the transaction after confirmation."""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        transfer_data = self.active_transfers.get(user_id)
        
        if not transfer_data:
            await query.message.reply_text("Transaction data not found. Please try again with /send.")
            return ConversationHandler.END
        
        try:
            # Get transfer details
            amount = transfer_data["amount"]
            to_address = transfer_data["to_address"]
            
            # Execute the transfer
            tx_hash = self.transfer(to_address, amount)
            
            # Record the transaction
            wallet = self.user_wallets[user_id]
            self.record_transaction(
                user_id,
                tx_hash,
                wallet["address"],
                to_address,
                amount
            )
            
            await query.message.reply_text(
                "✅ *Transaction Sent Successfully!*\n\n"
                f"Amount: *{amount} ETH*\n"
                f"To: `{to_address}`\n"
                f"Transaction hash: `{tx_hash}`\n\n"
                f"Use /history to view your transaction history.",
                parse_mode="Markdown"
            )
            
            # Clean up
            del self.active_transfers[user_id]
            
        except Exception as e:
            logger.error(f"Transaction error: {str(e)}")
            await query.message.reply_text(
                f"❌ *Transaction Failed*\n\n"
                f"Error: {str(e)}",
                parse_mode="Markdown"
            )
        
        return ConversationHandler.END
    
    async def send_cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Cancel the transaction."""
        if update.callback_query:
            query = update.callback_query
            await query.answer()
            user_id = update.effective_user.id
            
            # Clean up
            if user_id in self.active_transfers:
                del self.active_transfers[user_id]
            
            await query.message.reply_text("Transaction cancelled.")
        else:
            await update.message.reply_text("Transaction cancelled.")
        
        return ConversationHandler.END
    
    async def send_cancel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Cancel the transaction via command."""
        user_id = update.effective_user.id
        
        # Clean up
        if user_id in self.active_transfers:
            del self.active_transfers[user_id]
        
        await update.message.reply_text("Transaction cancelled.")
        
        return ConversationHandler.END

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
    