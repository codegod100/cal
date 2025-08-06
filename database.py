import sqlite3
from datetime import datetime, timedelta

def init_db():
    conn = sqlite3.connect('calendar.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            date DATE NOT NULL,
            time TEXT,
            description TEXT,
            is_recurring BOOLEAN DEFAULT 0,
            recurring_type TEXT DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Add new columns if they don't exist (for existing databases)
    try:
        cursor.execute('ALTER TABLE events ADD COLUMN time TEXT')
    except sqlite3.OperationalError:
        pass
        
    try:
        cursor.execute('ALTER TABLE events ADD COLUMN is_recurring BOOLEAN DEFAULT 0')
    except sqlite3.OperationalError:
        pass
        
    try:
        cursor.execute('ALTER TABLE events ADD COLUMN recurring_type TEXT DEFAULT NULL')
    except sqlite3.OperationalError:
        pass
        
    try:
        cursor.execute('ALTER TABLE events ADD COLUMN start_time TEXT')
    except sqlite3.OperationalError:
        pass
        
    try:
        cursor.execute('ALTER TABLE events ADD COLUMN end_time TEXT')
    except sqlite3.OperationalError:
        pass
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            calendar_title TEXT DEFAULT 'Event Calendar'
        )
    ''')
    
    cursor.execute('INSERT OR IGNORE INTO settings (id, calendar_title) VALUES (1, "Event Calendar")')
    
    conn.commit()
    conn.close()

def add_event(title, date, description='', start_time=None, end_time=None, is_recurring=False, recurring_type=None):
    conn = sqlite3.connect('calendar.db')
    cursor = conn.cursor()
    
    if is_recurring and recurring_type == 'weekly':
        # Create recurring events for the next 12 months
        base_date = datetime.strptime(date, '%Y-%m-%d').date()
        for i in range(52):  # 52 weeks = ~1 year
            recurring_date = base_date + timedelta(weeks=i)
            cursor.execute('''
                INSERT INTO events (title, date, start_time, end_time, description, is_recurring, recurring_type)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (title, recurring_date.strftime('%Y-%m-%d'), start_time, end_time, description, is_recurring, recurring_type))
    else:
        cursor.execute('''
            INSERT INTO events (title, date, start_time, end_time, description, is_recurring, recurring_type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (title, date, start_time, end_time, description, is_recurring, recurring_type))
    
    conn.commit()
    conn.close()

def get_events_for_month(year, month):
    conn = sqlite3.connect('calendar.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, title, date, start_time, end_time, description, is_recurring, recurring_type
        FROM events
        WHERE strftime('%Y', date) = ? AND strftime('%m', date) = ?
        ORDER BY date, start_time
    ''', (str(year), f'{month:02d}'))
    
    events = cursor.fetchall()
    conn.close()
    return events

def delete_event(event_id):
    conn = sqlite3.connect('calendar.db')
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM events WHERE id = ?', (event_id,))
    
    conn.commit()
    conn.close()

def update_event(event_id, title, date, description='', start_time=None, end_time=None, is_recurring=False, recurring_type=None):
    conn = sqlite3.connect('calendar.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE events 
        SET title = ?, date = ?, start_time = ?, end_time = ?, description = ?, is_recurring = ?, recurring_type = ?
        WHERE id = ?
    ''', (title, date, start_time, end_time, description, is_recurring, recurring_type, event_id))
    
    conn.commit()
    conn.close()

def get_event(event_id):
    conn = sqlite3.connect('calendar.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, title, date, start_time, end_time, description, is_recurring, recurring_type FROM events WHERE id = ?', (event_id,))
    event = cursor.fetchone()
    
    conn.close()
    return event

def get_calendar_title():
    conn = sqlite3.connect('calendar.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT calendar_title FROM settings WHERE id = 1')
    result = cursor.fetchone()
    
    conn.close()
    return result[0] if result else 'Event Calendar'

def update_calendar_title(title):
    conn = sqlite3.connect('calendar.db')
    cursor = conn.cursor()
    
    cursor.execute('UPDATE settings SET calendar_title = ? WHERE id = 1', (title,))
    
    conn.commit()
    conn.close()