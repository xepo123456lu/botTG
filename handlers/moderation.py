import os
from dotenv import load_dotenv
from aiogram import Router, F
from aiogram.types import CallbackQuery
from database import update_user_status
from aiogram import Bot

load_dotenv()
BOT_TOKEN = os.getenv("API_TOKEN")

router = Router()


@router.callback_query(F.data.startswith("approve_"))
async def approve_user(callback: CallbackQuery):
    """Одобряет анкету пользователя"""
    try:
        user_id = int(callback.data.split("_")[1])
    except (ValueError, IndexError):
        await callback.answer("Ошибка: некорректный ID пользователя", show_alert=True)
        return

    # Обновляем статус в БД на 'approved'
    await update_user_status(user_id, "approved")

    # Уведомляем модератора
    await callback.answer("✅ Анкета одобрена!", show_alert=False)
    
    # Убираем кнопки из сообщения
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception as e:
        print(f"Ошибка при удалении кнопок: {e}")

    # Уведомляем пользователя о том, что его анкета одобрена
    bot = Bot(token=BOT_TOKEN)
    try:
        await bot.send_message(
            chat_id=user_id,
            text="🎉 Отлично! Твоя анкета прошла модерацию.\n"
                 "Теперь ты можешь искать подруг! 🌖"
        )
    except Exception as e:
        print(f"Ошибка при отправке сообщения пользователю {user_id}: {e}")


@router.callback_query(F.data.startswith("reject_"))
async def reject_user(callback: CallbackQuery):
    """Отклоняет анкету пользователя"""
    try:
        user_id = int(callback.data.split("_")[1])
    except (ValueError, IndexError):
        await callback.answer("Ошибка: некорректный ID пользователя", show_alert=True)
        return

    # Обновляем статус в БД на 'rejected'
    await update_user_status(user_id, "rejected")

    # Уведомляем модератора
    await callback.answer("❌ Анкета отклонена.", show_alert=False)
    
    # Убираем кнопки из сообщения
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception as e:
        print(f"Ошибка при удалении кнопок: {e}")

    # Уведомляем пользователя о том, что его анкета отклонена
    bot = Bot(token=BOT_TOKEN)
    try:
        await bot.send_message(
            chat_id=user_id,
            text="Что ты не понял из описания? Давай иди отсюда, доступ запрещен."
        )
    except Exception as e:
        print(f"Ошибка при отправке сообщения пользователю {user_id}: {e}")
