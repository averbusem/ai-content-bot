import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from src.ai.ai_manager import AIManager


async def test_text_generation():
    """Тест генерации текста"""
    print("\n" + "="*60)
    print("ТЕСТ 1: Генерация свободного текста поста")
    print("="*60)

    ai_manager = AIManager(
        gigachat_client_id=os.getenv("GIGACHAT_CLIENT_ID"),
        gigachat_client_secret=os.getenv("GIGACHAT_CLIENT_SECRET"),
        salute_client_id=os.getenv("SALUTE_CLIENT_ID"),
        salute_client_secret=os.getenv("SALUTE_CLIENT_SECRET"),
        gigachat_model=os.getenv("GIGACHAT_MODEL", "GigaChat"),
        salute_scope=os.getenv("SALUTE_SCOPE", "SALUTE_SPEECH_PERS")
    )

    ngo_info = {
        "name": "Благотворительная организация 'Ночлежка'",
        "description": "Помощь людям без определенного места жительства",
        "activities": "Предоставление горячих обедов, ночлега, социальное сопровождение",
        "target_audience": "Люди без определенного места жительства",
        "values": "Достоинство, уважение, помощь каждому"
    }

    ai_manager.set_user_ngo_info(user_id=1, ngo_info=ngo_info)

    try:
        # Тест 1: Свободный текст
        print("\nГенерируем пост о благотворительной акции...")
        post = await ai_manager.generate_free_text_post(
            user_id=1,
            user_idea="Мы провели акцию по раздаче тёплых вещей. Собрали 150 курток и 200 пар обуви. Всё раздали нуждающимся.",
            style="разговорный"
        )
        print("\n📝 РЕЗУЛЬТАТ:")
        print(post)
        print("\n✅ Тест пройден!")

    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()


async def test_structured_post():
    """Тест структурированного поста"""
    print("\n" + "="*60)
    print("ТЕСТ 2: Генерация структурированного поста (анонс события)")
    print("="*60)

    ai_manager = AIManager(
        gigachat_client_id=os.getenv("GIGACHAT_CLIENT_ID"),
        gigachat_client_secret=os.getenv("GIGACHAT_CLIENT_SECRET"),
        salute_client_id=os.getenv("SALUTE_CLIENT_ID"),
        salute_client_secret=os.getenv("SALUTE_CLIENT_SECRET"),
        salute_scope=os.getenv("SALUTE_SCOPE", "SALUTE_SPEECH_PERS")
    )

    ngo_info = {
        "name": "Экологическое движение 'Зелёный мир'",
        "description": "Защита окружающей среды и экологическое просвещение",
        "activities": "Субботники, посадка деревьев, экологические уроки"
    }

    ai_manager.set_user_ngo_info(user_id=2, ngo_info=ngo_info)

    try:
        print("\nГенерируем анонс субботника...")
        post = await ai_manager.generate_structured_post(
            user_id=2,
            event_type="Экологический субботник",
            date="15 ноября 2025, 10:00",
            location="Парк 'Сокольники', центральный вход",
            participants="Все желающие, семьи с детьми",
            details="Приносите перчатки и хорошее настроение! Мешки для мусора предоставим. После субботника - чай и печенье.",
            style="дружелюбный разговорный"
        )
        print("\n📝 РЕЗУЛЬТАТ:")
        print(post)
        print("\n✅ Тест пройден!")

    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()


async def test_text_editing():
    """Тест редактирования текста"""
    print("\n" + "="*60)
    print("ТЕСТ 3: Редактирование текста")
    print("="*60)

    ai_manager = AIManager(
        gigachat_client_id=os.getenv("GIGACHAT_CLIENT_ID"),
        gigachat_client_secret=os.getenv("GIGACHAT_CLIENT_SECRET"),
        salute_client_id=os.getenv("SALUTE_CLIENT_ID"),
        salute_client_secret=os.getenv("SALUTE_CLIENT_SECRET"),
        salute_scope=os.getenv("SALUTE_SCOPE", "SALUTE_SPEECH_PERS")
    )

    try:
        text_to_edit = """
        Мы провили акцыю помощи. Было много людий. 
        Раздали вещей и еду всем. Все были довольны очень.
        Спасибо валантёрам за памощь.
        """

        print("\nИсходный текст:")
        print(text_to_edit)
        print("\nРедактируем...")

        result = await ai_manager.edit_text(
            text=text_to_edit,
            edit_focus="все аспекты"
        )

        print("\n📝 ОТРЕДАКТИРОВАННЫЙ ТЕКСТ:")
        print(result["edited_text"])

        print("\n🔍 НАЙДЕННЫЕ ОШИБКИ:")
        for error in result["errors"]:
            print(f"  • {error}")

        print("\n💡 РЕКОМЕНДАЦИИ:")
        for rec in result["recommendations"]:
            print(f"  • {rec}")

        print("\n✅ Тест пройден!")

    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()


async def test_content_plan():
    """Тест создания контент-плана"""
    print("\n" + "="*60)
    print("ТЕСТ 4: Создание контент-плана")
    print("="*60)

    ai_manager = AIManager(
        gigachat_client_id=os.getenv("GIGACHAT_CLIENT_ID"),
        gigachat_client_secret=os.getenv("GIGACHAT_CLIENT_SECRET"),
        salute_client_id=os.getenv("SALUTE_CLIENT_ID"),
        salute_client_secret=os.getenv("SALUTE_CLIENT_SECRET"),
        salute_scope=os.getenv("SALUTE_SCOPE", "SALUTE_SPEECH_PERS")
    )

    ngo_info = {
        "name": "Фонд помощи детям 'Счастливое детство'",
        "description": "Поддержка детей из малообеспеченных семей",
        "activities": "Образовательные программы, благотворительные концерты, помощь школьным принадлежностями"
    }

    ai_manager.set_user_ngo_info(user_id=3, ngo_info=ngo_info)

    try:
        print("\nСоздаём контент-план на 2 недели (3 поста в неделю)...")
        plan = await ai_manager.generate_content_plan(
            user_id=3,
            duration_days=14,
            posts_per_week=3,
            preferences="Больше историй детей, меньше просьб о донатах"
        )
        print("\n📅 КОНТЕНТ-ПЛАН:")
        print(plan)
        print("\n✅ Тест пройден!")

    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()


async def test_image_generation():
    """Тест генерации изображений"""
    print("\n" + "="*60)
    print("ТЕСТ 5: Генерация изображения")
    print("="*60)

    ai_manager = AIManager(
        gigachat_client_id=os.getenv("GIGACHAT_CLIENT_ID"),
        gigachat_client_secret=os.getenv("GIGACHAT_CLIENT_SECRET"),
        salute_client_id=os.getenv("SALUTE_CLIENT_ID"),
        salute_client_secret=os.getenv("SALUTE_CLIENT_SECRET")
    )

    try:
        print("\nГенерируем изображение...")
        prompt = "Волонтёры помогают пожилым людям, добрая атмосфера, реалистичный стиль, тёплые цвета"

        image_bytes = await ai_manager.generate_image(
            prompt=prompt,
            width=1024,
            height=1024
        )

        # Сохраняем изображение
        output_path = Path("test_output")
        output_path.mkdir(exist_ok=True)

        image_file = output_path / "generated_image.jpg"
        with open(image_file, "wb") as f:
            f.write(image_bytes)

        print(f"\n✅ Изображение сохранено: {image_file}")
        print(f"   Размер: {len(image_bytes)} байт")
        print("\n✅ Тест пройден!")

    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()


async def test_voice_transcription():
    """Тест транскрибации голоса"""
    print("\n" + "="*60)
    print("ТЕСТ 6: Транскрибация голосового сообщения")
    print("="*60)

    ai_manager = AIManager(
        gigachat_client_id=os.getenv("GIGACHAT_CLIENT_ID"),
        gigachat_client_secret=os.getenv("GIGACHAT_CLIENT_SECRET"),
        salute_client_id=os.getenv("SALUTE_CLIENT_ID"),
        salute_client_secret=os.getenv("SALUTE_CLIENT_SECRET"),
        gigachat_model=os.getenv("GIGACHAT_MODEL", "GigaChat"),
        salute_scope=os.getenv("SALUTE_SCOPE", "SALUTE_SPEECH_PERS")
    )

    try:
        audio_file = Path("test_output/test_audio.ogg")

        if audio_file.exists():
            print(f"\nТранскрибируем файл: {audio_file}")

            # Проверяем токен
            print("Проверяем аутентификацию...")
            await ai_manager.salute_speech._ensure_token()
            print(f"✅ Токен получен: {ai_manager.salute_speech.access_token[:20]}...")

            text = await ai_manager.transcribe_voice_file(str(audio_file))
            print("\n📝 РАСПОЗНАННЫЙ ТЕКСТ:")
            print(text)
            print("\n✅ Тест пройден!")
        else:
            print(f"\n⏭️  Файл не найден, пропускаем тест")
            print("   Тест можно будет выполнить позже с реальным аудио")

    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Главная функция для запуска всех тестов"""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*15 + "ТЕСТИРОВАНИЕ AI МОДЕЛЕЙ" + " "*20 + "║")
    print("╚" + "="*58 + "╝")

    # Проверяем наличие необходимых переменных окружения
    required_vars = [
        "GIGACHAT_CLIENT_ID",
        "GIGACHAT_CLIENT_SECRET",
        "SALUTE_CLIENT_ID",
        "SALUTE_CLIENT_SECRET"
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print("\n❌ ОШИБКА: Не установлены переменные окружения:")
        for var in missing_vars:
            print(f"   • {var}")
        print("\nУстановите их в файле .env")
        return

    # Запускаем тесты
    tests = [
        ("Генерация свободного текста", test_text_generation),
        ("Структурированный пост", test_structured_post),
        ("Редактирование текста", test_text_editing),
        ("Контент-план", test_content_plan),
        ("Генерация изображения", test_image_generation),
        ("Транскрибация голоса", test_voice_transcription),
    ]

    print("\n📋 Будет выполнено тестов: {}".format(len(tests)))
    print("\n" + "-"*60)

    for test_name, test_func in tests:
        try:
            await test_func()
        except KeyboardInterrupt:
            print("\n\n⚠️  Тестирование прервано пользователем")
            break
        except Exception as e:
            print(f"\n❌ Неожиданная ошибка в тесте '{test_name}': {e}")

        # Небольшая пауза между тестами
        await asyncio.sleep(1)

    print("\n" + "="*60)
    print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("="*60 + "\n")


# if __name__ == "__main__":
#     # Запускаем тесты
#     asyncio.run(main())

asyncio.run(test_voice_transcription())