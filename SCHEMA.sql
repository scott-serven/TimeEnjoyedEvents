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
    registered TIMESTAMP DEFAULT (now() at time zone 'utc')
);
