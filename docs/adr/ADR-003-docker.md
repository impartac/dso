# ADR 001: Выбор PostgreSQL с SQLAlchemy ORM
## **Status : Accepted**

## **Context:**
Требуется обеспечить изоляцию приложения:
* **NFR-4** (защита от инъекций)
* **NFR-8** (защита от DoS атак)

воспроизводимость развертывания и безопасную конфигурацию.

## **Solution:**
Использовать Docker с security-hardened образами и docker-compose для оркестрации.

## **Обоснование:**

* Изоляция процессов - ограничивает impact возможных уязвимостей (NFR-4)

* Read-only root filesystems - предотвращает модификацию контейнера при атаке

* Non-root пользователи - снижает привилегии (Principle of Least Privilege)

* Resource limits - защита от DoS через исчерпание ресурсов (NFR-8)

* Secrets management - безопасное хранение JWT ключей, DB паролей

## **Consequences:**

✅ Быстрое масштабирование при DoS атаках (NFR-8)

✅ Изоляция уязвимостей на уровне контейнера

✅ Воспроизводимая security конфигурация

⚠️ Overhead управления контейнерами

⚠️ Требует security scanning образов
