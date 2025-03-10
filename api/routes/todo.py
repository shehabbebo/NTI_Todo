from flask import request, jsonify
from .. import api_bp
from models import Todo, db
from .shared_functions import process_image, delete_image
from flask_jwt_extended import jwt_required, get_jwt_identity

TODO_UPLOAD_FOLDER = 'todos'  

@api_bp.route('/new_task', methods=['POST'])
@jwt_required()
def create_task():
    current_user_id = get_jwt_identity()

    title = request.form.get('title', '')
    description = request.form.get('description', '')

    image_path = None
    if 'image' in request.files:
        file = request.files['image']
        image_path, error = process_image(file, TODO_UPLOAD_FOLDER) 
        
        if error:
            return jsonify({"message": error, "status": False}), 400 
    

    todo = Todo(image_path=image_path, title=title, description=description, user_id=current_user_id)
    db.session.add(todo)
    db.session.commit()

    return jsonify({
        "status": True,
        "message": "Task created successfully"
    }), 201


@api_bp.route('/tasks', methods=['GET'])
def get_all_tasks():
    tasks = Todo.query.all()
    
    tasks_list = list(map(lambda task: {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "image_path": task.image_path
    }, tasks))

    response = {
        "status": True,
        "tasks": tasks_list
    }
    return jsonify(response), 200



@api_bp.route('/tasks/<int:id>', methods=['PUT'])
@jwt_required()
def update_task(id):
    current_user_id = get_jwt_identity()

    title = request.form.get('title')
    description = request.form.get('description')
    image = request.files.get('image') 

    if not id:
        return jsonify({"status": False, "message": "id is required"}), 400

    try:
        id = int(id)
    except ValueError:
        return {"message": "id must be an integer", "status": False}, 400

    task = Todo.query.get(id)
    if not task:
        return jsonify({"status": False, "message": "Task not found"}), 404
    
    if task.user_id != current_user_id:
        return jsonify({"status": False, "message": "Unauthorized"}), 403

    if title:
        task.title = title
    if description:
        task.description = description

    if image:
        image_path, error = process_image(image, TODO_UPLOAD_FOLDER, task.image_path) 
        if error:
            return jsonify({"message": error, "status": False}), 400 
        
        task.image_path = image_path

    db.session.commit()

    return jsonify({"status": True, "message": "Task updated successfully", "task": {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "image_path": task.image_path
    }}), 200


@api_bp.route('/tasks/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_task(id):
    current_user_id = get_jwt_identity()

    if not id:
        return jsonify({"status": False, "message": "id is required"}), 400

    try:
        id = int(id)
    except ValueError:
        return jsonify({"message": "id must be an integer", "status": False}), 400

    task = Todo.query.get(id)
    if not task:
        return jsonify({"status": False, "message": "Task not found"}), 404
    
    if task.user_id != current_user_id:
        return jsonify({"status": False, "message": "Unauthorized"}), 403

    if task.image_path:
        error = delete_image(task.image_path)
        if error:
            return jsonify({"message": error, "status": False}), 500

    # Delete the slider from the database
    db.session.delete(task)
    db.session.commit()

    return jsonify({"status": True, "message": "Task deleted successfully"}), 200


@api_bp.route('/my_tasks', methods=['GET'])
@jwt_required()
def get_user_tasks():
    current_user_id = get_jwt_identity()

    if not current_user_id:
        return jsonify({"status": False, "message": "Unauthorized"}), 403

    # Get the tasks for the current user

    tasks = Todo.query.filter_by(user_id=current_user_id).all()

    # Prepare the response
    tasks_list = [
        {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "image_path": task.image_path
        }
        for task in tasks
    ]

    return jsonify({
        "status": True,
        "tasks": tasks_list
    }), 200


