CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    slack_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL, 
    email VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE streams (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    owner_id INT REFERENCES users(id)
)