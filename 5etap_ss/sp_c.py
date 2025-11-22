import re
import json

def parse_skating_results(file_path):
    try:
        # Открываем файл с обработкой ошибок
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
    except FileNotFoundError:
        print(f"Ошибка: файл {file_path} не найден")
        return []
    except Exception as e:
        print(f"Ошибка при чтении файла: {str(e)}")
        return []

    results = []
    current_athlete = None
    elements = []
    base_technical_score = 0.0
    
    for line in lines:
        line = line.strip()
        
        # Ищем информацию о спортсмене
        if re.match(r'\d+ \w+ \w+, \d+ \d+\.\d+ \d+\.\d+ \d+\.\d+ 0\.00', line):
            if current_athlete:
                # Сохраняем предыдущего спортсмена
                current_athlete['elements'] = elements
                current_athlete['baseTechnicalScore'] = base_technical_score
                results.append(current_athlete)
                
            # Создаем нового спортсмена
            parts = line.split()
            try:
                current_athlete = {
                    "rank": int(parts[0]),
                    "name": parts[1],
                    "surname": parts[2],
                    "startNumber": int(parts[3]),
                    "totalScore": float(parts[4]),
                    "technicalScore": float(parts[5]),
                    "componentScore": float(parts[6]),
                    "deductions": float(parts[7]),
                    "elements": [],
                    "baseTechnicalScore": 0.0
                }
                elements = []
                base_technical_score = 0.0
            except (IndexError, ValueError):
                print("Ошибка формата данных спортсмена")
                current_athlete = None
                continue
            
        # Ищем местоположение и регион
        elif re.match(r'[^,]+, [^,]+', line):
            if current_athlete is not None:
                location_parts = line.split(',')
                if len(location_parts) >= 2:
                    current_athlete['location'] = location_parts[0].strip()
                    current_athlete['region'] = location_parts[1].strip()[:3]
                else:
                    print("Ошибка формата локации")
            
        # Ищем элементы программы
        elif re.match(r'\d+ \w+ \d+\.\d+ \d+\.\d+ \d+ \d+ \d+ \d+ \d+ \d+ \d+ \d+\.\d+', line):
            if current_athlete is not None:
                parts = line.split()
                try:
                    element = {
                        "number": int(parts[0]),
                        "name": parts[1],
                        "bv": float(parts[2]),
                        "goe": float(parts[3]),
                        "total": float(parts[-1])
                    }
                    elements.append(element)
                    base_technical_score += float(parts[2])
                except (IndexError, ValueError):
                    print("Ошибка формата элемента")
            
    # Добавляем последнего спортсмена
    if current_athlete is not None:
        current_athlete['elements'] = elements
        current_athlete['baseTechnicalScore'] = base_technical_score
        results.append(current_athlete)
        
    return results

def save_to_json(data, output_file):
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except IOError:
        print(f"Ошибка при записи в файл {output_file}")
    except Exception as e:
        print(f"Произошла ошибка при сохранении JSON: {str(e)}")

if __name__ == "__main__":
    input_file = 'debug_lines.txt'  # Укажите путь к вашему входному файлу
    output_file = 'results.json'    # Укажите путь к выходному файлу
    
    try:
        data = parse_sk