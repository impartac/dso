# ============================================================================
# Docker Build and Scanning Commands
# ============================================================================
# Используемые команды для локального тестирования и проверки

# ============================================================================
# 1. BUILD STAGE - Построение образа
# ============================================================================

## Построить образ в режиме production
docker build -t app:latest -f Dockerfile .

## Построить с указанием tag'а и версии
docker build -t app:v1.0.0 -f Dockerfile .

## Построить с прогрессом и показом layers
docker build --progress=plain -t app:latest -f Dockerfile .

## Построить с mount кэша для оптимизации
docker buildx build --cache-from=type=local,src=/tmp/docker-cache \
  --cache-to=type=local,dest=/tmp/docker-cache \
  -t app:latest -f Dockerfile .

# ============================================================================
# 2. INSPECTION - Анализ образа
# ============================================================================

## Посмотреть размер образа
docker images app:latest

## Детальный анализ слоёв (history)
docker history app:latest

## Просмотреть все слои с их размерами в таблице
docker history --human app:latest

## Инспектировать конфигурацию контейнера
docker inspect app:latest

## Просмотреть только Config и SecurityContext
docker inspect app:latest | jq '.[] | {User: .Config.User, Healthcheck: .Config.Healthcheck}'

## Просмотреть environment переменные
docker inspect app:latest | jq '.[] | .Config.Env'

## Проверить слои образа с человекочитаемыми размерами
docker history --human --no-trunc app:latest

# ============================================================================
# 3. COMPOSE - Управление многоконтейнерным окружением
# ============================================================================

## Стартовать все сервисы в prod профиле
docker compose --profile prod up -d

## Стартовать все сервисы в dev профиле
docker compose --profile dev up -d

## Построить только app сервис
docker compose build app

## Посмотреть логи всех сервисов
docker compose logs -f

## Посмотреть логи конкретного сервиса
docker compose logs -f app

## Остановить все сервисы
docker compose down

## Остановить и удалить volumes
docker compose down -v

## Перезагрузить конкретный сервис
docker compose restart app

## Выполнить команду в работающем контейнере
docker compose exec app bash

## Проверить статус сервисов
docker compose ps

# ============================================================================
# 4. HADOLINT - Linting Dockerfile
# ============================================================================

## Запустить hadolint локально
hadolint Dockerfile

## Запустить в контейнере (без установки)
docker run --rm -i hadolint/hadolint < Dockerfile

## Экспортировать результаты в JSON
docker run --rm -i hadolint/hadolint:latest-debian hadolint --format json Dockerfile > hadolint-report.json

# ============================================================================
# 5. TRIVY - Vulnerability Scanning
# ============================================================================

## Установить Trivy (если не установлена)
# curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin

## Сканировать локальный образ
trivy image app:latest

## Сканировать с форматом JSON
trivy image --format json app:latest > trivy-report.json

## Сканировать с форматом таблица и сохранить в файл
trivy image --format table app:latest > trivy-report.txt

## Сканировать только HIGH и CRITICAL уязвимости
trivy image --severity HIGH,CRITICAL app:latest

## Сканировать с полной информацией (скрыть LOW и INFO)
trivy image --severity MEDIUM,HIGH,CRITICAL app:latest

## Сканировать с ignoring известных уязвимостей
trivy image --skip-update app:latest

## Сканировать с форматом SARIF (для GitHub)
trivy image --format sarif app:latest > trivy-results.sarif

## Сканировать с временем ожидания
trivy image --timeout 10m app:latest

## Сканировать с детальным выводом
trivy image --debug app:latest

## Сканировать конфигурационные файлы
trivy config .

## Сканировать исходный код на секреты
trivy fs .

# ============================================================================
# 6. SECURITY COMPLIANCE CHECKS
# ============================================================================

## Проверить, что контейнер не запускается от root
docker inspect app:latest | jq '.[] | .Config.User'

## Проверить наличие HEALTHCHECK
docker inspect app:latest | jq '.[] | .Config.Healthcheck'

## Проверить, что используется read-only filesystem
docker inspect app:latest | jq '.[] | .Config.ReadonlyRootfs'

## Проверить entrypoint и command
docker inspect app:latest | jq '.[] | {Entrypoint: .Config.Entrypoint, Cmd: .Config.Cmd}'

## Проверить environment переменные
docker inspect app:latest | jq '.[] | .Config.Env'

## Проверить exposed ports
docker inspect app:latest | jq '.[] | .Config.ExposedPorts'

# ============================================================================
# 7. RUNTIME TESTING
# ============================================================================

## Запустить контейнер с hardening options
docker run --rm \
  --cap-drop=ALL \
  --cap-add=NET_BIND_SERVICE \
  --security-opt=no-new-privileges:true \
  --read-only \
  --tmpfs /tmp \
  -p 8000:8000 \
  app:latest

## Запустить и проверить healthcheck
docker run --rm -d --name test-app app:latest
sleep 5
docker exec test-app curl -f http://localhost:8000/health
docker stop test-app

## Запустить с логированием
docker run --rm --log-driver json-file --log-opt max-size=10m --log-opt max-file=3 app:latest

## Запустить с resource limits
docker run --rm \
  --memory=512m \
  --cpus=1 \
  --memory-swap=512m \
  -p 8000:8000 \
  app:latest

# ============================================================================
# 8. DOCKER COMPOSE SPECIFIC
# ============================================================================

## Запустить тесты через compose
docker compose --profile dev run test

## Запустить линтинг через compose
docker compose --profile dev run lint

## Запустить с переменными окружения
docker compose --profile prod -e DEBUG=false -e LOG_LEVEL=info up -d

## Выполнить миграции перед запуском
docker compose run --rm app alembic upgrade head

## Просмотреть используемые volumes
docker compose volume ls

## Очистить orphaned containers
docker compose down --remove-orphans

# ============================================================================
# 9. CI/CD INTEGRATION
# ============================================================================

## Запустить все проверки перед коммитом
./scripts/pre-commit.sh

## Запустить полный pipeline локально (требуется Docker + GitHub Actions)
act -j build

## Запустить только Trivy сканирование
act -j trivy-scan

## Запустить сканирование Hadolint
act -j hadolint

# ============================================================================
# 10. CLEANUP
# ============================================================================

## Удалить dangling images
docker image prune -f

## Удалить неиспользуемые контейнеры
docker container prune -f

## Удалить неиспользуемые volumes
docker volume prune -f

## Полная очистка (осторожно!)
docker system prune -a --volumes

## Удалить все образы приложения
docker rmi app:latest app:v1.0.0

# ============================================================================
# 11. TROUBLESHOOTING
# ============================================================================

## Просмотреть логи docker daemon
journalctl -u docker.service -f

## Диагностика Docker
docker info

## Проверить disk usage
docker system df

## Проверить сетевые соединения контейнера
docker inspect -f '{{json .NetworkSettings}}' <container_id> | jq

## Проверить mount точки контейнера
docker inspect -f '{{json .Mounts}}' <container_id> | jq

## Получить shell в работающем контейнере
docker exec -it <container_id> /bin/bash

## Скопировать файл из контейнера
docker cp <container_id>:/app/file.txt ./local_file.txt

## Логи контейнера в реальном времени
docker logs -f --tail 100 <container_id>
