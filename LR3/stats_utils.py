import statistics
from typing import List, Optional, Dict, Any

def calculate_average(numbers: List[float]) -> Optional[float]:
    """Обчислює середнє арифметичне."""
    return round(statistics.mean(numbers), 2) if numbers else None

def find_minimum(numbers: List[float]) -> Optional[float]:
    """Знаходить мінімальне число у списку."""
    return min(numbers) if numbers else None

def find_maximum(numbers: List[float]) -> Optional[float]:
    """Знаходить максимальне число у списку."""
    return max(numbers) if numbers else None

def calculate_median(numbers: List[float]) -> Optional[float]:
    """Обчислює медіану."""
    return round(statistics.median(numbers), 2) if numbers else None

def find_anomalies(numbers: List[float], time_labels: List[str], limit: float) -> List[str]:
    """
    Знаходить різкі стрибки значень, що перевищують заданий ліміт.
    Повертає список часових міток.
    """
    detected_points = []
    for i in range(1, len(numbers)):
        diff = abs(numbers[i] - numbers[i - 1])
        if diff > limit:
            detected_points.append(time_labels[i])
    return detected_points

def show_data_table(label: str, dataset: Dict[str, float]) -> None:
    """Виводить вихідні дані у вигляді таблиці."""
    print(f"\nВихідні дані: {label}")
    print("+----------------------+-------------+")
    print(f"| {'Час':<20} | {label:<11} |")
    print("+----------------------+-------------+")
    for time_point, val in dataset.items():
        print(f"| {time_point:<20} | {val:<11} |")
    print("+----------------------+-------------+")

def display_stats(label: str, computed_data: Dict[str, Any]) -> None:
    """Виводить розраховані підсумки (статистику) у таблиці."""
    print(f"\nПідсумкова статистика: {label}")
    print("+----------------------+--------------------------------+")
    print(f"| {'Параметр':<20} | {'Результат':<30} |")
    print("+----------------------+--------------------------------+")
    
    for k, v in computed_data.items():
        # Форматування списків у рядок
        if isinstance(v, list):
            display_val = ", ".join(v) if v else "Без змін"
        else:
            display_val = str(v)
            
        print(f"| {k:<20} | {display_val:<30} |")
        
    print("+----------------------+--------------------------------+")