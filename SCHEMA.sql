CREATE TABLE IF NOT EXISTS teams(
    id BIGINT PRIMARY KEY,
    token TEXT UNIQUE NOT NULL,
    invite TEXT UNIQUE NOT NULL,
    name TEXT UNIQUE NOT NULL,
    github TEXT,
    owner BIGINT UNIQUE NOT NULL,
    role_id BIGINT UNIQUE NOT NULL,
    text_id BIGINT UNIQUE NOT NULL,
    voice_id BIGINT UNIQUE NOT NULL,
    created TIMESTAMP DEFAULT (now() at time zone 'utc')
);