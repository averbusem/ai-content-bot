from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext

from src.bot.keyboards import nko_data_empty_keyboard, nko_data_exists_keyboard, back_to_menu_keyboard
from src.bot.states import NKODataStates
from src.services.nko_service import nko_service


router = Router()


def format_nko_data(data: dict) -> str:
    text = "📋 <b>Данные об НКО:</b>\n\n"

    name = data.get("name")
    if name:
        text += f"<b>Название:</b> {name}\n"

    activity = data.get("activity")
    if activity:
        text += f"<b>Деятельность:</b> {activity}\n"

    forms = data.get("forms")
    if forms:
        if isinstance(forms, list):
            text += f"<b>Формы деятельности:</b> {', '.join(forms)}\n"
        else:
            text += f"<b>Формы деятельности:</b> {forms}\n"

    region = data.get("region")
    if region:
        text += f"<b>Регион работы:</b> {region}\n"

    contacts = data.get("contacts")
    if contacts:
        text += f"<b>Контакты:</b> {contacts}\n"

    return text


@router.callback_query(F.data == "main_menu:nko_data")
async def nko_data_menu_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(NKODataStates.nko_menu)
    user_id = callback.from_user.id
    
    try:
        data = await nko_service.get_nko_data(user_id)
        
        if data:
            text = format_nko_data(data)
            await callback.answer()
            return await callback.message.edit_text(
                text,
                reply_markup=nko_data_exists_keyboard()
            )
        else:
            await callback.answer()
            return await callback.message.edit_text(
                "⚙️ <b>Рассказать об НКО</b>\n\n"
                "Чтобы я мог создавать персонализированный контент для вашей организации, "
                "расскажите немного о ней.",
                reply_markup=nko_data_empty_keyboard()
            )
    except Exception as e:
        await callback.answer("Произошла ошибка. Попробуйте позже.", show_alert=True)
        return await callback.message.edit_text(
            "⚙️ Рассказать об НКО\n\n"
            "Произошла ошибка при загрузке данных.",
            reply_markup=back_to_menu_keyboard()
        )


@router.callback_query(F.data == "nko_menu:fill_data")
async def nko_fill_data_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    return await callback.message.edit_text(
        "📝 Заполнение данных\n\n"
        "Эта функция будет реализована в следующем шаге.",
        reply_markup=back_to_menu_keyboard()
    )


@router.callback_query(F.data == "nko_menu:edit_data")
async def nko_edit_data_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    return await callback.message.edit_text(
        "✏️ Изменение данных\n\n"
        "Эта функция будет реализована в следующем шаге.",
        reply_markup=back_to_menu_keyboard()
    )


@router.callback_query(F.data == "nko_menu:delete_data")
async def nko_delete_data_handler(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    
    try:
        await nko_service.delete_nko_data(user_id)
        await callback.answer("Данные успешно удалены!")
        return await callback.message.edit_text(
            "🗑️ <b>Данные удалены</b>\n\n"
            "Данные об НКО успешно удалены.",
            reply_markup=nko_data_empty_keyboard()
        )
    except Exception as e:
        await callback.answer("Произошла ошибка при удалении данных.", show_alert=True)
        return await callback.message.edit_text(
            "❌ Произошла ошибка при удалении данных.",
            reply_markup=back_to_menu_keyboard()
        )

