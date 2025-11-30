# stats_module.py
# Модуль із підпрограмами для статистичної обробки показників
# виконати імпорт модулів, які викорстовуються, наприклад:
import statistics

"""Повертає середнє значення."""
def get_average(values):
    average = sum(values) / len(values)
    return average

"""Повертає мінімальне значення."""
def get_min(values):
    minimum = min(values)
    return minimum

"""Повертає максимальне значення."""
def get_max(values):
    maximum = max(values) 
    return maximum

"""Повертає медіану."""
def get_median(values):
    median = statistics.median(values) 
    return median

"""Знаходить різкі перепади між сусідніми значеннями. Повертає список рядків із вказаними мітками часу та різницею."""  
def find_jumps(values, threshold):
    jumps = {"index": [], "value1": [], "value2": []}
    for i in range(0, len(values)-1):
        if abs(values[i+1] - values[i]) > threshold:
            jumps["index"].append(i)
            jumps["value1"].append(values[i])
            jumps["value2"].append(values[i+1])
    return jumps

"""Виводить таблицю значень."""
def show_table(data_dict, title):
    print (f"\nТаблиця показників: {title}")
    print ("Мітка часу | Значення")
    for time_label, value in data_dict[title].items():
        print (f"   {time_label}   \t |  {value}")
