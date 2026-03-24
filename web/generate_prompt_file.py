import os
import subprocess

# Определяем пути к файлам
file_paths = [
    "main/models.py",
    "cars/models.py",
    "catalog/models.py",
    "client/models.py",
    "datagen_data/datagen.py",
    "datagen_data/script.py",
]

# Путь к файлу, который мы создаем
output_file = "datagen_data/prompts/api/prompt_api.txt"

os.makedirs(os.path.dirname(output_file), exist_ok=True)

with open(output_file, "w", encoding="utf-8") as f_out:
    for file_path in file_paths:
        f_out.write(f"Вот мой код из файла {file_path}\n" + "\n\n")
        try:
            with open(file_path, "r", encoding="utf-8") as f_in:
                f_out.write(f_in.read() + "\n\n")
        except FileNotFoundError:
            f_out.write("    (Файл не найден)\n\n")

    # Получаем список URL из Django
    try:
        result = subprocess.run(["python", "manage.py", "show_urls"], capture_output=True, text=True)
        urls = result.stdout.split("\n")
        
        f_out.write("Вот мой код из фрагмента выдачи из терминала на команду python manage.py show_urls\n\n")
        for url in urls:
            if url.startswith("/api/v1/"):
                f_out.write(url + "\n")
    except Exception as e:
        f_out.write(f"Ошибка при выполнении команды: {e}\n")

print(f"Файл {output_file} успешно создан!")












