from configs import Config
import sqlite3


class Database:
    def __init__(self, database=Config.DATABASE, schema=Config.SCHEMA):
        self.database = database
        self.schema = schema
        self.create_db()
        self.table_info()
        
    def create_db(self):
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        
        with open(self.schema) as f:
            schema = f.read()
        
        cursor.executescript(schema)
        conn.commit()
        print("Database and tables created successfully.")
        conn.close()
        
    def table_info(self):
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        for table in tables:
            table_name = table[0]
            print(f"{table_name}:")
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            for column in columns:
                print(column)
            print("\n")

        conn.close()

    
if __name__ == "__main__":
    Database()