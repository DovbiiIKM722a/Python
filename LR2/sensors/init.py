# файл sensors/__init__.py
# забезпечує використання модулів у складі пакета sensors

# дозволяє отримувати доступ до функцій модуля stats_module напряму
# без необхідності використання import sensors.stats_module, а потім
# sensors.stats_module.get_average(...)
# або import sensors.stats_module as sm, а потім sm.get_average(...)
# також можна: from sensors import stats_module → stats_module.get_average(...)
# також можна: from sensors.stats_module import get_average → get_average(...)
from .stats_module import (
    get_average,
    get_min,
    get_max,
    get_median,
    find_jumps,
    show_table
)
# визначає, що можна імпортувати, а що - заборонено (службові елементи)
# при використанні варіанту конструкції: from sensors import *
__all__ = [
    "get_average",
    "get_min",
    "get_max",
    "get_median",
    "find_jumps",
    "show_table"
]