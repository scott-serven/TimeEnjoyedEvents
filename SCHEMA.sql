CREATE TABLE IF NOT EXISTS teams(
    team_id BIGINT PRIMARY KEY,
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

CREATE TABLE IF NOT EXISTS members(
    member_id BIGINT PRIMARY KEY,
    languages INT[],
    timezone INTERVAL,
    solo BOOLEAN,
    team_id BIGINT,
    registered TIMESTAMP DEFAULT (now() at time zone 'utc'),
    FOREIGN KEY (team_id) REFERENCES teams (team_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS error_log(
    id SERIAL PRIMARY KEY,
    channel BIGINT,
    invoker BIGINT,
    command TEXT,
    error TEXT,
    traceback TEXT,
    created TIMESTAMP DEFAULT (now() at time zone 'utc')
);
