# django-shop
Выражаю благодарность этому человеку за его туториал https://www.youtube.com/watch?v=jME4-T_hfhQ&list=PLETAtUAAzGHRyGM0ksurmNYTEAd_rlA-u&index=3

Установите зависимые пакеты
```pip install -r requirements.txt```

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
