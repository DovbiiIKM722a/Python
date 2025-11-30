# main.py
# Основна програма для обробки показників системи "розумний будинок"

import sensors.stats_module as sm # підключення модулю

### TODO: основну програму можна написати однією функцією main(), або окремі задачі розділити на окремі підпрограми, наприклад наступним чином:

def parse_input(input_str):
    data = input_str.split()
    dataFloat = []
    for value in data:
        dataFloat.append(float(value))
    return dataFloat

def create_data_dict(temp_list, hum_list, pres_list):
    data_dict = {
        "temperature": {},
        "humidity": {},
        "pressure": {}
    }
    for i in range(len(temp_list)):
        time = f"T{i+1}"
        data_dict["temperature"][time] = temp_list[i]
        data_dict["humidity"][time] = hum_list[i]
        data_dict["pressure"][time] = pres_list[i]

    return data_dict

def process_measurements(title, data_dict, threshold):
    print (f"=== Обробка показників для:{title}===")
    value = list(data_dict[title].values())
    sm.show_table(data_dict, title)
    avg = sm.get_average(value)
    print (f"Середні значення: {avg:.2f}")
    min = sm.get_min(value)
    print (f"Мінімальні значення: {min:.2f}")
    max = sm.get_max(value)
    print (f"Максимальні значення: {max:.2f}")
    med = sm.get_median(value)
    print (f"Медіанні значення: {med:.2f}")
    
    jumps = sm.find_jumps(value, threshold)
    if jumps["index"]:
        print("Виявлені стрибки:")
        for i in range(len(jumps["index"])):
            print(f"  Між T{jumps['index'][i]+1} і T{jumps['index'][i]+2}: "
                  f"{jumps['value1'][i]} → {jumps['value2'][i]}")
    else:
        print("Стрибків не виявлено.")

def main():
    print("=== Обробка показів системи 'Розумний будинок' ===")
    temperature_input = input("Введіть показники температури (через пробіл): ")
    humidity_input = input("Введіть показники вологості (через пробіл): ")
    pressure_input = input("Введіть показники тиску (через пробіл): ")
    temp_list = parse_input(temperature_input)
    hum_list = parse_input(humidity_input)
    pres_list = parse_input(pressure_input)
    data_dict = create_data_dict(temp_list, hum_list, pres_list)
    process_measurements("temperature", data_dict, threshold=7)
    process_measurements("humidity", data_dict, threshold=20)
    process_measurements("pressure", data_dict, threshold=5000)
    

if __name__ == "__main__":
    main()
