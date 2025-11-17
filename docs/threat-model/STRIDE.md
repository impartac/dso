
## 3. STRIDE анализ угроз

**Файл: `docs/threat-model/STRIDE.md`**


# STRIDE Анализ угроз

## Анализ ключевых потоков данных

### Поток F1/F2: Клиент → Система
**Элементы:** Web App, Mobile App, API Gateway

| Угроза | Категория | Контрмеры | NFR ссылка | Обоснование |
|--------|-----------|-----------|------------|-------------|
| Перехват учетных данных | Information Disclosure | HTTPS, certificate pinning, HSTS | NFR-8 | Все внешние коммуникации должны использовать TLS 1.2+ |
| Подделка сессий/токенов | Spoofing | JWT signature validation, secure cookie flags | NFR-9, NFR-21 | Токены должны проверяться на каждом запросе |
| CSRF атаки | Tampering | CSRF tokens, SameSite cookies | NFR-17 | Защита state-changing операций |

### Поток F5/F6: Клиентские приложения → API
**Элементы:** Load Balancer, WAF

| Угроза | Категория | Контрмеры | NFR ссылка | Обоснование |
|--------|-----------|-----------|------------|-------------|
| DDoS атаки | Denial of Service | Rate limiting, WAF, auto-scaling | NFR-20 | Система должна выдерживать 10x нормальной нагрузки |
| SQL/NoSQL инъекции | Tampering | Input validation, prepared statements | NFR-7 | 0 успешных инъекций при тестировании |
| XSS атаки | Tampering | HTML escaping, CSP headers | NFR-13 | Защита пользовательского контента |

### Поток F9-F11: Внутренняя коммуникация
**Элементы:** API Gateway, Микросервисы

| Угроза | Категория | Контрмеры | NFR ссылка | Обоснование |
|--------|-----------|-----------|------------|-------------|
| Подделка сервисов | Spoofing | Mutual TLS, service mesh | NFR-18 | Проверка подлинности сервисов |
| Перехват внутреннего трафика | Information Disclosure | Service-to-service encryption | NFR-19 | Сегрегация сетей, шифрование |
| DoS внутренних сервисов | Denial of Service | Circuit breakers, quotas | NFR-20 | Защита от каскадных отказов |

### Поток F12-F16: Доступ к данным
**Элементы:** Базы данных, кэш, файловое хранилище

| Угроза | Категория | Контрмеры | NFR ссылка | Обоснование |
|--------|-----------|-----------|------------|-------------|
| Неавторизованный доступ к данным | Elevation of Privilege | RBAC, database permissions | NFR-11 | Принцип минимальных привилегий |
| Утечка чувствительных данных | Information Disclosure | Encryption at rest, data masking | NFR-6, NFR-10 | Шифрование ПДН, маскирование в логах |
| Инъекции в хранилища | Tampering | Parameterized queries, ORM | NFR-7 | Защита от NoSQL/SQL инъекций |

### Поток F15: Файловые операции
**Элементы:** Media Service, File Storage

| Угроза | Категория | Контрмеры | NFR ссылка | Обоснование |
|--------|-----------|-----------|------------|-------------|
| Загрузка malicious файлов | Tampering | File type validation, virus scanning | NFR-14 | Валидация MIME типа, антивирус |
| Доступ к чужим файлам | Elevation of Privilege | Access control checks | NFR-11 | Проверка прав доступа к файлам |

## Верификация контрмер

**Автоматические проверки:**
- SAST/DAST сканирование (NFR-7, NFR-13)
- Security testing в CI/CD (NFR-12)
- Compliance сканирование (NFR-18)
- Penetration testing (все NFR)

**Ручные проверки:**
- Security code review
- Architecture review
- Threat modeling sessions
