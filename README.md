# django-shop
Выражаю благодарность этому человеку за его туториал https://youtu.be/jME4-T_hfhQ

Устанавливаем зависимые пакеты
```
pip install -r requirements.txt
```

Создаем новые миграции на основе моделей models.py 
```
python manage.py makemigrations
```
Вводим команду (которая отвечает за применение и отмену миграций)
```
python manage.py migrate
```
Запускаем локальный сервер: To start project on localhost:8000
```
python manage.py runserver
```
