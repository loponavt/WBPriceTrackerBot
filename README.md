## Телеграмм-бот для отслеживания уменьшения цены по артикулу WB
Для работы с ботом используется aiogram, БД - sqlite. Токен передается через python dotenv.   
Для периодического запуска функции проверки изменения цены - apscheduler.  
Для получения данных с wb - fake_useragent, requests.

Работающий пример - https://t.me/WB_price_tracker_bot