from flask import Flask, render_template, request, redirect, url_for, jsonify, make_response
import calendar
from datetime import datetime, date
from database import init_db, add_event, get_events_for_month, delete_event, update_event, get_event, get_calendar_title, update_calendar_title
from weasyprint import HTML, CSS

app = Flask(__name__)

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
        event_date = datetime.strptime(event[2], '%Y-%m-%d').day
        if event_date not in events_dict:
            events_dict[event_date] = []
        events_dict[event_date].append({
            'id': event[0],
            'title': event[1],
            'start_time': event[3],
            'end_time': event[4],
            'description': event[5],
            'is_recurring': event[6],
            'recurring_type': event[7]
        })
    
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
        start_time_str = request.form.get('start_time', '')
        end_time_str = request.form.get('end_time', '')
        description = request.form.get('description', '')
        is_recurring = 'is_recurring' in request.form
        recurring_type = request.form.get('recurring_type', 'weekly') if is_recurring else None
        
        add_event(title, date_str, description, start_time_str or None, end_time_str or None, is_recurring, recurring_type)
        
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
        start_time_str = request.form.get('start_time', '')
        end_time_str = request.form.get('end_time', '')
        description = request.form.get('description', '')
        is_recurring = 'is_recurring' in request.form
        recurring_type = request.form.get('recurring_type', 'weekly') if is_recurring else None
        
        update_event(event_id, title, date_str, description, start_time_str or None, end_time_str or None, is_recurring, recurring_type)
        
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
        event_date = datetime.strptime(event[2], '%Y-%m-%d').day
        if event_date not in events_dict:
            events_dict[event_date] = []
        events_dict[event_date].append({
            'id': event[0],
            'title': event[1],
            'start_time': event[3],
            'end_time': event[4],
            'description': event[5],
            'is_recurring': event[6],
            'recurring_type': event[7]
        })
    
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