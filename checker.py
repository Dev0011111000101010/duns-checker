# checker.py
"""Проверка наличия компании FIBER LLC (Austin, TX) в D&B Business Directory."""

import sys
import time
sys.stdout.reconfigure(encoding="utf-8")

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

SEARCH_URL = (
    "https://www.dnb.com/site-search-results.html"
    "#BusinessDirectoryPageNumber=1"
    "&BusinessDirectorySearch=FIBER%20LLC%20TX"
    "&tab=Business%20Directory"
)

TARGET_NAME = "FIBER LLC"
TARGET_CITY = "Austin"
TARGET_STATE = "TX"


def check_fiber_llc() -> bool:
    """Открывает страницу D&B, читает таблицу и проверяет наличие целевой компании."""

    # ШАГ 1: Запуск Playwright
    print("🚀 [1] Запускаю Playwright...")
    p = sync_playwright().start()
    print("✅ [1] Playwright запущен")

    # ШАГ 2: Запуск браузера
    print("🌐 [2] Запускаю браузер Chromium (откроется окно)...")
    try:
        browser = p.chromium.launch(
            headless=False,
            args=["--start-maximized"],
        )
        print(f"✅ [2] Браузер запущен — версия: {browser.version}")
    except Exception as e:
        print(f"❌ [2] Браузер не запустился: {e}")
        p.stop()
        return False

    # ШАГ 3: Создание вкладки
    print("📄 [3] Создаю вкладку...")
    try:
        page = browser.new_page(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            )
        )
        print("✅ [3] Вкладка создана")
    except Exception as e:
        print(f"❌ [3] Не удалось создать вкладку: {e}")
        p.stop()
        return False

    # ШАГ 4: Проверка рендеринга на нейтральном сайте
    print("🔎 [4] Проверяю рендеринг на example.com...")
    try:
        page.goto("https://example.com", wait_until="domcontentloaded", timeout=10_000)
        page.screenshot(path="screenshot_verify.png")
        print(f"✅ [4] example.com загружен — «{page.title()}»")
    except Exception as e:
        print(f"❌ [4] Браузер не может открыть example.com: {e}")
        p.stop()
        return False

    # ШАГ 5: Переход на D&B
    print(f"🌐 [5] Открываю D&B Business Directory...")
    try:
        page.goto(SEARCH_URL, wait_until="domcontentloaded", timeout=15_000)
        print(f"✅ [5] Страница загружена — «{page.title()}»")
    except PlaywrightTimeoutError:
        print("❌ [5] Таймаут 15с — страница не ответила")
        page.screenshot(path="screenshot_step5_timeout.png")
        print("    💾 Скриншот: screenshot_step5_timeout.png")
        p.stop()
        return False
    except Exception as e:
        print(f"❌ [5] Ошибка загрузки: {e}")
        p.stop()
        return False

    # ШАГ 6: Ожидание таблицы
    print("⏳ [6] Жду таблицу результатов (5с)...")
    try:
        page.wait_for_selector("table tbody tr", timeout=5_000)
        print("✅ [6] Таблица найдена")
    except PlaywrightTimeoutError:
        print("❌ [6] Таблица не появилась за 5с")
        page.screenshot(path="screenshot_step6_no_table.png")
        print("    💾 Скриншот: screenshot_step6_no_table.png")
        raise RuntimeError("Таблица не появилась — проверьте доступ к сайту или селекторы.")

    # ШАГ 7: Чтение строк таблицы
    print("📋 [7] Читаю строки таблицы...")
    rows = page.locator("table tbody tr").all()
    print(f"✅ [7] Строк найдено: {len(rows)}")

    found_companies = []
    for i, row in enumerate(rows):
        cells = row.locator("td").all()
        if len(cells) < 4:
            print(f"    ⚠️  [строка {i+1}] пропущена — меньше 4 колонок")
            continue
        entry = {
            "name":          cells[0].text_content().strip(),
            "industry":      cells[1].text_content().strip(),
            "location_type": cells[2].text_content().strip(),
            "location":      cells[3].text_content().strip(),
        }
        found_companies.append(entry)
        print(f"    📌 [строка {i+1}] {entry['name']} | {entry['location']}")

    print("🔓 [8] Данные собраны. Браузер остаётся открытым.")

    # ── Вывод итогов ───────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  🔍 D&B Business Directory — поиск: FIBER LLC TX")
    print(f"{'='*60}")

    if not found_companies:
        print("  ❌ ОШИБКА: таблица загружена, но строк не обнаружено.")
        print("     Возможная причина: изменение структуры страницы.")
        print(f"{'='*60}\n")
        raise RuntimeError("Таблица пуста — ожидалась минимум 1 запись.")

    print(f"\n  📊 Найдено в таблице: {len(found_companies)} запись(ей)\n")
    for i, c in enumerate(found_companies, 1):
        print(f"  [{i}] {c['name']}")
        print(f"       Индустрия:  {c['industry']}")
        print(f"       Тип:        {c['location_type']}")
        print(f"       Локация:    {c['location']}")

    target_found = any(
        TARGET_NAME in c["name"]
        and TARGET_CITY in c["location"]
        and TARGET_STATE in c["location"]
        for c in found_companies
    )

    print(f"\n{'='*60}")
    if target_found:
        print(f"  ✅ FIBER LLC (Austin, TX) — ОБНАРУЖЕНА")
    else:
        print(f"  ❌ FIBER LLC (Austin, TX) — НЕ ОБНАРУЖЕНА")
        fiber_matches = [c for c in found_companies if TARGET_NAME in c["name"]]
        if fiber_matches:
            print(f"  ⚠️  Найдены записи с 'FIBER LLC', но не из Austin, TX:")
            for c in fiber_matches:
                print(f"      • {c['name']} — {c['location']}")
        else:
            print(f"  ℹ️  В таблице нет ни одной записи с '{TARGET_NAME}'")
    print(f"{'='*60}\n")

    print("⏳ Окно закроется через 3 секунды. Браузер остаётся открытым.")
    time.sleep(3)

    return target_found


if __name__ == "__main__":
    try:
        result = check_fiber_llc()
        sys.exit(0 if result else 1)
    except RuntimeError as e:
        print(f"\n  ❌ ОШИБКА: {e}\n")
        sys.exit(2)
