# install_autostart.py
"""Определяет папку автозагрузки текущего пользователя и создаёт ярлык для run.bat."""

import sys
sys.stdout.reconfigure(encoding="utf-8")

import os
import subprocess
from pathlib import Path


def main():
    # Текущий пользователь
    username = os.environ.get("USERNAME", "unknown")
    print(f"👤 Пользователь: {username}")

    # Папка автозагрузки
    appdata = os.environ.get("APPDATA")
    if not appdata:
        print("❌ Переменная окружения APPDATA не найдена")
        sys.exit(1)

    startup_dir = Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    print(f"📂 Папка автозагрузки: {startup_dir}")

    if not startup_dir.exists():
        print("❌ Папка автозагрузки не найдена")
        sys.exit(1)

    print(f"✅ Папка найдена")

    # Путь к run.bat
    project_dir = Path(__file__).parent.resolve()
    bat_path = project_dir / "run.bat"

    if not bat_path.exists():
        print(f"❌ Файл run.bat не найден: {bat_path}")
        sys.exit(1)

    print(f"📄 Лаунчер: {bat_path}")

    # Создаём .lnk ярлык через PowerShell
    shortcut_path = startup_dir / "DUNS Checker.lnk"
    ps_script = (
        f'$s = (New-Object -ComObject WScript.Shell).CreateShortcut("{shortcut_path}");'
        f'$s.TargetPath = "{bat_path}";'
        f'$s.WorkingDirectory = "{project_dir}";'
        f'$s.WindowStyle = 1;'
        f'$s.Save()'
    )

    if shortcut_path.exists():
        print(f"✅ Ярлык уже установлен: {shortcut_path}")
        return

    print(f"🔗 Создаю ярлык: {shortcut_path}")
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps_script],
        capture_output=True, text=True
    )

    if result.returncode != 0:
        print(f"❌ Ошибка PowerShell: {result.stderr.strip()}")
        sys.exit(1)

    if shortcut_path.exists():
        print(f"✅ Ярлык создан: {shortcut_path}")
        print(f"\n🚀 DUNS Checker будет запускаться автоматически при входе в Windows.")
    else:
        print("❌ Ярлык не был создан — проверьте права доступа")
        sys.exit(1)


if __name__ == "__main__":
    main()
