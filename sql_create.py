import os
import subprocess

POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "your_password_here"
POSTGRES_HOST = "0.0.0.0"
POSTGRES_PORT = "5432"
POSTGRES_DB = "postgres"

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

def create_postgres_container():
    docker_command = [
        "docker", "run", "--name", "postgres_container",
        "-e", f"POSTGRES_USER={POSTGRES_USER}",
        "-e", f"POSTGRES_PASSWORD={POSTGRES_PASSWORD}",
        "-e", f"POSTGRES_DB={POSTGRES_DB}",
        "-p", f"{POSTGRES_PORT}:{POSTGRES_PORT}",
        "-d", "postgres:latest"
    ]
    subprocess.run(docker_command)

def create_env_file():
    with open(".addtoenv", "w") as env_file:
        env_file.write(f"# PostgreSQL Configuration\n")
        env_file.write(f"POSTGRES_USER={POSTGRES_USER}\n")
        env_file.write(f"POSTGRES_PASSWORD={POSTGRES_PASSWORD}\n")
        env_file.write(f"POSTGRES_HOST={POSTGRES_HOST}\n")
        env_file.write(f"POSTGRES_PORT={POSTGRES_PORT}\n")
        env_file.write(f"POSTGRES_DB={POSTGRES_DB}\n")
        env_file.write(f"\n# Full Database URL (constructed from above)\n")
        env_file.write(f"DATABASE_URL={DATABASE_URL}\n")

if __name__ == "__main__":
    create_postgres_container()
    create_env_file()
    print(".env file and PostgreSQL container created successfully!")
