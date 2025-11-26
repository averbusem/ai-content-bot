import logging

from aiogram import types, Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards import (
    nko_data_empty_keyboard,
    nko_data_exists_keyboard,
    back_to_menu_keyboard,
    nko_forms_keyboard,
    nko_skip_keyboard,
    main_menu_keyboard,
)
from src.bot.states import NKODataStates
from src.services.nko import NKOService


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


def _build_forms_display(forms: list[str]) -> list[str]:
    display = []
    for form in forms:
        display.append(NKO_FORMS.get(form, f"✏️ {form}"))
    return display


def _prepare_nko_payload(data: dict) -> dict:
    name = data.get("name")
    activity = data.get("activity")
    forms = data.get("forms")

    if not name or not activity:
        raise ValueError("Заполните название и деятельность организации.")

    if not isinstance(forms, list) or not forms:
        raise ValueError("Выберите хотя бы одну форму деятельности.")

    payload = {
        "name": name,
        "activity": activity,
        "forms": forms,
    }

    region = data.get("region")
    if region:
        payload["region"] = region

    email = data.get("email")
    if email:
        payload["email"] = email

    website = data.get("website")
    if website:
        payload["website"] = website

    return payload


def _detect_validation_field(error_text: str) -> str | None:
    lowered = error_text.lower()
    if "email" in lowered:
        return "email"
    if "website" in lowered or "url" in lowered:
        return "website"
    return None


def _format_confirmation_text(data: dict) -> str:
    text = (
        "✅ <b>Данные успешно сохранены!</b>\n\n"
        f"<b>Название:</b> {data.get('name')}\n"
        f"<b>Деятельность:</b> {data.get('activity')}\n"
        f"<b>Формы деятельности:</b>\n"
    )

    for form in _build_forms_display(data.get("forms", [])):
        text += f"  • {form}\n"

    region = data.get("region")
    if region:
        text += f"\n<b>Регион работы:</b> {region}\n"

    email = data.get("email")
    if email:
        text += f"<b>Email:</b> {email}\n"

    website = data.get("website")
    if website:
        text += f"<b>Веб-сайт:</b> {website}\n"

    return text


async def _save_nko_data(
    state: FSMContext,
    session: AsyncSession,
    user_id: int,
) -> dict:
    data = await state.get_data()
    payload = _prepare_nko_payload(data)

    service = NKOService(session=session)
    saved = await service.save_data(user_id=user_id, data=payload)

    # сохраняем актуальные данные в payload из модели (если нужно)
    if saved and hasattr(saved, "name"):
        payload["name"] = saved.name
        payload["activity"] = saved.activity
        payload["forms"] = saved.forms or payload["forms"]

        if getattr(saved, "region", None) is not None:
            payload["region"] = saved.region
        else:
            payload.pop("region", None)

        if getattr(saved, "email", None) is not None:
            payload["email"] = saved.email
        else:
            payload.pop("email", None)

        if getattr(saved, "website", None) is not None:
            payload["website"] = saved.website
        else:
            payload.pop("website", None)

    await state.clear()
    return payload


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
        text += "<b>Формы деятельности:</b>\n"
        for form in _build_forms_display(forms if isinstance(forms, list) else [forms]):
            text += f"  • {form}\n"

    region = data.get("region")
    if region:
        text += f"<b>Регион работы:</b> {region}\n"

    email = data.get("email")
    if email:
        text += f"<b>Email:</b> {email}\n"

    website = data.get("website")
    if website:
        text += f"<b>Веб-сайт:</b> {website}\n"

    return text


@router.callback_query(F.data == "main_menu:nko_data")
async def nko_data_menu_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
):
    await state.set_state(NKODataStates.nko_menu)
    user_id = callback.from_user.id
    service = NKOService(session=session)

    try:
        data = await service.get_data(user_id)

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
        "📝 <b>Вопрос 1/6: Название организации</b>\n\n"
        "Как называется ваша некоммерческая организация?",
        reply_markup=back_to_menu_keyboard(),
    )


@router.callback_query(F.data == "nko_menu:edit_data")
async def nko_edit_data_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(NKODataStates.name)
    await callback.answer()
    return await callback.message.edit_text(
        "📝 <b>Вопрос 1/6: Название организации</b>\n\n"
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
        "📝 <b>Вопрос 2/6: Деятельность НКО</b>\n\n"
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

    data = await state.get_data()
    selected_forms = data.get("forms_selected", [])

    return await message.answer(
        "✅ Деятельность сохранена!\n\n"
        "📝 <b>Вопрос 3/6: Формы деятельности</b>\n\n"
        "Выберите формы деятельности вашей организации "
        "(можно выбрать несколько и добавить другие формы деятельности):",
        reply_markup=nko_forms_keyboard(selected_forms),
    )


@router.callback_query(F.data.startswith("forms:"), NKODataStates.forms)
async def nko_forms_toggle_handler(callback: types.CallbackQuery, state: FSMContext):
    form_key = callback.data.split(":")[1]

    data = await state.get_data()
    selected_forms = data.get("forms_selected", []).copy()
    forms_values = data.get("forms", []).copy()

    if form_key == "other":
        await state.set_state(NKODataStates.forms_other)
        await state.update_data(forms_selected=selected_forms)
        await callback.answer()
        return await callback.message.edit_text(
            "📝 <b>Вопрос 3/6: Формы деятельности</b>\n\n"
            "Вы указали 'Другое'. Опишите, пожалуйста, какие ещё формы деятельности есть у вашей организации:",
            reply_markup=back_to_menu_keyboard(),
        )

    selected_text = NKO_FORMS.get(form_key, "")
    was_selected = form_key in selected_forms

    if was_selected:
        selected_forms.remove(form_key)
        if form_key in forms_values:
            forms_values.remove(form_key)
        action = "удалена"
    else:
        selected_forms.append(form_key)
        if form_key not in forms_values:
            forms_values.append(form_key)
        action = "добавлена"

    await state.update_data(forms_selected=selected_forms, forms=forms_values)
    await callback.answer(f"{selected_text} {action}")

    return await callback.message.edit_reply_markup(
        reply_markup=nko_forms_keyboard(selected_forms)
    )


@router.message(NKODataStates.forms_other)
async def nko_forms_other_handler(message: types.Message, state: FSMContext):
    other_text = message.text.strip()

    if not other_text:
        return await message.answer(
            "❌ Описание не может быть пустым. Пожалуйста, опишите другие формы деятельности:"
        )

    data = await state.get_data()
    selected_forms = data.get("forms_selected", []).copy()
    forms_values = data.get("forms", []).copy()
    previous_other = data.get("forms_other_value")

    if previous_other and previous_other in forms_values:
        forms_values.remove(previous_other)

    if "other" not in selected_forms:
        selected_forms.append("other")

    forms_values.append(other_text)

    await state.update_data(
        forms_selected=selected_forms,
        forms=forms_values,
        forms_other_value=other_text,
    )
    await state.set_state(NKODataStates.forms)

    return await message.answer(
        f"✅ Добавлено: {other_text}\n\n"
        "📝 <b>Вопрос 3/6: Формы деятельности</b>\n\n"
        "Выберите формы деятельности вашей организации (можно выбрать несколько):",
        reply_markup=nko_forms_keyboard(selected_forms),
    )


@router.callback_query(F.data == "nko_forms:next", NKODataStates.forms)
async def nko_forms_next_handler(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected_forms = data.get("forms_selected", [])

    if not selected_forms:
        await callback.answer(
            "Выберите хотя бы одну форму деятельности!", show_alert=True
        )
        return

    await state.set_state(NKODataStates.region)
    await callback.answer()

    return await callback.message.edit_text(
        "✅ Формы деятельности сохранены!\n\n"
        "📝 <b>Вопрос 4/6: Регион работы</b>\n\n"
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
    await state.set_state(NKODataStates.email)

    return await message.answer(
        "✅ Регион сохранён!\n\n"
        "📝 <b>Вопрос 5/6: Email</b>\n\n"
        "Укажите email вашей организации или нажмите '⏭️ Пропустить'.",
        reply_markup=nko_skip_keyboard(),
    )


@router.callback_query(F.data == "nko_skip:skip", NKODataStates.region)
async def nko_region_skip_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(region=None)
    await state.set_state(NKODataStates.email)
    await callback.answer()

    return await callback.message.edit_text(
        "⏭️ Регион пропущен\n\n"
        "📝 <b>Вопрос 5/6: Email</b>\n\n"
        "Укажите email вашей организации или нажмите '⏭️ Пропустить'.",
        reply_markup=nko_skip_keyboard(),
    )


@router.message(NKODataStates.email)
async def nko_email_handler(message: types.Message, state: FSMContext):
    email = message.text.strip()

    if not email:
        return await message.answer(
            "❌ Email не может быть пустым. Введите email или нажмите '⏭️ Пропустить':",
            reply_markup=nko_skip_keyboard(),
        )

    await state.update_data(email=email)
    await state.set_state(NKODataStates.website)

    return await message.answer(
        "✅ Email сохранён!\n\n"
        "📝 <b>Вопрос 6/6: Веб-сайт</b>\n\n"
        "Укажите сайт вашей организации или нажмите '⏭️ Пропустить'.",
        reply_markup=nko_skip_keyboard(),
    )


@router.callback_query(F.data == "nko_skip:skip", NKODataStates.email)
async def nko_email_skip_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(email=None)
    await state.set_state(NKODataStates.website)
    await callback.answer()

    return await callback.message.edit_text(
        "⏭️ Email пропущен\n\n"
        "📝 <b>Вопрос 6/6: Веб-сайт</b>\n\n"
        "Укажите сайт вашей организации или нажмите '⏭️ Пропустить'.",
        reply_markup=nko_skip_keyboard(),
    )


@router.message(NKODataStates.website)
async def nko_website_handler(
    message: types.Message,
    state: FSMContext,
    session: AsyncSession,
):
    website = message.text.strip()

    if not website:
        return await message.answer(
            "❌ Сайт не может быть пустым. Введите сайт или нажмите '⏭️ Пропустить':",
            reply_markup=nko_skip_keyboard(),
        )

    await state.update_data(website=website)

    user_id = message.from_user.id

    try:
        payload = await _save_nko_data(state, session, user_id)
    except ValueError as exc:
        logger.warning("Ошибка валидации данных НКО: %s", exc)
        field = _detect_validation_field(str(exc))
        if field == "email":
            await state.update_data(email=None)
            await state.set_state(NKODataStates.email)
            return await message.answer(
                f"❌ {exc}\n\nВведите корректный email или нажмите '⏭️ Пропустить'.",
                reply_markup=nko_skip_keyboard(),
            )
        if field == "website":
            await state.update_data(website=None)
            await state.set_state(NKODataStates.website)
            return await message.answer(
                f"❌ {exc}\n\nВведите корректный сайт или нажмите '⏭️ Пропустить'.",
                reply_markup=nko_skip_keyboard(),
            )
        return await message.answer(f"❌ {exc}", reply_markup=nko_skip_keyboard())
    except Exception:
        logger.exception("Не удалось сохранить данные НКО для пользователя %s", user_id)
        return await message.answer(
            "❌ Произошла ошибка при сохранении данных. Попробуйте позже.",
            reply_markup=back_to_menu_keyboard(),
        )

    return await message.answer(
        _format_confirmation_text(payload),
        reply_markup=main_menu_keyboard(),
    )


@router.callback_query(F.data == "nko_skip:skip", NKODataStates.website)
async def nko_website_skip_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
):
    await state.update_data(website=None)
    user_id = callback.from_user.id

    try:
        payload = await _save_nko_data(state, session, user_id)
    except ValueError as exc:
        logger.warning("Ошибка валидации данных НКО: %s", exc)
        error_text = str(exc)
        field = _detect_validation_field(error_text)
        await callback.answer(error_text, show_alert=True)

        if field == "email":
            await state.update_data(email=None)
            await state.set_state(NKODataStates.email)
            return await callback.message.edit_text(
                f"❌ {error_text}\n\nВведите корректный email или нажмите '⏭️ Пропустить'.",
                reply_markup=nko_skip_keyboard(),
            )

        if field == "website":
            await state.set_state(NKODataStates.website)
            return await callback.message.edit_text(
                f"❌ {error_text}\n\nВведите корректный сайт или нажмите '⏭️ Пропустить'.",
                reply_markup=nko_skip_keyboard(),
            )
        return
    except Exception:
        logger.exception("Не удалось сохранить данные НКО для пользователя %s", user_id)
        await callback.answer(
            "Произошла ошибка при сохранении данных.", show_alert=True
        )
        return await callback.message.edit_text(
            "❌ Произошла ошибка при сохранении данных.",
            reply_markup=back_to_menu_keyboard(),
        )

    await callback.answer()

    try:
        return await callback.message.edit_text(
            _format_confirmation_text(payload),
            reply_markup=main_menu_keyboard(),
        )
    except TelegramBadRequest as e:
        logger.debug(f"Failed to edit message, sending new one: {e}")
        return await callback.message.answer(
            _format_confirmation_text(payload),
            reply_markup=main_menu_keyboard(),
        )


@router.callback_query(F.data == "nko_menu:delete_data")
async def nko_delete_data_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
):
    user_id = callback.from_user.id
    service = NKOService(session=session)

    try:
        deleted = await service.delete_data(user_id)
        if deleted:
            await callback.answer("Данные успешно удалены!")
        else:
            await callback.answer("Данных не найдено.", show_alert=True)
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
