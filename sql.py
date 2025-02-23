import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

database_url = os.getenv('DATABASE_URL')

try:
    conn = psycopg2.connect(database_url)
    cur = conn.cursor()

    # Create tables (only if they don't exist)
    create_users_table = """
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        slack_id VARCHAR(50) UNIQUE NOT NULL,
        name VARCHAR(100) NOT NULL, 
        email VARCHAR(100) NOT NULL,
        created_at TIMESTAMP DEFAULT NOW(),
        settings JSONB DEFAULT '{"ads_enabled": true}'
    );
    """
    create_streams_table = """
    CREATE TABLE IF NOT EXISTS streams (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT NOW(),
        owner_id INT REFERENCES users(id),
        likes INT DEFAULT 0,
        dislikes INT DEFAULT 0,
        category_id INT REFERENCES categories(id)
    );
    """


    create_votes_table = """
    CREATE TABLE IF NOT EXISTS votes (
        user_id INT REFERENCES users(id),
        stream_id INT REFERENCES streams(id),
        vote_type VARCHAR(7) CHECK (vote_type IN ('like', 'dislike')),
        PRIMARY KEY (user_id, stream_id)
    );
    """

    create_categories_table = """
    CREATE TABLE IF NOT EXISTS categories (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) UNIQUE NOT NULL
    );
    """

    cur.execute(create_users_table)
    cur.execute(create_categories_table)
    cur.execute(create_votes_table)

    # Alter the streams table
    alter_streams_table = """
    ALTER TABLE streams
    ADD COLUMN IF NOT EXISTS category_id INT REFERENCES categories(id);
    """

    cur.execute(alter_streams_table)

    # Insert initial data (only categories)
    insert_categories = """
    INSERT INTO categories (name) VALUES ('Gamedev'), ('3D Printing'), ('PCB'), ('YSWS');
    """

    cur.execute(insert_categories)

    conn.commit()
    print("Tables created/altered and categories inserted successfully!")

except psycopg2.Error as e:
    print(f"Error: {e}")

finally:
    if 'cur' in locals() and cur is not None:
        cur.close()
    if 'conn' in locals() and conn is not None:
        conn.close()