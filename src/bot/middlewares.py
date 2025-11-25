import logging
import time

from aiogram import BaseMiddleware, Bot, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey

from src.services.rate_limiter import rate_limiter
from src.bot.states import MainMenuStates
from src.config import settings


logger = logging.getLogger(__name__)


class RemoveLastKeyboardMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data: dict):
        state: FSMContext = data.get("state")
        data_state = await state.get_data()
        last_message_id = data_state.get("last_message_id")

        result = await handler(event, data)

        current_message_id = None
        if isinstance(result, types.Message):
            current_message_id = result.message_id
        elif isinstance(event, types.CallbackQuery):
            current_message_id = event.message.message_id

        if (
            last_message_id
            and current_message_id
            and last_message_id != current_message_id
        ):
            chat_id = (
                event.message.chat.id
                if isinstance(event, types.CallbackQuery)
                else event.chat.id
            )
            await _remove_keyboard(event.bot, chat_id, last_message_id)

        if state and current_message_id:
            logger.debug(f"Update last_message_id = {current_message_id}")
            await state.update_data(last_message_id=current_message_id)
        return result


async def _remove_keyboard(bot: Bot, chat_id: int, message_id: int) -> None:
    try:
        await bot.edit_message_reply_markup(
            chat_id=chat_id, message_id=message_id, reply_markup=None
        )
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            logger.debug(f"Keyboard already removed: {chat_id}:{message_id}")
            return
        logger.error(f"Error removing keyboard {chat_id}:{message_id}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error removing keyboard {chat_id}:{message_id}: {e}")


async def clear_initiator(chat_id: int):
    """Очистить статус инициатора для чата"""
    if not rate_limiter.redis_client:
        await rate_limiter.initialize()

    initiator_key = f"chat:{chat_id}:initiator"
    activity_key = f"chat:{chat_id}:initiator:last_activity"

    await rate_limiter.redis_client.delete(initiator_key)
    await rate_limiter.redis_client.delete(activity_key)


class GroupChatAccessMiddleware(BaseMiddleware):
    """
    Middleware для проверки прав доступа в групповых чатах.
    Блокирует callback_query и message от пользователей, которые не инициировали запрос.
    Использует Redis для хранения информации об инициаторе, привязанной к chat_id.
    """

    def __init__(self, storage=None):
        self.storage = storage

    async def __call__(self, handler, event, data: dict):
        state: FSMContext = data.get("state")

        user_id = None
        chat_id = None
        is_group_chat = False

        if isinstance(event, types.Message):
            user_id = event.from_user.id
            chat_id = event.chat.id
            is_group_chat = event.chat.type in ("group", "supergroup")
        elif isinstance(event, types.CallbackQuery):
            user_id = event.from_user.id
            chat_id = event.message.chat.id
            is_group_chat = event.message.chat.type in ("group", "supergroup")

        if not is_group_chat:
            return await handler(event, data)

        if not rate_limiter.redis_client:
            await rate_limiter.initialize()

        initiator_key = f"chat:{chat_id}:initiator"
        activity_key = f"chat:{chat_id}:initiator:last_activity"

        initiator_user_id_str = await rate_limiter.redis_client.get(initiator_key)
        initiator_user_id = (
            int(initiator_user_id_str) if initiator_user_id_str else None
        )

        if initiator_user_id is not None:
            last_activity_str = await rate_limiter.redis_client.get(activity_key)
            if last_activity_str:
                last_activity = float(last_activity_str)
                time_since_activity = time.time() - last_activity

                if time_since_activity > settings.INACTIVITY_TIMEOUT:
                    await clear_initiator(chat_id)
                    initiator_user_id = None
                    logger.debug(
                        f"Таймаут неактивности для чата {chat_id}, очищен статус инициатора"
                    )

        is_start_command = (
            isinstance(event, types.Message)
            and event.text
            and event.text.startswith("/use")
        )

        # Если это команда /use, проверяем, есть ли активный процесс у текущего инициатора
        if (
            is_start_command
            and initiator_user_id is not None
            and initiator_user_id != user_id
        ):
            if self.storage:
                try:
                    storage_key = StorageKey(
                        chat_id=chat_id, user_id=initiator_user_id, bot_id=event.bot.id
                    )
                    initiator_state = await self.storage.get_state(key=storage_key)

                    main_menu_state_str = str(MainMenuStates.main_menu)
                    is_active_process = (
                        initiator_state is not None
                        and str(initiator_state) != main_menu_state_str
                    )

                    if is_active_process:
                        if isinstance(event, types.CallbackQuery):
                            await event.answer(
                                "⏳ Другой пользователь сейчас использует бота. "
                                "Дождитесь завершения его запроса или попробуйте позже.",
                                show_alert=True,
                            )
                        elif isinstance(event, types.Message):
                            answer_msg = await event.answer(
                                "⏳ Другой пользователь сейчас использует бота. "
                                "Дождитесь завершения его запроса или попробуйте позже."
                            )
                            import asyncio

                            asyncio.create_task(
                                self._delete_message_after_delay(
                                    event.bot, chat_id, answer_msg.message_id, delay=5
                                )
                            )
                        return None
                except Exception as e:
                    logger.warning(f"Ошибка при проверке состояния инициатора: {e}")

        # Если это команда /use или инициатор еще не установлен, устанавливаем текущего пользователя как инициатора
        if is_start_command or initiator_user_id is None:
            await rate_limiter.redis_client.set(initiator_key, str(user_id))
            await rate_limiter.redis_client.expire(initiator_key, 180)

            await rate_limiter.redis_client.set(activity_key, str(time.time()))
            await rate_limiter.redis_client.expire(activity_key, 180)
            result = await handler(event, data)
            await self._check_and_clear_initiator_if_main_menu(chat_id, user_id, state)
            return result

        # Проверяем, что текущий пользователь - это инициатор
        if user_id != initiator_user_id:
            if isinstance(event, types.CallbackQuery):
                await event.answer(
                    "❌ Это не ваш запрос. Вы не можете использовать кнопки этого бота.",
                    show_alert=True,
                )
                return None

            return None

        await rate_limiter.redis_client.set(activity_key, str(time.time()))
        await rate_limiter.redis_client.expire(activity_key, 180)

        result = await handler(event, data)
        await self._check_and_clear_initiator_if_main_menu(chat_id, user_id, state)

        return result

    async def _check_and_clear_initiator_if_main_menu(
        self, chat_id: int, user_id: int, state: FSMContext
    ):
        """Проверяет, находится ли пользователь в главном меню, и очищает статус инициатора если да"""
        if not state or not self.storage:
            return

        try:
            current_state = await state.get_state()
            main_menu_state_str = str(MainMenuStates.main_menu)

            if current_state and str(current_state) == main_menu_state_str:
                await clear_initiator(chat_id)
                logger.debug(
                    f"Пользователь {user_id} в главном меню, очищен статус инициатора для чата {chat_id}"
                )
        except Exception as e:
            logger.warning(f"Ошибка при проверке состояния для очистки инициатора: {e}")

    async def _delete_message_after_delay(
        self, bot: Bot, chat_id: int, message_id: int, delay: int
    ):
        """Удаляет сообщение через указанное количество секунд"""
        import asyncio

        await asyncio.sleep(delay)
        try:
            await bot.delete_message(chat_id=chat_id, message_id=message_id)
        except Exception as e:
            logger.debug(f"Не удалось удалить сообщение {chat_id}:{message_id}: {e}")
