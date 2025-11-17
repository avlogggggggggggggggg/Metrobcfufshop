import json
import re

def analyze_file_structure(file_path):
    """Анализирует структуру файла и определяет паттерны данных"""
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = [line.strip() for line in file.readlines()]
    
    print("🔍 Анализ структуры файла...")
    
    # Собираем статистику по строкам
    skater_candidates = []
    element_candidates = []
    location_candidates = []
    score_candidates = []
    
    for i, line in enumerate(lines):
        if not line:
            continue
            
        # Кандидаты на данные фигуриста (содержат цифры и буквы в определенном порядке)
        parts = line.split()
        if len(parts) >= 5:
            # Проверяем различные паттерны
            if (parts[0].isdigit() and 
                len(parts[1]) > 2 and parts[1][0].isalpha() and
                len(parts[2]) > 2 and parts[2].isalpha() and
                len(parts[3]) in [2, 3] and parts[3].isalpha() and
                parts[4].isdigit()):
                skater_candidates.append((i, line))
                
            # Кандидаты на элементы (начинаются с цифры, содержат буквы и числа)
            elif (parts[0].isdigit() and 
                  any(c.isalpha() for c in parts[1]) and
                  re.match(r'^-?\d+\.?\d*$', parts[2].replace(',', '.'))):
                element_candidates.append((i, line))
            
            # Кандидаты на location (не начинаются с цифры, не технические данные)
            elif (not parts[0].isdigit() and
                  not any(word in line for word in ['Компоненты', 'Старт.', 'Всероссийские', 'Выполненные', 'элементы'])) and len(line) > 10:
                location_candidates.append((i, line))
            
            # Кандидаты на базовые оценки (два числа через пробел)
            elif re.match(r'^\d+\.\d+\s+\d+\.\d+$', line):
                score_candidates.append((i, line))
    
    print(f"Найдено кандидатов:")
    print(f"  - Фигуристы: {len(skater_candidates)}")
    print(f"  - Элементы: {len(element_candidates)}")
    print(f"  - Location: {len(location_candidates)}")
    print(f"  - Баллы: {len(score_candidates)}")
    
    # Показываем примеры
    if skater_candidates:
        print("\nПримеры данных фигуристов:")
        for i, (idx, line) in enumerate(skater_candidates[:3]):
            print(f"  {i+1}. Строка {idx}: {line}")
    
    return skater_candidates, element_candidates, location_candidates, score_candidates

def parse_universal(file_path):
    """Универсальный парсер для любых данных"""
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = [line.strip() for line in file.readlines()]
    
    skaters = []
    current_skater = None
    elements_collected = 0
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        if not line:
            i += 1
            continue
            
        parts = line.split()
        
        # Определяем строку с данными фигуриста
        if (len(parts) >= 9 and 
            parts[0].isdigit() and 
            parts[1][0].isalpha() and 
            parts[4].isdigit() and
            '.' in parts[5]):
            
            try:
                # Пытаемся извлечь данные
                rank = int(parts[0])
                name = parts[1]
                surname = parts[2]
                region = parts[3]
                start_number = int(parts[4])
                
                # Ищем числа с плавающей точкой (они могут быть в разных позициях)
                scores = []
                for part in parts[5:]:
                    if re.match(r'^-?\d+\.\d+$', part):
                        scores.append(float(part))
                
                if len(scores) >= 3:
                    total_score = scores[0]
                    technical_score = scores[1]
                    component_score = scores[2]
                    deductions = scores[3] if len(scores) > 3 else 0.0
                    
                    current_skater = {
                        "rank": rank,
                        "name": name,
                        "surname": surname,
                        "location": "",
                        "region": region,
                        "startNumber": start_number,
                        "totalScore": total_score,
                        "technicalScore": technical_score,
                        "componentScore": component_score,
                        "deductions": deductions,
                        "elements": [],
                        "baseTechnicalScore": 0.0
                    }
                    
                    # Ищем location в следующих строках
                    j = i + 1
                    while j < min(i + 5, len(lines)):
                        if (lines[j] and 
                            not lines[j][0].isdigit() and
                            not any(word in lines[j] for word in ['ofnI', 'Компоненты', 'элементы']) and
                            len(lines[j]) > 10):
                            current_skater["location"] = lines[j]
                            break
                        j += 1
                    
                    elements_collected = 0
                    print(f"✅ Найден фигурист: {name} {surname}")
            
            except (ValueError, IndexError) as e:
                print(f"❌ Ошибка парсинга: {line} - {e}")
        
        # Собираем элементы для текущего фигуриста
        elif (current_skater and 
              elements_collected < 7 and
              len(parts) >= 4 and
              parts[0].isdigit() and
              any(c.isalpha() for c in parts[1])):
            
            try:
                element_num = int(parts[0])
                element_name = parts[1]
                element_bv = float(parts[2].replace(',', '.'))
                element_goe = float(parts[3].replace(',', '.'))
                
                # Ищем итоговую оценку (последнее число в строке)
                element_total = 0.0
                for part in reversed(parts):
                    if re.match(r'^-?\d+\.?\d*$', part.replace(',', '.')):
                        element_total = float(part.replace(',', '.'))
                        break
                
                current_skater["elements"].append({
                    "number": element_num,
                    "name": element_name,
                    "bv": element_bv,
                    "goe": element_goe,
                    "total": element_total
                })
                
                elements_collected += 1
                
                if elements_collected == 7:
                    print(f"   📊 Собрано 7 элементов для {current_skater['name']}")
            
            except (ValueError, IndexError) as e:
                print(f"❌ Ошибка элемента: {line} - {e}")
        
        # Ищем базовую техническую оценку
        elif (current_skater and 
              elements_collected == 7 and
              re.match(r'^\d+\.\d+\s+\d+\.\d+$', line)):
            
            try:
                base_parts = line.split()
                current_skater["baseTechnicalScore"] = float(base_parts[0])
                
                # Сохраняем фигуриста
                skaters.append(current_skater)
                current_skater = None
                elements_collected = 0
                print(f"   💾 Сохранен фигурист")
            
            except (ValueError, IndexError) as e:
                print(f"❌ Ошибка базовой оценки: {line} - {e}")
        
        i += 1
    
    # Если остался незавершенный фигурист
    if current_skater and len(current_skater["elements"]) == 7:
        skaters.append(current_skater)
    
    return skaters

def parse_fallback(file_path):
    """Резервный метод парсинга - ищет блоки данных"""
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Разделяем на блоки по заголовкам или пустым строкам
    blocks = re.split(r'\n\s*\n', content)
    
    skaters = []
    
    for block in blocks:
        lines = [line.strip() for line in block.split('\n') if line.strip()]
        
        if len(lines) < 5:
            continue
            
        # Ищем блок с данными фигуриста
        skater_data = parse_block(lines)
        if skater_data:
            skaters.append(skater_data)
    
    return skaters

def parse_block(lines):
    """Парсит блок строк как данные одного фигуриста"""
    if len(lines) < 8:  # Минимум: заголовок + 7 элементов
        return None
    
    # Первая строка - данные фигуриста
    header_line = lines[0]
    parts = header_line.split()
    
    if len(parts) < 9:
        return None
    
    try:
        rank = int(parts[0])
        name = parts[1]
        surname = parts[2]
        region = parts[3]
        start_number = int(parts[4])
        
        # Ищем оценки
        scores = []
        for part in parts[5:]:
            if re.match(r'^-?\d+\.\d+$', part):
                scores.append(float(part))
        
        if len(scores) < 3:
            return None
            
        total_score = scores[0]
        technical_score = scores[1]
        component_score = scores[2]
        deductions = scores[3] if len(scores) > 3 else 0.0
        
        # Вторая строка - location
        location = lines[1] if len(lines) > 1 else ""
        
        # Следующие 7 строк - элементы
        elements = []
        for i in range(2, min(9, len(lines))):
            elem_parts = lines[i].split()
            if (len(elem_parts) >= 4 and 
                elem_parts[0].isdigit() and
                any(c.isalpha() for c in elem_parts[1])):
                
                try:
                    element_num = int(elem_parts[0])
                    element_name = elem_parts[1]
                    element_bv = float(elem_parts[2].replace(',', '.'))
                    element_goe = float(elem_parts[3].replace(',', '.'))
                    
                    # Ищем total
                    element_total = 0.0
                    for part in reversed(elem_parts):
                        if re.match(r'^-?\d+\.?\d*$', part.replace(',', '.')):
                            element_total = float(part.replace(',', '.'))
                            break
                    
                    elements.append({
                        "number": element_num,
                        "name": element_name,
                        "bv": element_bv,
                        "goe": element_goe,
                        "total": element_total
                    })
                except (ValueError, IndexError):
                    continue
        
        if len(elements) == 7:
            return {
                "rank": rank,
                "name": name,
                "surname": surname,
                "location": location,
                "region": region,
                "startNumber": start_number,
                "totalScore": total_score,
                "technicalScore": technical_score,
                "componentScore": component_score,
                "deductions": deductions,
                "elements": elements,
                "baseTechnicalScore": 0.0  # Будем искать отдельно
            }
    
    except (ValueError, IndexError):
        return None
    
    return None

def save_to_json(data, output_file):
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    input_file = "debug_lines.txt"
    output_file = "skaters_data.json"
    
    # Анализируем структуру
    skater_candidates, element_candidates, location_candidates, score_candidates = analyze_file_structure(input_file)
    
    if not skater_candidates:
        print("❌ Не найдено данных фигуристов. Файл может иметь неожиданный формат.")
        return
    
    print("\n🔄 Запуск универсального парсера...")
    
    # Пробуем основной парсер
    skaters_data = parse_universal(input_file)
    
    # Если не сработал, пробуем резервный
    if not skaters_data:
        print("🔄 Основной парсер не сработал, пробуем резервный...")
        skaters_data = parse_fallback(input_file)
    
    if skaters_data:
        # Сортируем по рангу
        skaters_data.sort(key=lambda x: x['rank'])
        
        # Сохраняем в JSON
        save_to_json(skaters_data, output_file)
        
        print(f"\n✅ Успешно обработано {len(skaters_data)} фигуристов")
        print(f"💾 Данные сохранены в файл: {output_file}")
        
        # Выводим статистику
        print(f"\n📊 Статистика:")
        for skater in skaters_data[:5]:  # Показываем первые 5
            print(f"  Ранг {skater['rank']}: {skater['name']} {skater['surname']} - {skater['totalScore']}")
        
        if len(skaters_data) > 5:
            print(f"  ... и еще {len(skaters_data) - 5} фигуристов")
    else:
        print("❌ Не удалось извлечь данные. Возможно, формат файла сильно отличается от ожидаемого.")

if __name__ == "__main__":
    main()