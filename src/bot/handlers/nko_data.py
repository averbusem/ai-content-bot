import logging

from aiogram import types, Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext

from src.bot.keyboards import (
    nko_data_empty_keyboard,
    nko_data_exists_keyboard,
    back_to_menu_keyboard,
    nko_forms_keyboard,
    nko_skip_keyboard,
    main_menu_keyboard,
)
from src.bot.states import NKODataStates
from src.services.nko_service import nko_service


NKO_FORMS = {
    "projects": "🎯 Проекты",
    "events": "🎪 Мероприятия",
    "donations": "💰 Сбор пожертвований",
    "volunteering": "🤝 Волонтёрство",
    "education": "📚 Образование",
    "direct_help": "🏥 Адресная помощь",
    "info_work": "📢 Информационная работа",
    "other": "✏️ Другое",
}


router = Router()
logger = logging.getLogger(__name__)


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
            forms_display = []
            for form_key in forms:
                if form_key == "other":
                    other_text = data.get("forms_other", "")
                    if other_text:
                        forms_display.append(f"✏️ Другое: {other_text}")
                    else:
                        forms_display.append("✏️ Другое")
                else:
                    forms_display.append(NKO_FORMS.get(form_key, form_key))

            text += "<b>Формы деятельности:</b>\n"
            for form in forms_display:
                text += f"  • {form}\n"
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
                text, reply_markup=nko_data_exists_keyboard()
            )
        else:
            await callback.answer()
            return await callback.message.edit_text(
                "⚙️ <b>Рассказать об НКО</b>\n\n"
                "Чтобы я мог создавать персонализированный контент для вашей организации, "
                "расскажите немного о ней.",
                reply_markup=nko_data_empty_keyboard(),
            )
    except Exception:
        await callback.answer("Произошла ошибка. Попробуйте позже.", show_alert=True)
        return await callback.message.edit_text(
            "⚙️ Рассказать об НКО\n\nПроизошла ошибка при загрузке данных.",
            reply_markup=back_to_menu_keyboard(),
        )


@router.callback_query(F.data == "nko_menu:fill_data")
async def nko_fill_data_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(NKODataStates.name)
    await callback.answer()
    return await callback.message.edit_text(
        "📝 <b>Вопрос 1/5: Название организации</b>\n\n"
        "Как называется ваша некоммерческая организация?",
        reply_markup=back_to_menu_keyboard(),
    )


@router.callback_query(F.data == "nko_menu:edit_data")
async def nko_edit_data_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(NKODataStates.name)
    await callback.answer()
    return await callback.message.edit_text(
        "📝 <b>Вопрос 1/5: Название организации</b>\n\n"
        "Как называется ваша некоммерческая организация?",
        reply_markup=back_to_menu_keyboard(),
    )


@router.message(NKODataStates.name)
async def nko_name_handler(message: types.Message, state: FSMContext):
    name = message.text.strip()

    if not name:
        return await message.answer(
            "❌ Название организации не может быть пустым. Пожалуйста, введите название:"
        )

    await state.update_data(name=name)
    await state.set_state(NKODataStates.activity)

    return await message.answer(
        "✅ Название сохранено!\n\n"
        "📝 <b>Вопрос 2/5: Деятельность НКО</b>\n\n"
        "Опишите, чем занимается ваша организация?",
        reply_markup=back_to_menu_keyboard(),
    )


@router.message(NKODataStates.activity)
async def nko_activity_handler(message: types.Message, state: FSMContext):
    activity = message.text.strip()

    if not activity:
        return await message.answer(
            "❌ Описание деятельности не может быть пустым. Пожалуйста, опишите деятельность:"
        )

    await state.update_data(activity=activity)
    await state.set_state(NKODataStates.forms)

    selected_forms = await state.get_data()
    forms_list = selected_forms.get("forms", [])

    return await message.answer(
        "✅ Деятельность сохранена!\n\n"
        "📝 <b>Вопрос 3/5: Формы деятельности</b>\n\n"
        "Выберите формы деятельности вашей организации "
        "(можно выбрать несколько и добавить другие формы деятельности):",
        reply_markup=nko_forms_keyboard(forms_list),
    )


@router.callback_query(F.data.startswith("forms:"), NKODataStates.forms)
async def nko_forms_toggle_handler(callback: types.CallbackQuery, state: FSMContext):
    form_key = callback.data.split(":")[1]

    data = await state.get_data()
    forms_list = data.get("forms", [])

    if form_key == "other":
        await state.set_state(NKODataStates.forms_other)
        await callback.answer()
        return await callback.message.edit_text(
            "📝 <b>Вопрос 3/5: Формы деятельности</b>\n\n"
            "Вы указали 'Другое'. Опишите, пожалуйста, какие ещё формы деятельности есть у вашей организации:",
            reply_markup=back_to_menu_keyboard(),
        )

    selected_text = NKO_FORMS.get(form_key, "")
    was_selected = form_key in forms_list

    if was_selected:
        forms_list.remove(form_key)
        action = "удалена"
    else:
        forms_list.append(form_key)
        action = "добавлена"

    await state.update_data(forms=forms_list)
    await callback.answer(f"{selected_text} {action}")

    return await callback.message.edit_reply_markup(
        reply_markup=nko_forms_keyboard(forms_list)
    )


@router.message(NKODataStates.forms_other)
async def nko_forms_other_handler(message: types.Message, state: FSMContext):
    other_text = message.text.strip()

    if not other_text:
        return await message.answer(
            "❌ Описание не может быть пустым. Пожалуйста, опишите другие формы деятельности:"
        )

    data = await state.get_data()
    forms_list = data.get("forms", [])

    if "other" not in forms_list:
        forms_list.append("other")

    await state.update_data(forms=forms_list, forms_other=other_text)
    await state.set_state(NKODataStates.forms)

    return await message.answer(
        f"✅ Добавлено: {other_text}\n\n"
        "📝 <b>Вопрос 3/5: Формы деятельности</b>\n\n"
        "Выберите формы деятельности вашей организации (можно выбрать несколько):",
        reply_markup=nko_forms_keyboard(forms_list),
    )


@router.callback_query(F.data == "nko_forms:next", NKODataStates.forms)
async def nko_forms_next_handler(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    forms_list = data.get("forms", [])

    if not forms_list:
        await callback.answer(
            "Выберите хотя бы одну форму деятельности!", show_alert=True
        )
        return

    await state.set_state(NKODataStates.region)
    await callback.answer()

    return await callback.message.edit_text(
        "✅ Формы деятельности сохранены!\n\n"
        "📝 <b>Вопрос 4/5: Регион работы</b>\n\n"
        "В каком регионе работает ваша организация?",
        reply_markup=nko_skip_keyboard(),
    )


@router.message(NKODataStates.region)
async def nko_region_handler(message: types.Message, state: FSMContext):
    region = message.text.strip()

    if not region:
        return await message.answer(
            "❌ Регион не может быть пустым. Введите регион или нажмите '⏭️ Пропустить':",
            reply_markup=nko_skip_keyboard(),
        )

    await state.update_data(region=region)
    await state.set_state(NKODataStates.contacts)

    return await message.answer(
        "✅ Регион сохранён!\n\n"
        "📝 <b>Вопрос 5/5: Контакты</b>\n\n"
        "Укажите контактную информацию (телефон, email, сайт и т.д.):\n\n"
        "Всё в одном сообщении",
        reply_markup=nko_skip_keyboard(),
    )


@router.callback_query(F.data == "nko_skip:skip", NKODataStates.region)
async def nko_region_skip_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(region=None)
    await state.set_state(NKODataStates.contacts)
    await callback.answer()

    return await callback.message.edit_text(
        "⏭️ Регион пропущен\n\n"
        "📝 <b>Вопрос 5/5: Контакты</b>\n\n"
        "Укажите контактную информацию (телефон, email, сайт и т.д.):",
        reply_markup=nko_skip_keyboard(),
    )


@router.message(NKODataStates.contacts)
async def nko_contacts_handler(message: types.Message, state: FSMContext):
    contacts = message.text.strip()

    if not contacts:
        return await message.answer(
            "❌ Контакты не могут быть пустыми. Введите контакты или нажмите '⏭️ Пропустить':",
            reply_markup=nko_skip_keyboard(),
        )

    await state.update_data(contacts=contacts)

    data = await state.get_data()
    await state.clear()

    user_id = message.from_user.id
    await nko_service.save_nko_data(user_id, data)

    forms_display = []
    forms_list = data.get("forms", [])
    for form_key in forms_list:
        if form_key == "other":
            other_text = data.get("forms_other", "")
            forms_display.append(f"✏️ Другое: {other_text}")
        else:
            forms_display.append(NKO_FORMS.get(form_key, form_key))

    confirmation_text = (
        "✅ <b>Данные успешно сохранены!</b>\n\n"
        f"<b>Название:</b> {data.get('name')}\n"
        f"<b>Деятельность:</b> {data.get('activity')}\n"
        f"<b>Формы деятельности:</b>\n"
    )

    for form in forms_display:
        confirmation_text += f"  • {form}\n"

    if data.get("region"):
        confirmation_text += f"\n<b>Регион работы:</b> {data.get('region')}\n"

    if data.get("contacts"):
        confirmation_text += f"<b>Контакты:</b> {data.get('contacts')}\n"

    return await message.answer(confirmation_text, reply_markup=main_menu_keyboard())


@router.callback_query(F.data == "nko_skip:skip", NKODataStates.contacts)
async def nko_contacts_skip_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(contacts=None)

    data = await state.get_data()
    await state.clear()

    user_id = callback.from_user.id
    await nko_service.save_nko_data(user_id, data)

    forms_display = []
    forms_list = data.get("forms", [])
    for form_key in forms_list:
        if form_key == "other":
            other_text = data.get("forms_other", "")
            forms_display.append(f"✏️ Другое: {other_text}")
        else:
            forms_display.append(NKO_FORMS.get(form_key, form_key))

    confirmation_text = (
        "✅ <b>Данные успешно сохранены!</b>\n\n"
        f"<b>Название:</b> {data.get('name')}\n"
        f"<b>Деятельность:</b> {data.get('activity')}\n"
        f"<b>Формы деятельности:</b>\n"
    )

    for form in forms_display:
        confirmation_text += f"  • {form}\n"

    if data.get("region"):
        confirmation_text += f"\n<b>Регион работы:</b> {data.get('region')}\n"

    confirmation_text += "\n⏭️ Контакты пропущены"

    await callback.answer()

    try:
        return await callback.message.edit_text(
            confirmation_text, reply_markup=main_menu_keyboard()
        )
    except TelegramBadRequest as e:
        logger.debug(f"Failed to edit message, sending new one: {e}")
        return await callback.message.answer(
            confirmation_text, reply_markup=main_menu_keyboard()
        )


@router.callback_query(F.data == "nko_menu:delete_data")
async def nko_delete_data_handler(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id

    try:
        await nko_service.delete_nko_data(user_id)
        await callback.answer("Данные успешно удалены!")
        return await callback.message.edit_text(
            "🗑️ <b>Данные удалены</b>\n\nДанные об НКО успешно удалены.",
            reply_markup=nko_data_empty_keyboard(),
        )
    except Exception:
        await callback.answer("Произошла ошибка при удалении данных.", show_alert=True)
        return await callback.message.edit_text(
            "❌ Произошла ошибка при удалении данных.",
            reply_markup=back_to_menu_keyboard(),
        )
