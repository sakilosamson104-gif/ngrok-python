import os
import sys
import logging
from typing import List
import base64

from telegram import Update
from telegram.ext import (
		Application,
		CommandHandler,
		ContextTypes,
		ApplicationBuilder,
		MessageHandler,
		filters,
)
from dotenv import load_dotenv

# Your new solana utils (paste the whole block from above here or import it)
# ... [paste the solana_utils.py code here] ...

# ------------------------------------------------------------------
# Config & logging (same as before)
# ------------------------------------------------------------------
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

required_vars = ["BOT_TOKEN", "ADMIN_ID", "PRIVATE_KEY", "MAIN_RPC"]
missing = [var for var in required_vars if not os.getenv(var)]
if missing:
		logger.error(f"Missing: {', '.join(missing)}")
		sys.exit(1)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_ID", "").split(",") if x.strip()]
PRIVATE_KEY = os.getenv("PRIVATE_KEY").strip()

# ... (all your other config variables exactly as before) ...

# ------------------------------------------------------------------
# Admin check & helpers
# ------------------------------------------------------------------
def is_admin(user_id: int | None) -> bool:
		return user_id in ADMIN_IDS

# ------------------------------------------------------------------
# Handlers
# ------------------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
		if not is_admin(update.effective_user.id):
				await update.message.reply_text("⛔ Unauthorized")
				return
		await update.message.reply_text("Bot alive. Use /help")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
		if not is_admin(update.effective_user.id):
				return
		await update.message.reply_text(
				"/buy <mint> [amount_sol] — e.g. /buy Dez... 0.5\n"
				"/sell <mint> [percent] — e.g. /sell Dez... 50 (sell 50%)"
		)

# --------------------- BUY ---------------------
async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
		if not is_admin(update.effective_user.id):
				return

		if len(context.args) < 1:
				await update.message.reply_text("Usage: /buy <token_mint> [amount_sol]")
				return

		mint = context.args[0]
		amount_sol = float(context.args[1]) if len(context.args) > 1 else DEFAULT_BUY_AMOUNT

		msg = await update.message.reply_text("Getting quote...")

		try:
				lamports = int(amount_sol * 1e9)
				quote = await get_quote("So11111111111111111111111111111111111111112", mint, lamports)
				tx = await get_swap_transaction(quote, keypair.pubkey())
				url = await execute_swap(tx)
				await msg.edit_text(f"BOUGHT ✅\n{url}")
		except Exception as e:
				await msg.edit_text(f"Buy failed ❌\n{str(e)}")

# --------------------- SELL ---------------------
async def sell(update: Update, context: ContextTypes.DEFAULT_TYPE):
		if not is_admin(update.effective_user.id):
				return

		if len(context.args) < 1:
				await update.message.reply_text("Usage: /sell <token_mint> [percent]")
				return

		mint = context.args[0]
		percent = float(context.args[1]) if len(context.args) > 1 else 100.0

		msg = await update.message.reply_text("Preparing sell...")

		try:
				# Get token balance
				resp = await async_client.get_token_accounts_by_owner(keypair.pubkey(), mint=mint)
				if not resp.value:
						await msg.edit_text("No tokens found")
						return
				ata = resp.value[0].pubkey
				balance_resp = await async_client.get_token_account_balance(ata)
				amount = int(balance_resp.value.amount)
				sell_amount = int(amount * (percent / 100))

				quote = await get_quote(mint, "So11111111111111111111111111111111111111112", sell_amount)
				tx = await get_swap_transaction(quote, keypair.pubkey())
				url = await execute_swap(tx)
				await msg.edit_text(f"SOLD {percent}% ✅\n{url}")
		except Exception as e:
				await msg.edit_text(f"Sell failed ❌\n{str(e)}")

# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------
async def main():
		logger.info("Initializing Solana connection...")
		await init_solana()
		logger.info(f"Wallet: {keypair.pubkey()}")

		app = Application.builder().token(BOT_TOKEN).build()

		app.add_handler(CommandHandler("start", start))
		app.add_handler(CommandHandler("help", help_command))
		app.add_handler(CommandHandler("buy", buy))
		app.add_handler(CommandHandler("sell", sell))

		logger.info("Bot started - listening...")
		await app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
		import asyncio
		asyncio.run(main())
