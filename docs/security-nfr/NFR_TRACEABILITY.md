## Traces:
   ### misuse: "Brute force атака на логин"
    nfr: "NFR-1 Защита аутентификации"
    test: "auth_rate_limit.feature: Блокировка IP при multiple failed logins"
    event_metric: "auth_ip_blocked, rate_limit_count"
    owner: "team-security"

  ### misuse: "Mass creation spam медиа"
    nfr: "NFR-2 Лимит создания медиа"
    test: "media_create_limit.feature: Срабатывание лимита на создание медиа"
    event_metric: "rate_limit_triggered, http_429_total"
    owner: "team-backend"

  ### misuse: "Information leakage через ошибки"
    nfr: "NFR-3 Маскирование ошибок"
    test: "test_error_masking.py::test_no_secrets_in_errors"
    event_metric: "error_redacted=true, dlp_findings_count"
    owner: "team-backend"

  ### misuse: "Compromise секретов из кода"
    nfr: "NFR-4 Управление секретами"
    test: "ci/secret_scan.sh"
    event_metric: "secret_scan_failed, secrets_rotation_days"
    owner: "team-devsecops"

  ### misuse: "Отсутствие расследования инцидента"
    nfr "NFR-5 Аудит критических действий"
    test: "test_audit_coverage.py"
    event_metric: "audit_event_missing, audit_coverage_percent"
    owner: "team-security"


# Спецификации Требований к Нефункциональным Аспектам (NFR)

| Scenario ID | Feature             | NFR ID        | Компоненты                       | Метрики                    | Тесты                   | Команда       | Приоритет |
| :---------- | :------------------ | :----- | :------------------------------- | :------------------------- | :---------------------- | :------------ | :-------- |
| SC-001      | Брутфорс защита     | NFR-1  | Auth Service, Rate Limiter       | auth_failures_per_ip       | Security, Integration   | Platform      | High      |
| SC-002      | Брутфорс защита     | NFR-1  | Auth Service, Rate Limiter       | ip_block_releases          | Integration, E2E        | Platform      | Medium    |
| SC-003      | Лимит медиа         | NFR-2  | Media Service, API Gateway       | media_create_requests      | Load, Integration       | Media         | High      |
| SC-004      | Лимит медиа         | NFR-2  | Media Service, Rate Limiter      | rate_limit_resets          | Integration, E2E        | Media         | Medium    |
| SC-005      | SQL инъекции        | NFR-7  | Database, API Layer              | sql_injection_attempts     | Security, Penetration   | Security      | Critical  |
| SC-006      | JWT валидация       | NFR-9  | Auth Service, API Gateway        | jwt_validation_errors      | Unit, Integration       | Platform      | High      |
| SC-007      | DoS защита          | NFR-20 | WAF, Load Balancer               | dos_attacks_blocked        | Load, Performance       | Infrastructure | Critical  |
| SC-008      | Управление сессиями | NFR-21 | Session Management, Auth         | session_timeouts           | Integration, Security   | Platform      | High      |
