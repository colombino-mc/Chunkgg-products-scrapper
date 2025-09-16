<div align="center">

# 🕷️ Scappy - Веб-скрапер для Chunk.gg

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Scrapy](https://img.shields.io/badge/Scrapy-2.13.3-green.svg)](https://scrapy.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Мощный веб-скрапер для извлечения данных о продуктах Minecraft с маркетплейса Chunk.gg**

[🚀 Быстрый старт](#-быстрый-старт) • [📋 Возможности](#-возможности) • [📊 Примеры](#-примеры) • [🛠️ Установка](#️-установка)

</div>

---

## 📋 Описание

**Scappy** — это высокопроизводительный веб-скрапер, построенный на базе фреймворка Scrapy, специально разработанный для сбора данных о продуктах Minecraft с популярного маркетплейса [chunk.gg](https://chunk.gg).

### 🎯 Что собираем:
- 🏷️ **Названия продуктов** и создателей
- 💰 **Категории и цены** в Minecoins  
- ⭐ **Рейтинги и отзывы** пользователей
- 📅 **Даты запуска** и требования к версии
- 🏷️ **Теги продуктов** и метаданные

---

## ✨ Возможности

<table>
<tr>
<td width="50%">

### 🚀 Производительность
- ⚡ **Асинхронный краулинг** с высокой скоростью
- 🎯 **Умное управление** запросами
- 📊 **Автоматическое регулирование** нагрузки

</td>
<td width="50%">

### 🛡️ Надежность  
- 🤖 **Соблюдение robots.txt**
- ⏱️ **Вежливые задержки** между запросами
- 🔄 **Автоматические повторы** при ошибках

</td>
</tr>
<tr>
<td width="50%">

### 📈 Масштабируемость
- 🌐 **Множественные категории** продуктов
- 📁 **Гибкая структура** данных
- 💾 **Экспорт в CSV** формат

</td>
<td width="50%">

### 🎮 Категории
- 🆕 Новинки
- 🔥 Трендовые  
- ⭐ Популярные
- 🔧 Аддоны
- 🌍 Миры
- 🎨 Машапы
- 🖼️ Текстуры
- 👤 Скины

</td>
</tr>
</table>

---

## 🚀 Быстрый старт

### 1️⃣ Клонирование репозитория
```bash
git clone https://github.com/yourusername/scappy.git
cd scappy
```

### 2️⃣ Установка зависимостей
```bash
pip install -r requirements.txt
```

### 3️⃣ Запуск скрапера
```bash
cd chunkgg
scrapy crawl chunk_products
```

### 4️⃣ Получение результатов
```bash
# Данные сохраняются в products.csv
head -5 products.csv
```

---

## 📊 Примеры

### 📈 Статистика сбора данных
```
📊 Статистика скрапинга:
┌─────────────────┬─────────┐
│ Категория       │ Количество │
├─────────────────┼─────────┤
│ 🆕 Новинки      │    245   │
│ 🔥 Трендовые    │    189   │
│ ⭐ Популярные   │    312   │
│ 🔧 Аддоны       │    156   │
│ 🌍 Миры         │    98    │
│ 🎨 Машапы       │    67    │
│ 🖼️ Текстуры     │    134   │
│ 👤 Скины        │    89    │
└─────────────────┴─────────┘
📈 Всего продуктов: 1,290
```

### 📋 Структура данных
```csv
url,title,creator,category,price_minecoins,rating_value,rating_count,launched,last_updated,min_version,uid,tags
https://chunk.gg/@creator/amazing-addon,Amazing Addon,Creator Name,Minecraft Addon Add-On,830,4.5,1234,2024-01-15,2024-02-01,1.20.0,12345678-1234-1234-1234-123456789012,"adventure,multiplayer,fun"
```

---

## 🛠️ Установка

### Требования
- 🐍 **Python 3.8+**
- 📦 **Scrapy 2.13.3**
- 🌐 **Интернет-соединение**

### Пошаговая установка

<details>
<summary>🔽 Развернуть инструкции</summary>

#### Windows
```powershell
# Создание виртуального окружения
python -m venv venv
venv\Scripts\activate

# Установка зависимостей
pip install -r requirements.txt
```

#### Linux/macOS
```bash
# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt
```

</details>

---

## 📁 Структура проекта

```
📦 scappy/
├── 📁 chunkgg/                    # Основной проект Scrapy
│   ├── 📁 chunkgg/
│   │   ├── 📁 spiders/
│   │   │   └── 🕷️ chunk_products.py    # Главный паук
│   │   ├── 📄 items.py                 # Модели данных
│   │   ├── ⚙️ settings.py              # Конфигурация
│   │   └── 🔄 pipelines.py             # Обработка данных
│   ├── 📊 products.csv                 # Результат скрапинга
│   └── 📋 scrapy.cfg                   # Конфиг проекта
├── 📄 requirements.txt                 # Зависимости
├── 📖 README.md                        # Документация
└── 🚫 .gitignore                       # Игнорируемые файлы
```

---

## 🎛️ Конфигурация

### Настройки производительности
```python
# settings.py
CONCURRENT_REQUESTS_PER_DOMAIN = 1
DOWNLOAD_DELAY = 0.75
AUTOTHROTTLE_ENABLED = True
```

### Пользовательские заголовки
```python
DEFAULT_REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ChunkResearchBot/1.0)"
}
```

---

## 📈 Результаты

### 📊 Собранные поля данных:
- 🌐 **url** - Ссылка на продукт
- 🏷️ **title** - Название продукта  
- 👤 **creator** - Создатель
- 📂 **category** - Категория
- 💰 **price_minecoins** - Цена в Minecoins
- ⭐ **rating_value** - Средний рейтинг
- 📊 **rating_count** - Количество оценок
- 📅 **launched** - Дата запуска
- 🔄 **last_updated** - Последнее обновление
- 🎮 **min_version** - Минимальная версия
- 🆔 **uid** - Уникальный идентификатор
- 🏷️ **tags** - Теги продукта

---

## 🤝 Вклад в проект

Мы приветствуем вклад в развитие проекта! 

1. 🍴 Форкните репозиторий
2. 🌿 Создайте ветку для новой функции
3. 💾 Сделайте коммит изменений
4. 📤 Отправьте Pull Request

---

## 📄 Лицензия

Этот проект распространяется под лицензией MIT. См. файл [LICENSE](LICENSE) для подробностей.

---

<div align="center">

**Сделано с ❤️ для сообщества Minecraft**

[⬆️ Наверх](#-scappy---веб-скрапер-для-chunkgg)

</div>
