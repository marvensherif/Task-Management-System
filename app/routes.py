from flask import request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

def routes(app):

    @app.route('/auth/register', methods=['POST'])
    def register():
        data = request.get_json()
        hashed_password = generate_password_hash(data['password'])
        conn = sqlite3.connect('DB.db')
        c = conn.cursor()
        try:
            c.execute('INSERT INTO users (username, password, is_manager) VALUES (?, ?, ?)',
                      (data['username'], hashed_password, data.get('is_manager', False)))
            conn.commit()
        except sqlite3.IntegrityError:
            return jsonify({"msg": "Username Already Exists"})
        finally:
            conn.close()
        return jsonify({"msg": "User Created Succesfully"})

    @app.route('/auth/login', methods=['POST'])
    def login():
        data = request.get_json()
        conn = sqlite3.connect('DB.db')
        c = conn.cursor()
        c.execute('SELECT id, username, password, is_manager FROM users WHERE username = ?', (data['username'],))
        user = c.fetchone()
        conn.close()
        if user and check_password_hash(user[2], data['password']):
            token = create_access_token(identity={'id': user[0], 'is_manager': user[3]})
            return jsonify("Logged In Succefully access_token = ",token)
        return jsonify({"msg": "Invalid Credentials"})

    @app.route('/api/tasks', methods=['POST'])
    @jwt_required()
    def create_task():
        current_user = get_jwt_identity()
        if not current_user['is_manager']:
            return jsonify({"msg": "Only Managers Can Create Tasks"})

        data = request.get_json()
        conn = sqlite3.connect('DB.db')
        c = conn.cursor()
        c.execute('INSERT INTO tasks (title, description, status, due_date, assignee_id) VALUES (?, ?, ?, ?, ?)',
                  (data['title'], data['description'], 'pending', data['due_date'], data['assignee_id']))
        conn.commit()
        conn.close()
        return jsonify({"msg": "Task Created Succesfully"})
    
    @app.route('/api/tasks', methods=['GET'])
    @jwt_required()
    def get_tasks():
        current_user = get_jwt_identity()
        conn = sqlite3.connect('DB.db')
        c = conn.cursor()
        if current_user['is_manager']:
            c.execute('SELECT * FROM tasks')
        else:
            c.execute('SELECT * FROM tasks WHERE assignee_id = ?', (current_user['id'],))
        tasks = c.fetchall()

        task_list = []
        for task in tasks:
            c.execute('SELECT dependent_task_id FROM task_dependencies WHERE task_id = ?', (task[0],))
            dependencies = c.fetchall()
            dependency_ids = [dep[0] for dep in dependencies]
            task_list.append({
                "id": task[0],
                "title": task[1],
                "description": task[2],
                "status": task[3],
                "due_date": task[4],
                "assignee_id": task[5],
                "dependencies": dependency_ids
            })

        conn.close()
        return jsonify(task_list)
    

    @app.route('/api/tasks/<int:task_id>', methods=['PUT'])
    @jwt_required()
    def update_task(task_id):
        current_user = get_jwt_identity()
        conn = sqlite3.connect('DB.db')
        c = conn.cursor()
        c.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
        task = c.fetchone()

        if not task:
            return jsonify({"msg": "Task Not Found"})

        data = request.get_json()
        if current_user['is_manager']:
            c.execute('UPDATE tasks SET title = ?, description = ?, status = ?, due_date = ?, assignee_id = ? WHERE id = ?',
                      (data['title'], data['description'], data['status'], data['due_date'], data['assignee_id'], task_id))
        elif task[5] == current_user['id']:
            new_status = data.get('status', task[3])
            if new_status == 'completed':
                c.execute('SELECT dependent_task_id FROM task_dependencies WHERE task_id = ?', (task_id,))
                dependencies = c.fetchall()
                for dep in dependencies:
                    c.execute('SELECT status FROM tasks WHERE id = ?', (dep[0],))
                    dep_task = c.fetchone()
                    if dep_task[0] != 'completed':
                        return jsonify({"msg": "Cannot Complete Task Until All Dependencies Are Completed"})
            c.execute('UPDATE tasks SET status = ? WHERE id = ?', (new_status, task_id))
        else:
            return jsonify({"msg": "Not authorized to update this task"})

        conn.commit()
        conn.close()
        return jsonify({"msg": "Task updated successfully"})
    

    @app.route('/api/tasks/<int:task_id>/dependencies', methods=['POST'])
    @jwt_required()
    def add_dependency(task_id):
        current_user = get_jwt_identity()
        if not current_user['is_manager']:
            return jsonify({"msg": "Only Managers Can Add Dependencies"})

        data = request.get_json()
        dependent_task_id = data['dependent_task_id']

        conn = sqlite3.connect('DB.db')
        c = conn.cursor()
        c.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
        task = c.fetchone()
        c.execute('SELECT * FROM tasks WHERE id = ?', (dependent_task_id,))
        dependent_task = c.fetchone()

        if not task or not dependent_task:
            return jsonify({"msg": "Task Or Dependent Task Not Found"})

        c.execute('INSERT INTO task_dependencies (task_id, dependent_task_id) VALUES (?, ?)',
                  (task_id, dependent_task_id))
        conn.commit()
        conn.close()
        return jsonify({"msg": "Dependency Added"})

   