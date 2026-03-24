from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from database import db, Task
from datetime import datetime, date
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Create database tables
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    """Home page - displays all tasks"""
    # Get filter parameters
    filter_type = request.args.get('filter', 'all')
    sort_by = request.args.get('sort', 'created_date')
    
    # Base query
    query = Task.query
    
    # Apply filters
    if filter_type == 'completed':
        query = query.filter_by(completed=True)
    elif filter_type == 'pending':
        query = query.filter_by(completed=False)
    elif filter_type == 'high':
        query = query.filter_by(priority='high', completed=False)
    elif filter_type == 'medium':
        query = query.filter_by(priority='medium', completed=False)
    elif filter_type == 'low':
        query = query.filter_by(priority='low', completed=False)
    
    # Apply sorting
    tasks = []
    if sort_by == 'title':
        tasks = query.order_by(Task.title).all()
    elif sort_by == 'priority':
        # Custom priority ordering: high, medium, low
        tasks = query.all()
        priority_order = {'high': 1, 'medium': 2, 'low': 3}
        tasks.sort(key=lambda x: priority_order.get(x.priority, 4))
    elif sort_by == 'due_date':
        tasks = query.order_by(Task.due_date).all()
    else:
        tasks = query.order_by(Task.created_date.desc()).all()
    
    # Get today's date for comparison
    today_date = date.today()
    
    return render_template('index.html', tasks=tasks, filter_type=filter_type, 
                         sort_by=sort_by, today=today_date)

@app.route('/add', methods=['GET', 'POST'])
def add_task():
    """Add a new task"""
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        priority = request.form.get('priority', 'medium')
        due_date_str = request.form.get('due_date')
        
        if not title or title.strip() == '':
            flash('Task title is required!', 'error')
            return redirect(url_for('add_task'))
        
        # Parse due date if provided
        due_date = None
        if due_date_str and due_date_str.strip():
            try:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
            except ValueError:
                flash('Invalid date format!', 'error')
                return redirect(url_for('add_task'))
        
        task = Task(
            title=title.strip(),
            description=description.strip() if description else None,
            priority=priority,
            due_date=due_date
        )
        
        try:
            db.session.add(task)
            db.session.commit()
            flash('Task added successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding task: {str(e)}', 'error')
            return redirect(url_for('add_task'))
        
        return redirect(url_for('index'))
    
    return render_template('add.html')

@app.route('/edit/<int:task_id>', methods=['GET', 'POST'])
def edit_task(task_id):
    """Edit an existing task"""
    task = Task.query.get_or_404(task_id)
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        priority = request.form.get('priority', 'medium')
        
        if not title or title.strip() == '':
            flash('Task title is required!', 'error')
            return redirect(url_for('edit_task', task_id=task_id))
        
        task.title = title.strip()
        task.description = description.strip() if description else None
        task.priority = priority
        task.completed = 'completed' in request.form
        
        due_date_str = request.form.get('due_date')
        if due_date_str and due_date_str.strip():
            try:
                task.due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
            except ValueError:
                task.due_date = None
        else:
            task.due_date = None
        
        try:
            db.session.commit()
            flash('Task updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating task: {str(e)}', 'error')
            return redirect(url_for('edit_task', task_id=task_id))
        
        return redirect(url_for('index'))
    
    return render_template('edit.html', task=task)

@app.route('/delete/<int:task_id>')
def delete_task(task_id):
    """Delete a task"""
    task = Task.query.get_or_404(task_id)
    try:
        db.session.delete(task)
        db.session.commit()
        flash('Task deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting task: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/toggle/<int:task_id>')
def toggle_task(task_id):
    """Toggle task completion status"""
    task = Task.query.get_or_404(task_id)
    task.completed = not task.completed
    try:
        db.session.commit()
        flash('Task status updated!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating task status: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/api/tasks')
def api_tasks():
    """API endpoint to get tasks as JSON"""
    tasks = Task.query.all()
    tasks_list = []
    for task in tasks:
        tasks_list.append({
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'completed': task.completed,
            'priority': task.priority,
            'created_date': task.created_date.strftime('%Y-%m-%d %H:%M:%S'),
            'due_date': task.due_date.strftime('%Y-%m-%d') if task.due_date else None
        })
    return jsonify(tasks_list)

@app.route('/stats')
def stats():
    """Get task statistics"""
    total_tasks = Task.query.count()
    completed_tasks = Task.query.filter_by(completed=True).count()
    pending_tasks = total_tasks - completed_tasks
    high_priority = Task.query.filter_by(priority='high', completed=False).count()
    
    stats_data = {
        'total': total_tasks,
        'completed': completed_tasks,
        'pending': pending_tasks,
        'high_priority': high_priority,
        'completion_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    }
    
    return jsonify(stats_data)

if __name__ == '__main__':
    app.run(debug=True)