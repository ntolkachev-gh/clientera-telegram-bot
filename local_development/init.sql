-- Инициализация базы данных для бота
-- Этот файл выполняется при первом запуске PostgreSQL контейнера

-- Создаем расширения
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Создаем схему для бота
CREATE SCHEMA IF NOT EXISTS bot;

-- Устанавливаем права
GRANT ALL PRIVILEGES ON SCHEMA bot TO bot_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA bot TO bot_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA bot TO bot_user;

-- Устанавливаем поиск по схеме
ALTER DATABASE bot_db SET search_path TO bot, public;

-- Комментарий к базе данных
COMMENT ON DATABASE bot_db IS 'База данных для бота салона красоты';

