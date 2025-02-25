CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    slack_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL, 
    email VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    settings JSONB DEFAULT '{"ads_enabled": true}'
);

CREATE TABLE streams (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    owner_id INT REFERENCES users(id),
    likes INT DEFAULT 0,
    dislikes INT DEFAULT 0,
    category_id INT REFERENCES categories(id),
    video_filename TEXT
);

CREATE TABLE votes (
    user_id INT REFERENCES users(id),
    stream_id INT REFERENCES streams(id),
    vote_type VARCHAR(7) CHECK (vote_type IN ('like', 'dislike')),
    PRIMARY KEY (user_id, stream_id)
);

CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL
);

