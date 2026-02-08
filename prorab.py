import random
import time
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

TOKEN = os.environ.get("TOKEN")  # Токен из переменной среды

users = {}

def get_user(uid, full_name):
    if uid not in users:
        users[uid] = {"name": full_name, "money": 1000, "level": 1, "last_work": 0, "fines": []}
    return users[uid]

def inline_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Получка", callback_data="work")],
        [InlineKeyboardButton("🏗 Магазин", callback_data="shop")],
        [InlineKeyboardButton("🏦 Депозит", callback_data="deposit")],
        [InlineKeyboardButton("💳 Кредит", callback_data="credit")],
        [InlineKeyboardButton("🔁 Перевод", callback_data="transfer")]
    ])

reply_buttons = ReplyKeyboardMarkup([
    [KeyboardButton("💰 Моя получка"), KeyboardButton("🏗 Заработать получку")],
    [KeyboardButton("🆔 Мой ID"), KeyboardButton("👥 Игроки банка")],
    [KeyboardButton("📊 Профиль"), KeyboardButton("🔁 Перевести получку")]
], resize_keyboard=True)

def vit_check(user):
    if random.random() < 0.15:
        fine = random.randint(300, 2500)
        reason = random.choice(["не тот шрифт в журнале","погода не по ГОСТу","лицо слишком довольное","документы лежали криво","подозрительно ровный асфальт"])
        user["money"] -= fine
        user["fines"].append(f"-{fine} ₽ за '{reason}'")
        return f"\n🚨 Проверка! Инспектор Виталик.\nНарушение: {reason}\nШтраф: -{fine} ₽"
    return ""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    full_name = update.effective_user.first_name + " " + (update.effective_user.last_name or "")
    user = get_user(update.effective_user.id, full_name)
    await update.message.reply_text(f"🏦 КаменскАвтодор АсфальтКапитал\nРаботяга: {user['name']}\nБаланс: {user['money']} ₽", reply_markup=inline_menu())
    await update.message.reply_text("Или используй нижние кнопки:", reply_markup=reply_buttons)

async def pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        to_id = int(context.args[0])
        amount = int(context.args[1])
        sender = get_user(update.effective_user.id, update.effective_user.first_name + " " + (update.effective_user.last_name or ""))
        if sender["money"] < amount:
            await update.message.reply_text("❌ Недостаточно средств", reply_markup=inline_menu())
            return
        receiver = users.get(to_id)
        if not receiver:
            receiver = get_user(to_id, f"Игрок {to_id}")
        sender["money"] -= amount
        receiver["money"] += amount
        await update.message.reply_text(f"✅ Вы перевели {amount} ₽ игроку {receiver['name']}", reply_markup=inline_menu())
        try:
            await context.bot.send_message(chat_id=to_id, text=f"💸 Вам пришло {amount} ₽ от {sender['name']}!")
        except: pass
    except:
        await update.message.reply_text("❌ Формат перевода: /pay ID СУММА", reply_markup=inline_menu())

async def reply_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id, update.effective_user.first_name + " " + (update.effective_user.last_name or ""))
    text = update.message.text
    if text in ["💰 Моя получка", "🏗 Заработать получку"]:
        now = time.time()
        if now - user["last_work"] < 60:
            msg = "⏳ Смена ещё не закончилась"
        else:
            user["last_work"] = now
            pay_amount = random.randint(800, 1200)
            user["money"] += pay_amount
            msg = f"Получка: {pay_amount} ₽"
        msg += vit_check(user)
        await update.message.reply_text(msg + f"\nБаланс: {user['money']} ₽", reply_markup=inline_menu())
    elif text == "🔁 Перевести получку":
        await update.message.reply_text("Введите: /pay ID СУММА", reply_markup=inline_menu())
    elif text == "🆔 Мой ID":
        await update.message.reply_text(f"🆔 Твой ID: {update.effective_user.id}", reply_markup=inline_menu())
    elif text == "📊 Профиль":
        fines = "\n".join(user["fines"][-5:]) if user["fines"] else "Нет штрафов"
        msg = f"📊 Профиль: {user['name']}\n💰 Баланс: {user['money']} ₽\n🏗 Уровень: {user['level']}\n📜 Последние штрафы:\n{fines}"
        await update.message.reply_text(msg, reply_markup=inline_menu())
    elif text == "👥 Игроки банка":
        top = sorted(users.values(), key=lambda x: x["money"], reverse=True)
        msg = "👥 Игроки банка:\n"
        for i, u in enumerate(top[:10], 1):
            msg += f"{i}. {u['name']} — {u['money']} ₽\n"
        await update.message.reply_text(msg, reply_markup=inline_menu())
    else:
        await update.message.reply_text("Не понял команду 🤷‍♂️", reply_markup=inline_menu())

async def inline_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = get_user(update.effective_user.id, update.effective_user.first_name + " " + (update.effective_user.last_name or ""))
    if query.data == "work":
        now = time.time()
        if now - user["last_work"] < 60:
            msg = "⏳ Смена ещё не закончилась"
        else:
            user["last_work"] = now
            pay_amount = random.randint(800, 1200)
            user["money"] += pay_amount
            msg = f"Получка: {pay_amount} ₽"
        msg += vit_check(user)
        await query.edit_message_text(msg + f"\nБаланс: {user['money']} ₽", reply_markup=inline_menu())
    elif query.data == "shop":
        if user["money"] < 500:
            await query.edit_message_text("❌ Недостаточно бабла для покупки!", reply_markup=inline_menu())
        else:
            user["money"] -= 500
            await query.edit_message_text("🏗 Куплено оборудование! -500 ₽", reply_markup=inline_menu())
    elif query.data == "deposit":
        gain = int(user["money"] * 0.1)
        user["money"] += gain
        await query.edit_message_text(f"🏦 Депозит +10% = {gain} ₽\nБаланс: {user['money']} ₽", reply_markup=inline_menu())
    elif query.data == "credit":
        user["money"] += 1000
        await query.edit_message_text(f"💳 Кредит +1000 ₽\nБаланс: {user['money']} ₽", reply_markup=inline_menu())
    elif query.data == "transfer":
        await query.edit_message_text("🔁 Для перевода используйте: /pay ID СУММА", reply_markup=inline_menu())

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("pay", pay))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply_text))
app.add_handler(CallbackQueryHandler(inline_callback))
print("Бот КаменскАвтодор запущен")
app.run_polling()