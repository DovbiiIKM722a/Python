from typing import List, Dict, Any
import statistics

# Пороги для виявлення "різких перепадів"
DEFAULT_THRESHOLDS = {
    "temperature": 7.0,   # градуси Цельсія
    "humidity": 20.0,     # відсоткові пункти (absolute)
    "pressure": 5000.0    # Паскалі
}


def get_average(values: List[int|float]) -> float | None:
    if not values:
        return None
    return round(statistics.mean(values), 2)


def get_min(values: List[int|float]) -> float | None:
    if not values:
        return None
    return min(values)


def get_max(values: List[int|float]) -> float | None:
    if not values:
        return None
    return max(values)


def get_median(values: List[int|float]) -> float | None:
    if not values:
        return None
    return round(statistics.median(values), 2)


def detect_jumps(values: List[int|float], timestamps: List[str], threshold: float) -> List[str]:
    """
    Повертає список timestamps (тої мітки часу, на якій стався перепад),
    коли різниця між сусідніми значеннями > threshold.
    Позначає timestamp з індексом i (тобто мітку другого елементу у парі),
    де abs(values[i] - values[i-1]) > threshold.
    """
    jumps: List[str] = []
    if not values or len(values) < 2:
        return jumps

    for i in range(1, len(values)):
        try:
            if abs(values[i] - values[i - 1]) > threshold:
                # Повертаємо timestamp де виявлено перепад (поточний)
                jumps.append(timestamps[i])
        except Exception:
            # у випадку невідповідних типів — пропускаємо
            continue
    return jumps


def compute_stats_for_parameter(
    timestamps: List[str],
    values: List[float|None],
    stats_to_compute: List[str],
    param_name: str,
    thresholds: dict | None = None
) -> Dict[str, Any]:
    """
    Проводить обчислення згідно списку stats_to_compute для одного параметра.
    stats_to_compute — список рядків: 'average','min','max','median','jumps'
    Повертає словник результатів.
    """
    if thresholds is None:
        thresholds = DEFAULT_THRESHOLDS

    res: Dict[str, Any] = {}
    # ensure numeric list
    numeric_values = [v for v in values if isinstance(v, (int, float))]

    for s in stats_to_compute:
        s = s.strip().lower()
        if s == "average":
            res["average"] = get_average(numeric_values)
        elif s == "min":
            res["min"] = get_min(numeric_values)
        elif s == "max":
            res["max"] = get_max(numeric_values)
        elif s == "median":
            res["median"] = get_median(numeric_values)
        elif s == "jumps":
            thr = thresholds.get(param_name, thresholds.get(param_name.lower(), DEFAULT_THRESHOLDS.get(param_name, 0)))
            res["jumps"] = detect_jumps(numeric_values, timestamps, thr)
    return res