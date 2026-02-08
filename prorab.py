import random
import time
import asyncio
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

TOKEN = os.environ.get("TOKEN")  # Переменная среды

users = {}

# Магазин
shop_items = {
    "Асфальтовая катка": 1000,
    "Щебень премиум": 500,
    "Каска прораба": 200
}

# Твой Telegram ID для рассылок
OWNER_ID = 5775839902 # <-- Сюда вставь свой ID

# Получаем или создаем пользователя
def get_user(uid, full_name):
    if uid not in users:
        users[uid] = {"name": full_name, "money": 1000, "level": 1, "last_work": 0, "fines": []}
    return users[uid]

# Проверка Виталика
def vit_check(user):
    if random.random() < 0.15:
        fine = random.randint(300, 2500)
        reason = random.choice([
            "не тот шрифт в журнале",
            "погода не по ГОСТу",
            "лицо слишком довольное",
            "документы лежали криво",
            "подозрительно ровный асфальт"
        ])
        user["money"] -= fine
        user["fines"].append(f"-{fine} ₽ за '{reason}'")
        return f"\n🚨 Проверка! Инспектор Виталик.\nНарушение: {reason}\nШтраф: -{fine} ₽"
    return ""

# Нижние кнопки
reply_buttons = ReplyKeyboardMarkup([
    [KeyboardButton("💰 Моя получка"), KeyboardButton("🏗 Заработать получку")],
    [KeyboardButton("🆔 Мой ID"), KeyboardButton("👥 Игроки банка")],
    [KeyboardButton("📊 Профиль"), KeyboardButton("🔁 Перевести получку")]
], resize_keyboard=True)

# Главная inline-клавиатура
def inline_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Получка", callback_data="work")],
        [InlineKeyboardButton("🏗 Магазин", callback_data="shop")],
        [InlineKeyboardButton("🏦 Депозит", callback_data="deposit")],
        [InlineKeyboardButton("💳 Кредит", callback_data="credit")],
        [InlineKeyboardButton("🔁 Перевод", callback_data="transfer")]
    ])

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    full_name = update.effective_user.first_name + " " + (update.effective_user.last_name or "")
    user = get_user(update.effective_user.id, full_name)
    await update.message.reply_text(f"🏦 КаменскАвтодор АсфальтКапитал\nРаботяга: {user['name']}\nБаланс: {user['money']} ₽", reply_markup=inline_menu())
    await update.message.reply_text("Или используй нижние кнопки:", reply_markup=reply_buttons)

# Перевод
async def pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        parts = context.args
        if len(parts) < 3:
            await update.message.reply_text("❌ Формат перевода: /pay имя фамилия сумма", reply_markup=inline_menu())
            return
        name = parts[0]
        surname = parts[1]
        amount = int(parts[2])
        sender = get_user(update.effective_user.id, update.effective_user.first_name + " " + (update.effective_user.last_name or ""))
        # ищем получателя по имени+фамилии
        receiver = None
        for u in users.values():
            if u["name"] == f"{name} {surname}":
                receiver = u
                break
        if not receiver:
            await update.message.reply_text("❌ Игрок не найден", reply_markup=inline_menu())
            return
        if sender["money"] < amount:
            await update.message.reply_text("❌ Недостаточно средств", reply_markup=inline_menu())
            return
        sender["money"] -= amount
        receiver["money"] += amount
        await update.message.reply_text(f"✅ Вы перевели {amount} ₽ игроку {receiver['name']}", reply_markup=inline_menu())
        # уведомление получателю
        try:
            for uid, u in users.items():
                if u == receiver:
                    await context.bot.send_message(chat_id=uid, text=f"💸 Вам пришло {amount} ₽ от {sender['name']}!")
        except:
            pass
    except:
        await update.message.reply_text("❌ Формат перевода: /pay имя фамилия сумма", reply_markup=inline_menu())

# Обработка нижних кнопок
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
        await update.message.reply_text("Введите: /pay имя фамилия сумма", reply_markup=inline_menu())
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

# Магазин с выбором товара
async def shop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = get_user(update.effective_user.id, update.effective_user.first_name + " " + (update.effective_user.last_name or ""))
    if query.data.startswith("buy_"):
        item_name = query.data[4:]
        cost = shop_items[item_name]
        if user["money"] < cost:
            await query.edit_message_text(f"❌ Недостаточно средств для покупки {item_name}", reply_markup=inline_menu())
        else:
            user["money"] -= cost
            await query.edit_message_text(f"✅ Куплено {item_name} за {cost} ₽\nБаланс: {user['money']} ₽", reply_markup=inline_menu())
    else:
        # показать магазин
        buttons = [[InlineKeyboardButton(f"{name} — {price} ₽", callback_data=f"buy_{name}")] for name, price in shop_items.items()]
        buttons.append([InlineKeyboardButton("Назад", callback_data="back")])
        markup = InlineKeyboardMarkup(buttons)
        await query.edit_message_text("🏗 Магазин: выберите товар", reply_markup=markup)

# Inline callback
async def inline_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if