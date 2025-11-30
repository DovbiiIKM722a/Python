import csv
import json
import sys
import argparse
import stats_utils as su
try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        print("Помилка: Не знайдено бібліотеку для роботи з TOML.")
        print("Встановіть її командою: pip install tomli")
        sys.exit(1)

# Базові ліміти для датчиків (якщо не задані інакше)
STANDARD_LIMITS = {
    "temperature": 7,
    "humidity": 20,
    "pressure": 5000
}

def get_cli_args():
    """Обробляє аргументи, передані при запуску скрипта."""
    parser = argparse.ArgumentParser(description="Утиліта для аналізу показників сенсорів.")
    
    # Позиційний аргумент для файлу
    parser.add_argument("filepath", nargs="?", help="Шлях до вхідного CSV файлу")
    
    # Прапорці для налаштування порогів (використовуємо -H для вологості)
    parser.add_argument("-t", "--temp_limit", type=float, help="Ліміт стрибка температури")
    parser.add_argument("-H", "--hum_limit", type=float, help="Ліміт стрибка вологості")
    parser.add_argument("-p", "--press_limit", type=float, help="Ліміт стрибка тиску")
    
    return parser.parse_args()

def load_csv_data(path):
    """Читає CSV файл та структурує дані."""
    parsed_data = {"temperature": {}, "humidity": {}, "pressure": {}}
    try:
        with open(path, newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                ts = row["timestamp"]
                parsed_data["temperature"][ts] = float(row["temperature"])
                parsed_data["humidity"][ts] = float(row["humidity"])
                parsed_data["pressure"][ts] = float(row["pressure"])
        return parsed_data
    except FileNotFoundError:
        print(f"Помилка: Файл '{path}' відсутній.")
        return None
    except KeyError as e:
        print(f"Помилка структури CSV: Не знайдено колонку {e}. Перевірте заголовки у файлі.")
        return None
    except Exception as err:
        print(f"Критична помилка читання: {err}")
        return None

def load_configuration(config_path):
    """Завантажує налаштування з TOML файлу."""
    app_settings = {}
    analysis_rules = {}

    try:
        with open(config_path, "rb") as cfg_file:
            toml_data = tomllib.load(cfg_file)

        for section, data in toml_data.items():
            if section == "App":
                app_settings = data
            else:
                # TOML автоматично повертає список, не треба робити split
                analysis_rules[section] = data.get("stats", [])
                
        return app_settings, analysis_rules

    except FileNotFoundError:
        print(f"Увага: Конфіг '{config_path}' не знайдено.")
        return {}, {}
    except Exception as e:
        print(f"Помилка парсингу TOML: {e}")
        sys.exit(1)

def determine_source_file(arg_path, config_path):
    """
    Вибирає файл даних за пріоритетом:
    1. Аргумент командного рядка
    2. Файл конфігурації
    3. Ручне введення
    """
    if arg_path:
        return arg_path
    
    if config_path:
        return config_path

    # Інтерактивний режим
    user_input = input("Вкажіть шлях до CSV файлу даних: ").strip()
    # Прибираємо зайві лапки, якщо користувач скопіював шлях
    return user_input.replace('"', '').replace("'", "")

def resolve_limits(args):
    """Формує актуальні пороги чутливості."""
    current_limits = STANDARD_LIMITS.copy()
    
    if args.temp_limit is not None:
        current_limits["temperature"] = args.temp_limit
    if args.hum_limit is not None:
        current_limits["humidity"] = args.hum_limit
    if args.press_limit is not None:
        current_limits["pressure"] = args.press_limit
        
    return current_limits

def main():
    # 1. Отримання аргументів CLI
    cli_args = get_cli_args()

    # 2. Завантаження конфігурації TOML
    app_conf, rules_conf = load_configuration("config.toml")
    
    # 3. Визначення файлу для обробки
    target_file = determine_source_file(cli_args.filepath, app_conf.get("filename"))
    print(f"Обробляється файл: {target_file}")

    # 4. Встановлення порогів
    active_limits = resolve_limits(cli_args)

    # 5. Читання даних
    measurements = load_csv_data(target_file)
    if measurements is None:
        return
    
    final_report = {}

    # 6. Основний цикл обробки
    for category, series in measurements.items():
        if not series:
            continue

        time_keys = list(series.keys())
        data_values = list(series.values())
        final_report[category] = {}

        # Вивід сирих даних
        su.show_data_table(category, series)

        # Розрахунки згідно правил з TOML
        if category in rules_conf:
            required_stats = rules_conf[category]
            
            for stat_type in required_stats:
                if stat_type == "average":
                    final_report[category]["average"] = su.calculate_average(data_values)
                elif stat_type == "min":
                    final_report[category]["min"] = su.find_minimum(data_values)
                elif stat_type == "max":
                    final_report[category]["max"] = su.find_maximum(data_values)
                elif stat_type == "median":
                    final_report[category]["median"] = su.calculate_median(data_values)
                elif stat_type == "jumps":
                    limit = active_limits.get(category, 0)
                    final_report[category]["jumps"] = su.find_anomalies(data_values, time_keys, limit)
            
            # Вивід результатів розрахунків
            su.display_stats(category, final_report[category])

    # 7. Збереження звіту
    try:
        with open("results.json", "w", encoding="utf-8") as out_file:
            json.dump(final_report, out_file, ensure_ascii=False, indent=4)
        print("\nЗвіт успішно збережено у 'results.json'")
    except Exception as ex:
        print(f"Не вдалося зберегти звіт: {ex}")

if __name__ == "__main__":
    main()
