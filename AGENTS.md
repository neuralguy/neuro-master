# Notes

## Архитектура: фоновые задачи и сессии БД

`asyncio.create_task()` запускает задачи в фоне — сессия БД из HTTP-запроса к этому моменту уже закрыта.
Все операции с БД внутри фоновых задач (`_process_generation`, `_poll_generation` и т.п.) **должны открывать новую сессию** через `get_session_context()`, а не использовать `self.session`.

Пример правильного паттерна для фоновых операций:
```python
from src.core.database import get_session_context

async with get_session_context() as session:
    repo = SomeRepository(session)
    await repo.do_something()
# коммит происходит автоматически при выходе из контекста
```

## Модели с price_display_mode = per_second

Для моделей с `price_display_mode = "per_second"` обязательно задавать в `DEFAULT_MODELS`:
- `price_per_second` — стоимость за секунду
- `price_display_mode` — `"per_second"`
- `price_tokens` — можно поставить равным `price_per_second` (используется как fallback)

Seed (`sync` в `service.py`) должен синхронизировать `price_display_mode` так же как `price_per_second`.

## Motion Control: длительность из загруженного видео

Для моделей с `config.mode == "motion-control"` длительность определяется автоматически из загруженного видео (ffprobe в `upload.py`). Фронтенд должен:
1. Сохранять `response.duration` после загрузки видео (округлять через `Math.round`)
2. Передавать её как `duration` при создании генерации
3. Использовать для расчёта стоимости: `price_per_second * uploadedVideoDuration`

## FastAPI + Pydantic ошибки валидации

FastAPI возвращает ошибки валидации как `detail: [{loc, msg, type}]` (массив), а не строку.
В axios-interceptor нужно обрабатывать оба случая:
```ts
const detail = error.response?.data?.detail;
if (typeof detail === 'string') { message = detail; }
else if (Array.isArray(detail)) { message = detail[0]?.msg || JSON.stringify(detail); }
```
