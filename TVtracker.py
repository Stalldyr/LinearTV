import sqlite3
from datetime import datetime

DATABASE = 'data/traffic.db'

def get_db_connection():
    """Åpne tilkobling til database"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row 
    return conn

def init_db():
    """Opprett tabellen hvis den ikke finnes (kjør ved oppstart)"""
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS program_views (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            program_id INTEGER NOT NULL,
            ip_address TEXT,
            viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            time_spent INTEGER DEFAULT 0
            
        )
    ''')
    conn.commit()
    conn.close()
    print("Database initialisert!")

def log_view(program_id, ip_address):
    """Logg at noen så et program"""
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO program_views (program_id, ip_address) VALUES (?, ?)',
        (program_id, ip_address)
    )
    conn.commit()
    conn.close()

def get_view_count(program_id):
    """Hent totalt antall visninger for et program"""
    conn = get_db_connection()
    cursor = conn.execute(
        'SELECT COUNT(*) as count FROM program_views WHERE program_id = ?',
        (program_id,)
    )
    count = cursor.fetchone()['count']
    conn.close()
    return count

def get_unique_views(program_id):
    """Hent antall unike IP-adresser som har sett programmet"""
    conn = get_db_connection()
    cursor = conn.execute(
        'SELECT COUNT(DISTINCT ip_address) as count FROM program_views WHERE program_id = ?',
        (program_id,)
    )
    count = cursor.fetchone()['count']
    conn.close()
    return count

def update_time(seconds, program_id, ip_address):
    conn = get_db_connection()
    conn.execute('''
        UPDATE program_views 
        SET ime_spent = ? 
        WHERE program_id = ? 
        AND ip_address = ?
        ORDER BY viewed_at DESC 
        LIMIT 1
    ''', (seconds, program_id, ip_address))
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()