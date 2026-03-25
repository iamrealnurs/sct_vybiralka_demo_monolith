import os
import subprocess

# Определяем пути к файлам
file_paths = [
    # Конфигурация
    "src/urls.py",
    
    # Модели (Базис)
    "main/models.py",
    "cars/models.py",
    "catalog/models.py",
    "client/models.py",
    
    # Логика API для сотрудников (Сложные операции)
    "api/staff/cars/services.py",
    "api/staff/cars/urls.py",
    "api/staff/cars/views.py",

    "api/staff/packages/forms.py",
    "api/staff/packages/services.py",
    "api/staff/packages/urls.py",
    "api/staff/packages/views.py",
    
    "api/staff/urls.py",
    
    # Логика API для клиентов
    "api/client/services.py",
    "api/client/views.py",    

    # --- ТЕПЕРЬ ШАБЛОНЫ (Templates) ---
    "templates/client/auth/login.html",
    "templates/client/garage/create.html",
    "templates/client/garage/detail.html",
    "templates/client/garage/list.html",
    "templates/client/base.html",    
    "templates/client/dashboard.html",    

    "templates/staff/base.html",
    "templates/staff/cars/list.html",
    "templates/staff/cars/detail.html",

    "templates/staff/packages/create.html",
    "templates/staff/packages/edit.html",
    "templates/staff/packages/detail.html",
    "templates/staff/packages/list.html",

    # Компоненты
    "templates/staff/packages/_image_card.html",
    "templates/staff/packages/_page_header.html",
    "templates/staff/packages/_price_summary.html",
    "templates/staff/packages/_promo_card.html",
    "templates/staff/packages/_vehicle_card.html",
]

output_file = "datagen_data/prompts/api/prompt_api.txt"
os.makedirs(os.path.dirname(output_file), exist_ok=True)

with open(output_file, "w", encoding="utf-8") as f_out:
    for i, file_path in enumerate(file_paths):
        # Если это не первый элемент, добавляем 3 переноса (\n\n\n), 
        # что дает ровно 2 пустые строки между блоками.
        prefix = "\n" if i > 0 else ""
        f_out.write(f"{prefix}Вот мой код из файла {file_path}\n\n")
        
        try:
            with open(file_path, "r", encoding="utf-8") as f_in:
                # .strip() убирает лишние "хвосты" в конце файлов
                f_out.write(f_in.read().strip() + "\n")
        except FileNotFoundError:
            f_out.write("(Файл не найден)\n")

    # Секция с URL
    try:
        result = subprocess.run(["python", "manage.py", "show_urls"], capture_output=True, text=True)
        # Фильтруем пустые строки и нужные эндпоинты
        urls = [url.strip() for url in result.stdout.split("\n") if url.startswith("/api/v1/")]
        
        if urls:
            f_out.write("\n\n\nВот мой код из фрагмента выдачи из терминала на команду python manage.py show_urls\n\n")
            f_out.write("\n".join(urls) + "\n")
            
    except Exception as e:
        # Теперь кавычка на месте
        f_out.write(f"\n\n\nОшибка при выполнении команды: {e}\n")

print(f"Файл {output_file} успешно создан!")

