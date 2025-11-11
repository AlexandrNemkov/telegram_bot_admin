import asyncio
import base64
import logging
import os
from datetime import datetime, timedelta
from typing import Optional, Tuple

from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardRemove,
    InputMediaPhoto,
)
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

from database import Database

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ===== Простая обфускация токена (не безопасность, а скрытие) =====
def _xor_bytes(data: bytes, key: bytes) -> bytes:
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))

def _decrypt_token() -> str:
    # Токен из запроса пользователя:
    # 8269885977:AAHdF4_XwZSph_Fh5M2QSG8_mFHYzREhw0E
    # Держим его в обфусцированном виде
    key = b"\x13\x2A\x59\x07\xC3\x9D"
    part1_b64 = b"Qjg2OTg4NTk3Nzo"  # часть префикса
    part2_b64 = b"6QUFIZEY0X1hY1pTcGhfRmg1TTJRU0c4X21G"  # середина
    part3_b64 = b"SFk6UkVodzBF"  # окончание
    raw = base64.b64decode(part1_b64 + part2_b64 + part3_b64)
    token = _xor_bytes(raw, key).decode("utf-8")
    return token

# Состояния ConversationHandler
(
    ADD_BOT_WAIT_TOKEN,
    ADD_BOT_WAIT_USERNAME,
    BROADCAST_WAIT_TEXT,
    BROADCAST_WAIT_PHOTO,
    BROADCAST_WAIT_SCHEDULE,
    WELCOME_WAIT_CAPTION,
    WELCOME_WAIT_FILE,
) = range(7)

class AdminBot:
    def __init__(self):
        self.token = _decrypt_token()
        self.db = Database()

    # ===== Helpers =====
    def _ensure_owner(self, update: Update) -> int:
        tg_user = update.effective_user
        full_name = f"{tg_user.first_name or ''} {tg_user.last_name or ''}".strip()
        return self.db.upsert_system_user_from_telegram(tg_user.id, tg_user.username or "", full_name)

    async def _send_owner_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [InlineKeyboardButton("➕ Добавить своего бота", callback_data="add_bot")],
            [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
            [InlineKeyboardButton("📎 Приветственный файл", callback_data="welcome_file")],
        ]
        await update.message.reply_text("Выберите действие:", reply_markup=InlineKeyboardMarkup(keyboard))

    # ===== Commands =====
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        owner_id = self._ensure_owner(update)
        await update.message.reply_text(f"Админ-бот готов. Ваш ID: {owner_id}")
        await self._send_owner_menu(update, context)

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "Доступно:\n"
            "— Добавить своего бота (токен + username)\n"
            "— Смотреть базовую статистику подписчиков\n"
            "— Задать приветственный файл (file_id) и подпись"
        )

    async def on_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        data = query.data
        if data == "add_bot":
            await query.edit_message_text("Пришлите токен вашего бота:")
            return ADD_BOT_WAIT_TOKEN
        if data == "stats":
            owner_id = self._ensure_owner(update)
            # Подписчики
            total = self.db.get_total_subscribers_count(owner_id)
            day_ago = (datetime.now() - timedelta(days=1)).isoformat()
            week_ago = (datetime.now() - timedelta(days=7)).isoformat()
            new_24h = self.db.get_new_subscribers_count(owner_id, day_ago)
            new_7d = self.db.get_new_subscribers_count(owner_id, week_ago)
            text = (
                f"Подписчики\n"
                f"— Всего: {total}\n"
                f"— За 24ч: +{new_24h}\n"
                f"— За 7д: +{new_7d}\n"
            )
            await query.edit_message_text(text)
            return ConversationHandler.END
        if data == "welcome_file":
            await query.edit_message_text("Пришлите подпись (сообщение), отправляемую вместе с файлом при подписке:")
            return WELCOME_WAIT_CAPTION
        return ConversationHandler.END

    # ===== Add bot flow =====
    async def add_bot_token(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data["tmp_bot_token"] = update.message.text.strip()
        await update.message.reply_text("Теперь пришлите username бота (без @):")
        return ADD_BOT_WAIT_USERNAME

    async def add_bot_username(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        owner_id = self._ensure_owner(update)
        bot_token = context.user_data.pop("tmp_bot_token", "")
        bot_username = update.message.text.strip().lstrip("@")
        ok = self.db.update_user_bot_token(owner_id, bot_token, bot_username)
        if ok:
            await update.message.reply_text("Бот добавлен. Можно создавать рассылки.")
        else:
            await update.message.reply_text("Не удалось сохранить бота.")
        return ConversationHandler.END

    # ===== Broadcast flow =====
    async def broadcast_get_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data["bc_text"] = update.message.text or ""
        await update.message.reply_text(
            "Пришлите фото (как изображение), если нужно, либо отправьте '-' чтобы пропустить."
        )
        return BROADCAST_WAIT_PHOTO

    async def broadcast_get_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message.text and update.message.text.strip() == "-":
            context.user_data["bc_photo_file_id"] = None
        else:
            if not update.message.photo:
                await update.message.reply_text("Пришлите фото или '-' чтобы пропустить.")
                return BROADCAST_WAIT_PHOTO
            context.user_data["bc_photo_file_id"] = update.message.photo[-1].file_id
        await update.message.reply_text(
            "Когда отправить?\n"
            "— 'сейчас'\n"
            "— или укажите дату/время в формате YYYY-MM-DD HH:MM"
        )
        return BROADCAST_WAIT_SCHEDULE

    async def broadcast_get_schedule(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        owner_id = self._ensure_owner(update)
        schedule_str = update.message.text.strip().lower()
        text = context.user_data.pop("bc_text", "")
        photo_file_id = context.user_data.pop("bc_photo_file_id", None)
        scheduled_at = None
        if schedule_str != "сейчас":
            try:
                scheduled_at = datetime.strptime(schedule_str, "%Y-%m-%d %H:%M").isoformat(" ")
            except Exception:
                await update.message.reply_text("Неверный формат времени. Повторите команду /start и создайте заново.")
                return ConversationHandler.END
        campaign_id = self.db.create_campaign(owner_id, text, photo_file_id, scheduled_at)
        if scheduled_at:
            await update.message.reply_text(f"Кампания #{campaign_id} запланирована на {scheduled_at}.")
        else:
            await update.message.reply_text(f"Кампания #{campaign_id} поставлена в очередь и будет отправлена сейчас.")
        return ConversationHandler.END

    # ===== Welcome file flow =====
    async def welcome_caption(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data["welcome_caption"] = update.message.text or ""
        await update.message.reply_text("Пришлите файл (документ/фото), который будет отправляться при подписке.")
        return WELCOME_WAIT_FILE

    async def welcome_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        owner_id = self._ensure_owner(update)
        caption = context.user_data.pop("welcome_caption", "")
        file_id = None
        if update.message.document:
            file_id = update.message.document.file_id
        elif update.message.photo:
            file_id = update.message.photo[-1].file_id
        else:
            await update.message.reply_text("Нужно отправить документ или фото.")
            return WELCOME_WAIT_FILE
        self.db.update_user_welcome_file_id(owner_id, file_id, caption)
        await update.message.reply_text("Приветственный файл обновлён.")
        return ConversationHandler.END

    # ===== Scheduler =====
    async def _send_campaign(self, owner_id: int, campaign_id: int, text: Optional[str], photo_file_id: Optional[str]):
        try:
            # Получаем токен бота владельца
            settings = self.db.get_user_settings(owner_id)
            bot_token = settings.get("bot_token") or ""
            if not bot_token:
                await asyncio.sleep(0)  # yield
                self.db.mark_campaign_status(campaign_id, "failed")
                return
            # Получаем подписчиков
            users = self.db.get_users_for_bot(owner_id)
            import requests
            base_url = f"https://api.telegram.org/bot{bot_token}"
            sent = 0
            failed = 0
            for u in users:
                uid = u["id"]
                try:
                    if photo_file_id:
                        url = f"{base_url}/sendPhoto"
                        payload = {"chat_id": uid, "photo": photo_file_id}
                        if text:
                            payload["caption"] = text
                        r = requests.post(url, data=payload, timeout=20)
                    else:
                        url = f"{base_url}/sendMessage"
                        payload = {"chat_id": uid, "text": text or "", "parse_mode": "HTML"}
                        r = requests.post(url, json=payload, timeout=20)
                    ok = False
                    if r.status_code == 200:
                        resp = r.json()
                        ok = bool(resp.get("ok"))
                    if ok:
                        sent += 1
                        self.db.log_delivery(uid, owner_id, campaign_id, "success", None)
                    else:
                        failed += 1
                        self.db.log_delivery(uid, owner_id, campaign_id, "failed", r.text[:200])
                except Exception as e:
                    failed += 1
                    self.db.log_delivery(uid, owner_id, campaign_id, "failed", str(e)[:200])
                await asyncio.sleep(0)  # cooperative
            self.db.mark_campaign_status(campaign_id, "sent" if failed == 0 else "failed")
            logger.info(f"Campaign #{campaign_id} done: sent={sent}, failed={failed}")
        except Exception as e:
            logger.error(f"Campaign #{campaign_id} error: {e}")
            self.db.mark_campaign_status(campaign_id, "failed")

    async def scheduler_tick(self, context: ContextTypes.DEFAULT_TYPE):
        # Функционал рассылок отключён для админ-бота
        return

    # ===== Bootstrap =====
    def run(self):
        application: Application = ApplicationBuilder().token(self.token).build()

        # Conversation for add bot
        add_bot_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.on_button, pattern="^add_bot$")],
            states={
                ADD_BOT_WAIT_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.add_bot_token)],
                ADD_BOT_WAIT_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.add_bot_username)],
            },
            fallbacks=[CommandHandler("start", self.start)],
            map_to_parent={},
        )
        # Conversation for broadcast
        bc_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.on_button, pattern="^broadcast$")],
            states={
                BROADCAST_WAIT_TEXT: [MessageHandler(filters.ALL & ~filters.COMMAND, self.broadcast_get_text)],
                BROADCAST_WAIT_PHOTO: [MessageHandler((filters.PHOTO | filters.TEXT) & ~filters.COMMAND, self.broadcast_get_photo)],
                BROADCAST_WAIT_SCHEDULE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.broadcast_get_schedule)],
            },
            fallbacks=[CommandHandler("start", self.start)],
            map_to_parent={},
        )
        # Conversation for welcome file
        welcome_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.on_button, pattern="^welcome_file$")],
            states={
                WELCOME_WAIT_CAPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.welcome_caption)],
                WELCOME_WAIT_FILE: [MessageHandler((filters.DOCUMENT | filters.PHOTO) & ~filters.COMMAND, self.welcome_file)],
            },
            fallbacks=[CommandHandler("start", self.start)],
            map_to_parent={},
        )

        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("help", self.help))
        application.add_handler(CallbackQueryHandler(self.on_button, pattern="^(stats)$"))
        application.add_handler(add_bot_conv)
        # Рассылки отключены
        application.add_handler(welcome_conv)

        # Планировщик отключён для админ-бота

        logger.info("Admin bot started")
        application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    AdminBot().run()


