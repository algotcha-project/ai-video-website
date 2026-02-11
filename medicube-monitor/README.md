# Medicube Korea Product Monitor

Автоматичний моніторинг нових товарів на сайті [m.themedicube.co.kr](https://m.themedicube.co.kr/) з повідомленнями через Telegram бот.

## Що робить

- Скрейпить усі товари з сайту Medicube Korea (7+ категорій)
- Порівнює з попередньо збереженими товарами
- Надсилає Telegram повідомлення при появі нових товарів
- Працює автономно кожні 24 години (cron або daemon)

## Швидкий старт

### 1. Встановлення

```bash
cd medicube-monitor
chmod +x setup.sh
./setup.sh
```

### 2. Налаштування Telegram

1. Відкрийте Telegram і знайдіть бот: **@KoreanEonni_bot**
2. Надішліть боту `/start`
3. Запустіть налаштування:

```bash
python3 monitor.py --setup
```

### 3. Ручний запуск

```bash
# Одноразова перевірка
python3 monitor.py --check

# Перевірка з детальним логуванням
python3 monitor.py --check --verbose

# Режим демона (безперервний моніторинг)
python3 monitor.py --daemon --interval 24
```

## Варіанти розгортання

### Cron (рекомендовано)

Скрипт `setup.sh` автоматично додає cron завдання.
Перевірка відбувається щодня о 00:00 UTC (09:00 KST).

```bash
# Переглянути cron завдання
crontab -l

# Ручне додавання
crontab -e
# Додати: 0 0 * * * cd /path/to/medicube-monitor && python3 monitor.py --check
```

### Systemd Service

```bash
sudo systemctl enable medicube-monitor
sudo systemctl start medicube-monitor
sudo systemctl status medicube-monitor

# Логи
sudo journalctl -u medicube-monitor -f
```

### Docker

```bash
docker build -t medicube-monitor .
docker run -d \
  --name medicube-monitor \
  -v medicube-data:/app/data \
  --restart unless-stopped \
  medicube-monitor
```

## Структура файлів

```
medicube-monitor/
├── monitor.py          # Головний скрипт
├── scraper.py          # Скрейпер сайту Medicube
├── telegram_bot.py     # Telegram бот для повідомлень
├── storage.py          # Зберігання даних (JSON)
├── requirements.txt    # Python залежності
├── setup.sh            # Скрипт автоматичного налаштування
├── Dockerfile          # Docker конфігурація
├── README.md           # Документація
└── data/               # Створюється автоматично
    ├── known_products.json   # Відомі товари
    ├── config.json           # Конфігурація (chat IDs)
    ├── check_history.json    # Історія перевірок
    └── monitor.log           # Логи
```

## Конфігурація

| Параметр | Опис | За замовчуванням |
|----------|------|------------------|
| `--interval` | Інтервал перевірки (години) | 24 |
| `--token` | Telegram bot token | Вбудований |
| `--chat-id` | Telegram chat ID | Автовиявлення |
| `--verbose` | Детальне логування | Вимкнено |
| `MEDICUBE_BOT_TOKEN` | ENV змінна для токена | - |

## Як працює

1. **Скрейпінг**: Парсить HTML сторінки категорій товарів на Cafe24 платформі Medicube
2. **Порівняння**: Зберігає `product_no` кожного товару в JSON. Нові ID = нові товари
3. **Повідомлення**: Для кожного нового товару надсилає форматоване повідомлення в Telegram
4. **Перший запуск**: Зберігає всі поточні товари як базу (без повідомлень), щоб не спамити
