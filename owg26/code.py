import pdfplumber
import re
import json
import os

def parse_all_athletes_with_variable_elements(pdf_path):
    """Парсит всех спортсменов с переменным количеством элементов (1-16)"""
    results = []
    
    print("Читаю PDF файл...")
    with pdfplumber.open(pdf_path) as pdf:
        # Собираем весь текст из PDF
        full_text = ""
        for page_num, page in enumerate(pdf.pages):
            print(f"Обрабатываю страницу {page_num + 1}")
            text = page.extract_text()
            if text:
                full_text += text + "\n"
    
    print(f"Общий размер текста: {len(full_text)} символов")
    
    # Разбиваем на строки
    lines = full_text.split('\n')
    print(f"Всего строк: {len(lines)}")
    
    # Сохраняем для отладки
    with open('debug_lines.txt', 'w', encoding='utf-8') as f:
        for i, line in enumerate(lines):
            f.write(f"{i:3d}: {line}\n")
    
    # Ищем всех спортсменов
    i = 0
    athlete_count = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Ищем шаблон: цифра пробел цифра (место и стартовый номер)
        if re.match(r'^\d+\s+\d+$', line):
            # Проверяем следующие строки на наличие имени и региона
            if (i + 2 < len(lines) and 
                re.match(r'^[А-Я][а-я]+\s+[А-Я]+$', lines[i + 1].strip()) and
                re.match(r'^[А-Я]{2,4}$', lines[i + 2].strip())):
                
                athlete_count += 1
                print(f"\n🎯 Найден спортсмен #{athlete_count}: {lines[i + 1].strip()}")
                athlete_data = extract_athlete_with_variable_elements(lines, i)
                if athlete_data and athlete_data['elements']:  # Только если есть элементы!
                    results.append(athlete_data)
                    print(f"✅ Добавлен: {athlete_data['name']} {athlete_data['surname']} - {len(athlete_data['elements'])} элементов")
                    i += 40  # Пропускаем большой блок спортсмена
                    continue
        
        i += 1
    
    return results

def extract_athlete_with_variable_elements(lines, start_idx):
    """Извлекает данные спортсмена с переменным количеством элементов (1-16)"""
    try:
        athlete = {}
        
        # Место и стартовый номер
        rank_num = lines[start_idx].strip().split()
        athlete['rank'] = int(rank_num[0])
        athlete['startNumber'] = int(rank_num[1])
        
        # Имя и фамилия
        name_parts = lines[start_idx + 1].strip().split()
        athlete['name'] = name_parts[0]
        athlete['surname'] = name_parts[1]
        
        # Регион
        athlete['region'] = lines[start_idx + 2].strip()
        
        # Место тренировки
        if start_idx + 3 < len(lines):
            location = lines[start_idx + 3].strip()
            if (location and not re.match(r'^\d', location) and 
                not re.match(r'^[А-Я]{2,4}$', location) and
                len(location) > 3):
                athlete['location'] = location
        
        # Поиск баллов
        scores_found = False
        for i in range(start_idx, min(start_idx + 20, len(lines))):
            line = lines[i].strip()
            # Ищем формат: XX.XX 0.00 XX.XX XX.XX
            scores_match = re.search(r'(\d+\.\d{2})\s+0\.00\s+(\d+\.\d{2})\s+(\d+\.\d{2})', line)
            if scores_match:
                athlete['totalScore'] = float(scores_match.group(1))
                athlete['componentScore'] = float(scores_match.group(2))
                athlete['technicalScore'] = float(scores_match.group(3))
                athlete['deductions'] = 0.00
                scores_found = True
                print(f"   Баллы: {scores_match.group(1)} / {scores_match.group(3)} / {scores_match.group(2)}")
                break
        
        if not scores_found:
            print(f"   ⚠️ Не найдены баллы для {athlete['name']}")
            return None
        
        # Извлекаем элементы - ОТ 1 ДО 16!
        elements = []
        base_technical_score = 0.0
        
        # Ищем блок элементов (строки с номерами 1-16)
        for i in range(start_idx + 5, min(start_idx + 100, len(lines))):  # Увеличиваем диапазон поиска
            line = lines[i].strip()
            
            # Паттерн для элемента: номер (1-16), название, BV, GOE, ..., total
            element_match = re.match(r'^(\d+)\s+([A-Za-z0-9+<>!*\.q\-]+)\s+([\d\.]+)\s+([\-\d\.]+)', line)
            if element_match and 1 <= int(element_match.group(1)) <= 16:
                element_num = int(element_match.group(1))
                element_name = element_match.group(2).strip()
                bv = float(element_match.group(3))
                goe = float(element_match.group(4))
                
                # Ищем total (последнее число в формате XX.XX в этой строке)
                numbers_in_line = re.findall(r'\d+\.\d{2}', line)
                total_score = float(numbers_in_line[-1]) if numbers_in_line else 0.0
                
                # Если не нашли в текущей строке, проверяем следующую
                if total_score == 0 and i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    next_numbers = re.findall(r'\d+\.\d{2}', next_line)
                    if next_numbers:
                        total_score = float(next_numbers[0])
                
                element_data = {
                    'number': element_num,
                    'name': element_name,
                    'bv': bv,
                    'goe': goe,
                    'total': total_score
                }
                
                elements.append(element_data)
                base_technical_score += bv
                
                print(f"   Элемент {element_num}: {element_name} BV={bv} GOE={goe} Total={total_score}")
            
            # Если нашли начало следующего блока или конец данных спортсмена - выходим
            elif elements and (re.match(r'^\d+\s+\d+$', line) or 'Компоненты программы' in line):
                break
        
        # Проверяем что нашли хотя бы 1 элемент
        if len(elements) == 0:
            print(f"   ❌ Не найдено ни одного элемента для {athlete['name']}!")
            return None
        
        print(f"   📊 Найдено элементов: {len(elements)}")
        
        athlete['elements'] = elements
        athlete['baseTechnicalScore'] = round(base_technical_score, 2)
        
        return athlete
        
    except Exception as e:
        print(f"❌ Ошибка при извлечении данных: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    pdf_path = "p_K_Scores.pdf"
    
    # Проверяем что файл существует
    if not os.path.exists(pdf_path):
        print(f"❌ Файл {pdf_path} не найден!")
        print(f"Текущая папка: {os.getcwd()}")
        return
    
    print(f"✅ Файл найден: {pdf_path}")
    
    try:
        # Запускаем парсер
        data = parse_all_athletes_with_variable_elements(pdf_path)
        
        if data:
            # Сохраняем в JSON
            output_file = 'skating_results_complete.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"\n🎉 УСПЕХ! Обработано спортсменов: {len(data)}")
            print(f"💾 Файл сохранен: {output_file}")
            
            # Статистика по элементам
            total_elements = sum(len(athlete['elements']) for athlete in data)
            avg_elements = total_elements / len(data) if data else 0
            min_elements = min(len(athlete['elements']) for athlete in data) if data else 0
            max_elements = max(len(athlete['elements']) for athlete in data) if data else 0
            
            print(f"\n📊 СТАТИСТИКА ПО ЭЛЕМЕНТАМ:")
            print(f"   Всего элементов: {total_elements}")
            print(f"   Спортсменов: {len(data)}")
            print(f"   Минимум элементов: {min_elements}")
            print(f"   Максимум элементов: {max_elements}")
            print(f"   В среднем: {avg_elements:.1f} элементов на спортсмена")
            
            # Распределение по количеству элементов
            element_counts = {}
            for athlete in data:
                count = len(athlete['elements'])
                element_counts[count] = element_counts.get(count, 0) + 1
            
            print(f"   Распределение: {dict(sorted(element_counts.items()))}")
            
            # Показываем первых 3 спортсменов для проверки
            print(f"\n👥 ПЕРВЫЕ 3 СПОРТСМЕНА:")
            for i, athlete in enumerate(data[:3]):
                print(f"\n{athlete['rank']}. {athlete['name']} {athlete['surname']} - {len(athlete['elements'])} элементов")
                for element in athlete['elements']:
                    print(f"   {element['number']:2d}. {element['name']:15} BV={element['bv']:5.2f} GOE={element['goe']:5.2f} Total={element['total']:5.2f}")
            
            # Полная структура первого спортсмена
            print(f"\n📋 ПОЛНАЯ СТРУКТУРА ПЕРВОГО СПОРТСМЕНА:")
            print(json.dumps(data[0], ensure_ascii=False, indent=2))
            
        else:
            print("❌ Не удалось извлечь данные")
            print("Проверьте файл debug_lines.txt для анализа структуры")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()