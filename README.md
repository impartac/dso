# SecDev Course Template

Media Catalog

## Быстрый старт
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-dev.txt
pre-commit install
uvicorn app.main:app --reload
```

## Ритуал перед PR
```bash
ruff check --fix .
black .
isort .
pytest -q
pre-commit run --all-files
```

## Тесты
```bash
pytest -q
```

## CI
В репозитории настроен workflow **CI** (GitHub Actions) — required check для `main`.
Badge добавится автоматически после загрузки шаблона в GitHub.

## Контейнеры
```bash
docker compose up -d app
```

## Эндпойнты
- `GET /health` → `{"status": "ok"}`
- `POST /items?name=...` — демо-сущность
- `GET /items/{id}`

## Формат ошибок
Все ошибки — JSON-обёртка:
```json
{
  "error": {"code": "not_found", "message": "item not found"}
}
```

См. также: `SECURITY.md`, `.pre-commit-config.yaml`, `.github/workflows/ci.yml`.

## 🔒 Security Evidence

This project follows evidence-based security practices. Automated artifacts are stored in the `EVIDENCE/` directory.

### SBOM (Software Bill of Materials)
- **Location:** `EVIDENCE/P09/`
- **Generation:** Automated via GitHub Actions on every push and release
- **Format:** SPDX JSON
- **Tool:** Anchore Syft (v0.102.1)
- **Access:** Available as workflow artifacts and attached to releases

To view the latest SBOM:
1. Go to [Actions](https://github.com/your-username/your-repo/actions)
2. Find the latest "SBOM Generation" workflow run
3. Download the `sbom-evidence-{SHA}` artifact

For more details, see [EVIDENCE/README.md](EVIDENCE/README.md).

## 🛡️ Compliance
This setup satisfies the following requirements:
- ✅ Automated SBOM generation
- ✅ Fixed tool version (deterministic builds)
- ✅ Evidence storage with commit linkage

## 🔍 SCA (Software Composition Analysis)

### Автоматическое сканирование уязвимостей
- **Инструмент:** Anchore Grype (фиксированная версия)
- **Частота:** При каждом push, PR и релизе
- **Источник:** SBOM + прямые зависимости

### Отчеты и сводки
- **Полный отчет:** `EVIDENCE/P09/sca_report.json` (JSON)
- **Сводка:** `EVIDENCE/P09/sca_summary.md` (Markdown)
- **PR комментарии:** Автоматические уведомления о Critical/High уязвимостях

### Ключевые метрики
- Severity breakdown (Critical/High/Medium/Low)
- Планы действий для каждой категории
- Воспроизводимые результаты
- Историческое сравнение

### Настройка
- Исключение ложных срабатываний: `.github/grype-config.yaml`
- Локальная переопределение: `.grype.yaml`
- Thresholds: Настраивается в workflow

### Быстрый доступ
1. **Текущий статус:** Последний workflow run в Actions
2. **История:** Артефакты за последние 90 дней
3. **PR проверка:** Комментарии в Pull Requests
