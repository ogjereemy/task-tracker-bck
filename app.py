from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
from datetime import datetime

app = Flask(__name__)
CORS(app)

def init_db():
    with sqlite3.connect('tasks.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                completed BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Check if created_at column exists, add if not (for existing databases)
        cursor.execute("PRAGMA table_info(tasks)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'created_at' not in columns:
            cursor.execute('ALTER TABLE tasks ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
            # Set created_at for existing tasks to current time
            cursor.execute('UPDATE tasks SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL')
        conn.commit()

init_db()

def get_task(task_id):
    with sqlite3.connect('tasks.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, title, completed, created_at FROM tasks WHERE id = ?', (task_id,))
        row = cursor.fetchone()
        if row:
            return {'id': row[0], 'title': row[1], 'completed': bool(row[2]), 'created_at': row[3]}
        return None

@app.route('/tasks', methods=['POST'])
def add_task():
    data = request.json
    title = data.get('title')
    if not title:
        return jsonify({'error': 'Title is required'}), 400
    
    with sqlite3.connect('tasks.db') as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO tasks (title, created_at) VALUES (?, ?)', 
                      (title, datetime.utcnow().isoformat()))
        task_id = cursor.lastrowid
        conn.commit()
    
    task = get_task(task_id)
    return jsonify({'message': 'Task added successfully', 'task': task}), 201

@app.route('/tasks', methods=['GET'])
def get_tasks():
    with sqlite3.connect('tasks.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, title, completed, created_at FROM tasks ORDER BY created_at DESC')
        tasks = [
            {'id': row[0], 'title': row[1], 'completed': bool(row[2]), 'created_at': row[3]}
            for row in cursor.fetchall()
        ]
    return jsonify(tasks)

@app.route('/tasks/<int:task_id>', methods=['PATCH'])
def toggle_task_completion(task_id):
    data = request.json
    completed = data.get('completed')
    if completed is None:
        return jsonify({'error': 'Completed status is required'}), 400

    task = get_task(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404

    with sqlite3.connect('tasks.db') as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE tasks SET completed = ? WHERE id = ?', (int(completed), task_id))
        conn.commit()

    task = get_task(task_id)
    return jsonify({'message': 'Task completion updated', 'task': task})

@app.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task_title(task_id):
    data = request.json
    title = data.get('title')
    if not title:
        return jsonify({'error': 'Title is required'}), 400

    task = get_task(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404

    with sqlite3.connect('tasks.db') as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE tasks SET title = ? WHERE id = ?', (title, task_id))
        conn.commit()

    task = get_task(task_id)
    return jsonify({'message': 'Task title updated', 'task': task})

@app.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    task = get_task(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404

    with sqlite3.connect('tasks.db') as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
        conn.commit()

    return jsonify({'message': 'Task deleted successfully'})

if __name__ == '__main__':
    app.run(debug=True)