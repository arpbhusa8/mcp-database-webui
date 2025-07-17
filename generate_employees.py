import os
import psycopg2
from psycopg2.extras import execute_values
from faker import Faker
from dotenv import load_dotenv

# Load environment variables (for DB_LINK)
load_dotenv()
DB_LINK = os.getenv("DB_LINK")

# Table and columns
TABLE_NAME = "employees"
COLUMNS = [
    "name",
    "age",
    "email",
    "department",
    "salary",
    "is_active",
    "country_code"
]

# Departments and countries for random selection
departments = ["Engineering", "HR", "Sales", "Marketing", "Finance", "Support", "IT", "Legal"]
countries = ["US", "CA", "GB", "IN", "DE", "FR", "JP", "CN", "BR", "AU"]

# Number of records to generate
NUM_RECORDS = 10000

# Create table SQL
CREATE_TABLE_SQL = f"""
CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    age INTEGER NOT NULL,
    email TEXT NOT NULL,
    department TEXT NOT NULL,
    salary INTEGER NOT NULL,
    is_active BOOLEAN NOT NULL,
    country_code VARCHAR(2) NOT NULL
);
"""

# Generate fake employee data
def generate_employee(fake):
    return (
        fake.name(),
        fake.random_int(min=18, max=65),
        fake.unique.email(),
        fake.random_element(departments),
        fake.random_int(min=30000, max=200000),
        fake.boolean(chance_of_getting_true=80),
        fake.random_element(countries)
    )

def main():
    fake = Faker()
    Faker.seed(0)
    fake.unique.clear()
    employees = [generate_employee(fake) for _ in range(NUM_RECORDS)]

    # Connect to PostgreSQL
    conn = psycopg2.connect(DB_LINK)
    cur = conn.cursor()

    # Create table if not exists
    cur.execute(CREATE_TABLE_SQL)
    conn.commit()

    # Insert data in batches for efficiency
    insert_sql = f"INSERT INTO {TABLE_NAME} ({', '.join(COLUMNS)}) VALUES %s"
    batch_size = 1000
    for i in range(0, NUM_RECORDS, batch_size):
        batch = employees[i:i+batch_size]
        execute_values(cur, insert_sql, batch)
        conn.commit()
        print(f"Inserted {i+len(batch)} / {NUM_RECORDS}")

    cur.close()
    conn.close()
    print("Done!")

if __name__ == "__main__":
    main() 