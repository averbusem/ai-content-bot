"""
Утилита для автоматической загрузки сертификатов МинЦифры
"""

import logging
from pathlib import Path
import requests

logger = logging.getLogger(__name__)

GIGACHAT_CERT_URL = "https://gu-st.ru/content/lending/russian_trusted_root_ca_pem.crt"
SALUTE_CERT_URL = "https://gu-st.ru/content/Other/doc/russian_trusted_root_ca.cer"

PROJECT_ROOT = Path(__file__).parent.parent
CERT_DIR = PROJECT_ROOT / "certificates"
GIGACHAT_CERT_PATH = CERT_DIR / "russian_trusted_root_ca_pem.crt"
SALUTE_CERT_PATH = CERT_DIR / "russian_trusted_root_ca.cer"


def setup_gigachat_certificate() -> bool:
    """Загрузка сертификата МинЦифры для Gigachat"""
    if GIGACHAT_CERT_PATH.exists():
        logger.info(f"Сертификат GigaChat уже установлен: {GIGACHAT_CERT_PATH}")
        return True

    try:
        CERT_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"Загрузка сертификата GigaChat из {GIGACHAT_CERT_URL}...")

        response = requests.get(GIGACHAT_CERT_URL, verify=False, timeout=30)
        response.raise_for_status()

        GIGACHAT_CERT_PATH.write_bytes(response.content)
        logger.info(f"Сертификат GigaChat успешно установлен: {GIGACHAT_CERT_PATH}")
        return True

    except Exception as e:
        logger.error(f"Ошибка загрузки сертификата GigaChat: {e}")
        logger.warning("GigaChat продолжит работу без проверки SSL")
        return False


def setup_salute_certificate() -> bool:
    """Загрузка сертификата МинЦифры для Salute"""
    if SALUTE_CERT_PATH.exists():
        logger.info(f"Сертификат Salute уже установлен: {SALUTE_CERT_PATH}")
        return True

    try:
        CERT_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"Загрузка сертификата Salute из {SALUTE_CERT_URL}...")

        response = requests.get(SALUTE_CERT_URL, verify=False, timeout=30)
        response.raise_for_status()

        SALUTE_CERT_PATH.write_bytes(response.content)
        logger.info(f"Сертификат Salute успешно установлен: {SALUTE_CERT_PATH}")
        return True

    except Exception as e:
        logger.error(f"Ошибка загрузки сертификата Salute: {e}")
        logger.warning("Salute продолжит работу без проверки SSL")
        return False


def setup_certificates():
    """Загрузка всех необходимых сертификатов"""
    gigachat_ok = setup_gigachat_certificate()
    salute_ok = setup_salute_certificate()

    if gigachat_ok and salute_ok:
        logger.info("Все сертификаты готовы к использованию")
    elif gigachat_ok or salute_ok:
        logger.warning(
            "Некоторые сертификаты не загружены, но приложение продолжит работу"
        )
    else:
        logger.warning("Сертификаты не загружены, будет использоваться verify=False")
