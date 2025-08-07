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
        
    try:
        cursor.execute('ALTER TABLE events ADD COLUMN color TEXT DEFAULT "blue"')
    except sqlite3.OperationalError:
        pass
        
    try:
        cursor.execute('ALTER TABLE events ADD COLUMN end_date DATE')
    except sqlite3.OperationalError:
        pass
        
    try:
        cursor.execute('ALTER TABLE events ADD COLUMN url TEXT')
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

def add_event(title, date, description='', start_time=None, end_time=None, is_recurring=False, recurring_type=None, color='blue', end_date=None, url=None):
    conn = sqlite3.connect('calendar.db')
    cursor = conn.cursor()
    
    # Always store only one event, even if recurring
    cursor.execute('''
        INSERT INTO events (title, date, start_time, end_time, description, is_recurring, recurring_type, color, end_date, url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (title, date, start_time, end_time, description, is_recurring, recurring_type, color, end_date, url))
    
    conn.commit()
    conn.close()

def get_events_for_month(year, month):
    conn = sqlite3.connect('calendar.db')
    cursor = conn.cursor()
    
    # Get all events (including recurring ones from any date)
    cursor.execute('''
        SELECT id, title, date, start_time, end_time, description, is_recurring, recurring_type, color, end_date, url
        FROM events
        ORDER BY date, start_time
    ''')
    
    all_events = cursor.fetchall()
    conn.close()
    
    # Generate events for the requested month
    month_events = []
    target_month_start = datetime(year, month, 1).date()
    if month == 12:
        target_month_end = datetime(year + 1, 1, 1).date() - timedelta(days=1)
    else:
        target_month_end = datetime(year, month + 1, 1).date() - timedelta(days=1)
    
    for event in all_events:
        event_id, title, date_str, start_time, end_time, description, is_recurring, recurring_type, color, end_date_str, url = event
        event_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        event_end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else event_date
        
        if is_recurring and recurring_type == 'weekly':
            # Generate weekly recurring instances for this month
            current_date = event_date
            # Find the first occurrence in or before the target month
            while current_date > target_month_start:
                current_date -= timedelta(weeks=1)
            while current_date < target_month_start:
                current_date += timedelta(weeks=1)
            
            # Add all weekly occurrences within the month
            while current_date <= target_month_end:
                # For recurring events, calculate the end date based on the duration
                duration = event_end_date - event_date
                current_end_date = current_date + duration
                month_events.append((event_id, title, current_date.strftime('%Y-%m-%d'), 
                                   start_time, end_time, description, is_recurring, recurring_type, color, current_end_date.strftime('%Y-%m-%d'), url))
                current_date += timedelta(weeks=1)
        else:
            # Non-recurring event - include if it overlaps with the target month
            if event_date <= target_month_end and event_end_date >= target_month_start:
                month_events.append(event)
    
    # Sort by date and time
    month_events.sort(key=lambda e: (e[2], e[3] or ''))
    return month_events

def delete_event(event_id):
    conn = sqlite3.connect('calendar.db')
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM events WHERE id = ?', (event_id,))
    
    conn.commit()
    conn.close()

def update_event(event_id, title, date, description='', start_time=None, end_time=None, is_recurring=False, recurring_type=None, color='blue', end_date=None, url=None):
    conn = sqlite3.connect('calendar.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE events 
        SET title = ?, date = ?, start_time = ?, end_time = ?, description = ?, is_recurring = ?, recurring_type = ?, color = ?, end_date = ?, url = ?
        WHERE id = ?
    ''', (title, date, start_time, end_time, description, is_recurring, recurring_type, color, end_date, url, event_id))
    
    conn.commit()
    conn.close()

def get_event(event_id):
    conn = sqlite3.connect('calendar.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, title, date, start_time, end_time, description, is_recurring, recurring_type, color, end_date, url FROM events WHERE id = ?', (event_id,))
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