# vezdecode-WEB-MASTER-20
## Запуск

### Windows

```bash
python3 -m pip install -r requirements.txt
set VK_GROUP_ID=
  # ID группы бота вк
set VK_TOKEN=
  # Токен бота вк
set DISCORD_TOKEN=
  # Токен бота дискорда
python3 __main__.py
```
### Linux

```bash
python3 -m pip install -r requirements.txt
export VK_GROUP_ID=
  # ID группы бота вк
export VK_TOKEN=
  # Токен бота вк
export DISCORD_TOKEN=
  # Токен бота дискорда
python3 __main__.py
```

Во время запуска нужно ввести:
  - vk peer id - 2000000000 + id чата, обычно 1, или id пользователя
  - discord channel id - id канала в дискорде, можно получить нажав пкм по каналу -> Копировать ID (Нужен режим разработчика)

## Возможности
  - ВК -> Дискорд
    - Текст
    - Фото
    - Опросы
    - Документы
    - Стикеры
    - Аудио (Исполнитель и название)
    - Видео (Только ссылка)
    - Ответы на сообщения
    - Пересланное сообщения
  - Дискорд -> ВК
    - Текст
    - Фото
