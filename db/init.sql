-- Создание расширения для UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Удаление существующих типов если они есть (для пересоздания)
DROP TYPE IF EXISTS user_role CASCADE;
DROP TYPE IF EXISTS media_type CASCADE;
DROP TYPE IF EXISTS media_status CASCADE;

-- Создание enum типов с правильными именами
CREATE TYPE user_role AS ENUM ('USER', 'ADMIN');
CREATE TYPE media_type AS ENUM ('IMAGE', 'VIDEO', 'AUDIO', 'DOCUMENT');
CREATE TYPE media_status AS ENUM ('DRAFT', 'PUBLISHED', 'ARCHIVED', 'DELETED');

-- Таблица пользователей
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL UNIQUE,
    role user_role NOT NULL DEFAULT 'USER',
    hash_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Таблица медиа контента
CREATE TABLE media (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    kind media_type NOT NULL,
    name VARCHAR(255) NOT NULL,
    title VARCHAR(255) NOT NULL,
    status media_status NOT NULL DEFAULT 'DRAFT',
    owner_id UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_media_owner
        FOREIGN KEY (owner_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);

-- Таблица попыток входа
CREATE TABLE login_attempts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ip_address VARCHAR(45) NOT NULL,
    user_id UUID NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    successful BOOLEAN NOT NULL DEFAULT FALSE,
    user_agent TEXT,
    user_agent_hash VARCHAR(64),
    failure_reason VARCHAR(255),
    CONSTRAINT fk_login_attempts_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);

-- Индексы для таблицы users
CREATE INDEX ix_users_email ON users(email);
CREATE INDEX ix_users_created_at ON users(created_at);

-- Индексы для таблицы media
CREATE INDEX ix_media_owner_status ON media(owner_id, status);
CREATE INDEX ix_media_kind_status ON media(kind, status);
CREATE INDEX ix_media_created_at ON media(created_at);

-- Индексы для таблицы login_attempts
CREATE INDEX ix_login_attempts_ip_timestamp ON login_attempts(ip_address, timestamp);
CREATE INDEX ix_login_attempts_user_timestamp ON login_attempts(user_id, timestamp);
CREATE INDEX ix_login_attempts_successful ON login_attempts(successful);
CREATE INDEX ix_login_attempts_user_agent_hash ON login_attempts(user_agent_hash);

-- Функция для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Триггеры для автоматического обновления updated_at
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_media_updated_at
    BEFORE UPDATE ON media
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Функция для автоматического хеширования user_agent
CREATE OR REPLACE FUNCTION hash_user_agent()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.user_agent IS NOT NULL THEN
        NEW.user_agent_hash = encode(sha256(NEW.user_agent::bytea), 'hex');
    ELSE
        NEW.user_agent_hash = NULL;
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Триггер для автоматического хеширования user_agent
CREATE TRIGGER hash_login_attempts_user_agent
    BEFORE INSERT OR UPDATE ON login_attempts
    FOR EACH ROW
    EXECUTE FUNCTION hash_user_agent();
