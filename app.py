from flask import Flask, render_template, request, redirect, url_for, jsonify, make_response
import calendar
from datetime import datetime, date, timedelta
from database import init_db, add_event, get_events_for_month, delete_event, update_event, get_event, get_calendar_title, update_calendar_title
from weasyprint import HTML, CSS

app = Flask(__name__)

def format_12_hour_time(time_str):
    """Convert 24-hour time string to 12-hour format"""
    if not time_str:
        return ''
    try:
        time_obj = datetime.strptime(time_str, '%H:%M').time()
        return time_obj.strftime('%I:%M %p').lstrip('0')
    except:
        return time_str

def format_time_range(start_time, end_time):
    """Format time range in 12-hour format"""
    if start_time and end_time:
        return f"{format_12_hour_time(start_time)}-{format_12_hour_time(end_time)}"
    elif start_time:
        return format_12_hour_time(start_time)
    return ''

# Color mapping for events
COLOR_SCHEMES = {
    'blue': {'bg': 'bg-blue-100', 'border': 'border-blue-500', 'text': 'text-blue-800'},
    'green': {'bg': 'bg-green-100', 'border': 'border-green-500', 'text': 'text-green-800'},
    'red': {'bg': 'bg-red-100', 'border': 'border-red-500', 'text': 'text-red-800'},
    'purple': {'bg': 'bg-purple-100', 'border': 'border-purple-500', 'text': 'text-purple-800'},
    'yellow': {'bg': 'bg-yellow-100', 'border': 'border-yellow-500', 'text': 'text-yellow-800'},
    'indigo': {'bg': 'bg-indigo-100', 'border': 'border-indigo-500', 'text': 'text-indigo-800'},
    'pink': {'bg': 'bg-pink-100', 'border': 'border-pink-500', 'text': 'text-pink-800'},
    'gray': {'bg': 'bg-gray-100', 'border': 'border-gray-500', 'text': 'text-gray-800'}
}

def get_color_classes(color):
    """Get Tailwind CSS classes for event color"""
    return COLOR_SCHEMES.get(color, COLOR_SCHEMES['blue'])

def should_show_in_legend(description, max_length=25):
    """Determine if event should show in legend due to long description"""
    return description and len(description) > max_length

# PDF color mapping (grayscale with different intensities)
PDF_COLOR_SCHEMES = {
    'blue': {'bg': '#E6F3FF', 'border': '#3B82F6'},
    'green': {'bg': '#E6F7E6', 'border': '#10B981'},
    'red': {'bg': '#FEE6E6', 'border': '#EF4444'},
    'purple': {'bg': '#F3E6FF', 'border': '#8B5CF6'},
    'yellow': {'bg': '#FFFCE6', 'border': '#F59E0B'},
    'indigo': {'bg': '#E6E6FF', 'border': '#6366F1'},
    'pink': {'bg': '#FFE6F3', 'border': '#EC4899'},
    'gray': {'bg': '#F3F4F6', 'border': '#6B7280'}
}

def get_pdf_colors(color):
    """Get PDF-compatible colors"""
    return PDF_COLOR_SCHEMES.get(color, PDF_COLOR_SCHEMES['blue'])

def get_next_available_color(year, month, date_str):
    """Get next available color that doesn't clash with existing events on the same date"""
    events = get_events_for_month(year, month)
    used_colors = set()
    
    target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    
    # Find colors used on the target date
    for event in events:
        event_date = datetime.strptime(event[2], '%Y-%m-%d').date()
        event_end_date = datetime.strptime(event[9], '%Y-%m-%d').date() if len(event) > 9 and event[9] else event_date
        
        # If this event overlaps with our target date, mark its color as used
        if event_date <= target_date <= event_end_date:
            color = event[8] if len(event) > 8 and event[8] else 'blue'
            used_colors.add(color)
    
    # Return first available color
    available_colors = ['blue', 'green', 'red', 'purple', 'yellow', 'indigo', 'pink', 'gray']
    for color in available_colors:
        if color not in used_colors:
            return color
    
    # If all colors are used, cycle through them
    return available_colors[len(used_colors) % len(available_colors)]

# Make functions available in templates
app.jinja_env.globals.update(format_12_hour_time=format_12_hour_time)
app.jinja_env.globals.update(format_time_range=format_time_range)
app.jinja_env.globals.update(get_color_classes=get_color_classes)
app.jinja_env.globals.update(get_pdf_colors=get_pdf_colors)
app.jinja_env.globals.update(should_show_in_legend=should_show_in_legend)
app.jinja_env.globals.update(COLOR_SCHEMES=COLOR_SCHEMES)

with app.app_context():
    init_db()

@app.route('/')
def index():
    today = datetime.now()
    year = request.args.get('year', today.year, type=int)
    month = request.args.get('month', today.month, type=int)
    calendar_title = get_calendar_title()
    
    return render_template('index.html', year=year, month=month, calendar_title=calendar_title)

@app.route('/calendar/<int:year>/<int:month>')
def view_calendar(year, month):
    events = get_events_for_month(year, month)
    
    cal = calendar.Calendar(firstweekday=6)  # Sunday first
    month_days = cal.monthdayscalendar(year, month)
    
    events_dict = {}
    for event in events:
        event_date = datetime.strptime(event[2], '%Y-%m-%d').date()
        event_end_date = datetime.strptime(event[9], '%Y-%m-%d').date() if len(event) > 9 and event[9] else event_date
        
        # Add event to all days it spans
        current_date = event_date
        while current_date <= event_end_date:
            day = current_date.day
            if day not in events_dict:
                events_dict[day] = []
            events_dict[day].append({
                'id': event[0],
                'title': event[1],
                'start_time': event[3],
                'end_time': event[4],
                'description': event[5],
                'is_recurring': event[6],
                'recurring_type': event[7],
                'color': event[8] if len(event) > 8 else 'blue',
                'event_start_date': event_date,
                'event_end_date': event_end_date,
                'is_multi_day': event_date != event_end_date,
                'url': event[10] if len(event) > 10 else None
            })
            current_date += timedelta(days=1)
    
    month_name = calendar.month_name[month]
    calendar_title = get_calendar_title()
    
    return render_template('calendar.html', 
                         year=year, 
                         month=month,
                         month_name=month_name,
                         month_days=month_days, 
                         events=events_dict,
                         calendar_title=calendar_title)

@app.route('/add_event', methods=['GET', 'POST'])
def add_event_route():
    if request.method == 'POST':
        title = request.form['title']
        date_str = request.form['date']
        end_date_str = request.form.get('end_date', '') or date_str
        start_time_str = request.form.get('start_time', '')
        end_time_str = request.form.get('end_time', '')
        description = request.form.get('description', '')
        url = request.form.get('url', '')
        
        # Auto-select color if not specified or if "auto" is selected
        selected_color = request.form.get('color', 'auto')
        if selected_color == 'auto':
            event_date = datetime.strptime(date_str, '%Y-%m-%d')
            color = get_next_available_color(event_date.year, event_date.month, date_str)
        else:
            color = selected_color
            
        is_recurring = 'is_recurring' in request.form
        recurring_type = request.form.get('recurring_type', 'weekly') if is_recurring else None
        
        add_event(title, date_str, description, start_time_str or None, end_time_str or None, is_recurring, recurring_type, color, end_date_str, url or None)
        
        event_date = datetime.strptime(date_str, '%Y-%m-%d')
        return redirect(url_for('view_calendar', year=event_date.year, month=event_date.month))
    
    year = request.args.get('year', datetime.now().year, type=int)
    month = request.args.get('month', datetime.now().month, type=int)
    return render_template('add_event.html', year=year, month=month)

@app.route('/edit_event/<int:event_id>', methods=['GET', 'POST'])
def edit_event_route(event_id):
    if request.method == 'POST':
        title = request.form['title']
        date_str = request.form['date']
        end_date_str = request.form.get('end_date', '') or date_str
        start_time_str = request.form.get('start_time', '')
        end_time_str = request.form.get('end_time', '')
        description = request.form.get('description', '')
        url = request.form.get('url', '')
        
        # Auto-select color if "auto" is selected
        selected_color = request.form.get('color', 'blue')
        if selected_color == 'auto':
            event_date = datetime.strptime(date_str, '%Y-%m-%d')
            color = get_next_available_color(event_date.year, event_date.month, date_str)
        else:
            color = selected_color
            
        is_recurring = 'is_recurring' in request.form
        recurring_type = request.form.get('recurring_type', 'weekly') if is_recurring else None
        
        update_event(event_id, title, date_str, description, start_time_str or None, end_time_str or None, is_recurring, recurring_type, color, end_date_str, url or None)
        
        event_date = datetime.strptime(date_str, '%Y-%m-%d')
        return redirect(url_for('view_calendar', year=event_date.year, month=event_date.month))
    
    event = get_event(event_id)
    if not event:
        return redirect(url_for('index'))
    
    return render_template('edit_event.html', event=event)

@app.route('/delete_event/<int:event_id>', methods=['POST'])
def delete_event_route(event_id):
    delete_event(event_id)
    return redirect(request.referrer or url_for('index'))

@app.route('/export_pdf/<int:year>/<int:month>')
def export_pdf(year, month):
    events = get_events_for_month(year, month)
    
    cal = calendar.Calendar(firstweekday=6)  # Sunday first
    month_days = cal.monthdayscalendar(year, month)
    
    events_dict = {}
    for event in events:
        event_date = datetime.strptime(event[2], '%Y-%m-%d').date()
        event_end_date = datetime.strptime(event[9], '%Y-%m-%d').date() if len(event) > 9 and event[9] else event_date
        
        # Add event to all days it spans
        current_date = event_date
        while current_date <= event_end_date:
            day = current_date.day
            if day not in events_dict:
                events_dict[day] = []
            events_dict[day].append({
                'id': event[0],
                'title': event[1],
                'start_time': event[3],
                'end_time': event[4],
                'description': event[5],
                'is_recurring': event[6],
                'recurring_type': event[7],
                'color': event[8] if len(event) > 8 else 'blue',
                'event_start_date': event_date,
                'event_end_date': event_end_date,
                'is_multi_day': event_date != event_end_date,
                'url': event[10] if len(event) > 10 else None
            })
            current_date += timedelta(days=1)
    
    month_name = calendar.month_name[month]
    calendar_title = get_calendar_title()
    
    # Render the template for PDF
    html_string = render_template('calendar_pdf.html', 
                                year=year, 
                                month=month,
                                month_name=month_name,
                                month_days=month_days, 
                                events=events_dict,
                                calendar_title=calendar_title)
    
    # Create PDF
    html = HTML(string=html_string)
    pdf = html.write_pdf()
    
    # Create response
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename="calendar-{year}-{month:02d}.pdf"'
    
    return response

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        title = request.form['calendar_title']
        update_calendar_title(title)
        return redirect(url_for('settings'))
    
    calendar_title = get_calendar_title()
    return render_template('settings.html', calendar_title=calendar_title)

if __name__ == '__main__':
    app.run(debug=True)