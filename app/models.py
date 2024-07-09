import sqlite3

def init_db():
    conn = sqlite3.connect('DB.db')
    c = conn.cursor()
    #creating user table if not exixt
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            is_manager BOOLEAN NOT NULL
        )
    ''')
    #creating taks table if not exixt
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            due_date TEXT NOT NULL,
            assignee_id INTEGER,
            FOREIGN KEY (assignee_id) REFERENCES users (id)
        )
    ''')
    #creating task_dependencies table if not exixt
    c.execute('''
        CREATE TABLE IF NOT EXISTS task_dependencies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            dependent_task_id INTEGER NOT NULL,
            FOREIGN KEY (task_id) REFERENCES tasks (id),
            FOREIGN KEY (dependent_task_id) REFERENCES tasks (id)
        )
    ''')
    conn.commit()
    conn.close()
