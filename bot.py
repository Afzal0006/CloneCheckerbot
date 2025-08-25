from pyrogram import Client, filters
from pymongo import MongoClient
import asyncio

# ==== CONFIG ====
API_ID = 24597778
API_HASH = "0b34ead62566cc7b072c0cf6b86b716e"
BOT_TOKEN = "6470654669:AAGdIa0b0As_XmgnT0OD2yZa1Otpos2f3YM"

# ==== MongoDB Atlas ====
MONGO_URI = "mongodb+srv://afzal99550:afzal99550@cluster0.aqmbh9q.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["escrow_db"]     # Database ka naam
deals_col = db["deals"]            # Collection ka naam

app = Client("escrow_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


@app.on_message(filters.group)
async def handle_group_messages(client, message):
    if not message.text:
        return

    text = message.text.strip()

    # 1) Agar new DEAL INFO form hai → extract buyer & seller
    if text.startswith("DEAL INFO"):
        lines = text.splitlines()
        buyer_line = next((l for l in lines if l.startswith("BUYER")), "")
        seller_line = next((l for l in lines if l.startswith("SELLER")), "")
        amount_line = next((l for l in lines if l.startswith("DEAL AMOUNT")), "")
        time_line = next((l for l in lines if l.startswith("TIME TO COMPLETE DEAL")), "")

        buyer = buyer_line.split(":", 1)[1].strip() if ":" in buyer_line else None
        seller = seller_line.split(":", 1)[1].strip() if ":" in seller_line else None
        amount = amount_line.split(":", 1)[1].strip() if ":" in amount_line else None
        deadline = time_line.split(":", 1)[1].strip() if ":" in time_line else None

        if buyer and seller:
            # DB save
            deal_data = {
                "chat_id": message.chat.id,
                "buyer": buyer,
                "seller": seller,
                "amount": amount,
                "deadline": deadline,
                "created_by": message.from_user.id,
                "status": "active"
            }
            deals_col.insert_one(deal_data)

            # Send confirmation + instant delete
            sent_msg = await client.send_message(
                message.chat.id,
                f"✅ New Deal Set!\nBuyer: {buyer}\nSeller: {seller}"
            )
            await sent_msg.delete()   # instantly delete

        return

    # 2) Agar koi 'release' ya 'refund' bole
    lowered = text.lower()
    if "release" in lowered or "refund" in lowered:
        sender_username = f"@{message.from_user.username}" if message.from_user.username else ""

        # Latest deal nikaalo is group ka
        current_deal = deals_col.find_one({"chat_id": message.chat.id}, sort=[("_id", -1)])

        if not current_deal:
            await client.send_message(message.chat.id, "⚠ No active deal found in this group.")
            return

        buyer = current_deal["buyer"]
        seller = current_deal["seller"]

        # Check: agar wo current buyer ya seller hai → allowed
        if sender_username in [buyer, seller]:
            await client.send_message(
                message.chat.id,
                f"✔ Allowed: {sender_username} used `{lowered}` on deal between {buyer} & {seller}"
            )
            return

        # Agar admin hai to skip
        member = await client.get_chat_member(message.chat.id, message.from_user.id)
        if member.status in ["administrator", "creator"]:
            return

        # Warn user: "Tag on deal"
        await client.send_message(
            message.chat.id,
            f"⚠ {sender_username} please tag on deal. Only Buyer ({buyer}) or Seller ({seller}) can request."
        )
        return


print("🤖 Escrow bot with MongoDB Atlas is running…")
app.run()
