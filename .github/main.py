import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import time
import threading
from solana.rpc.api import Client
from solana.keypair import Keypair
from solana.transaction import Transaction

BOT_TOKEN     = "YOUR_BOT_TOKEN_HERE"
WALLET_SECRET = "1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64"
TOKEN_MINT    = "PUT_YOUR_TOKEN_MINT_HERE"

client = Client("https://api.mainnet-beta.solana.com")
keypair = Keypair.from_bytes(bytes([int(x) for x in WALLET_SECRET.split(",")]))

bot = telebot.TeleBot(BOT_TOKEN)

def get_swap_tx(amount=500000):
    quote = requests.get("https://quote-api.jup.ag/v6/quote", params={
        "inputMint": "So11111111111111111111111111111111111111112",
        "outputMint": TOKEN_MINT,
        "amount": amount,
        "slippageBps": 300
    }).json()

    swap = requests.post("https://quote-api.jup.ag/v6/swap", json={
        "quoteResponse": quote,
        "userPublicKey": str(keypair.pubkey()),
        "wrapAndUnwrapSol": True
    }).json()

    return swap["swapTransaction"]

@bot.message_handler(commands=['start'])
def start(m):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("10x", callback_data="v10"),
        InlineKeyboardButton("30x", callback_data="v30"),
        InlineKeyboardButton("100x", callback_data="v100")
    )
    bot.send_message(m.chat.id,
        f"Mainnet Volume Bot Ready\n\n"
        f"Wallet: `{keypair.pubkey()}`\n"
        f"Token: `{TOKEN_MINT}`\n\n"
        "Select volume:",
        reply_markup=kb, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: True)
def run(c):
    if not c.data.startswith("v"): return
    n = int(c.data[1:])
    bot.answer_callback_query(c.id, f"Pumping {n}x…")
    threading.Thread(target=pump, args=(c.message.chat.id, n)).start()

def pump(chat, count):
    ok = 0
    for i in range(1, count+1):
        try:
            raw = get_swap_tx(400000 + i%200000)
            tx = Transaction.deserialize(bytes.fromhex(raw))
            tx.sign(keypair)
            txid = client.send_raw_transaction(tx.serialize())["result"]
            ok += 1
            bot.send_message(chat, f"{i}/{count} https://solscan.io/tx/{txid}")
            time.sleep(2.8)
        except Exception as e:
            bot.send_message(chat, f"Error {i}: {str(e)[:80]}")
            time.sleep(4)
    bot.send_message(chat, f"DONE → {ok}/{count} real trades sent")

bot.infinity_polling()