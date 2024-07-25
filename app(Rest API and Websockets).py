from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, join_room
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import json
import os


app = Flask(__name__)
socketio = SocketIO(app, async_mode='threading')

DATABASE_FILE = '/home/tommy/Desktop/High Frequency Database Project/database.json'
RULES_FILE = '/home/tommy/Desktop/High Frequency Database Project/rules.json'

def load_json(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                print(f"Error decoding JSON from {filename}. Please check the file format.")
                return {}
    else:
        return {}

def save_json(data, filename):
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)

database = load_json(DATABASE_FILE)
rules = load_json(RULES_FILE)

# User credentials
users = {
    "user1": {"password": "password123", "uid": "user1"},
    "user2": {"password": "password456", "uid": "user2"}
}

# User login endpoint
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    user = users.get(username)
    if user and user['password'] == password:
        return jsonify({"uid": user['uid']}), 200
    else:
        return jsonify({"error": "Invalid credentials"}), 401

# Check permissions
def check_permissions(uid, collection, action, document=None, field=None):
    user_rules = rules.get(uid, {})
    
    if collection not in user_rules:
        return False
    
    if action == 'read':
        return user_rules[collection].get('allow_read', False)
    elif action == 'write':
        return user_rules[collection].get('allow_write', False)
    
    if document:
        if document not in user_rules[collection]:
            return False
        if action == 'read':
            return user_rules[collection][document].get('allow_read', False)
        elif action == 'write':
            return user_rules[collection][document].get('allow_write', False)
    
    if field:
        if document not in user_rules[collection]:
            return False
        if field not in user_rules[collection][document]:
            return False
        if action == 'read':
            return user_rules[collection][document][field].get('allow_read', False)
        elif action == 'write':
            return user_rules[collection][document][field].get('allow_write', False)
    
    return False

# Read structure endpoint
@app.route('/read', methods=['POST'])
def read_structure():
    data = request.json
    uid = data.get('uid')
    main_collection = data.get('main_collection')
    document = data.get('document')
    field = data.get('field')
    
    if not check_permissions(uid, main_collection, 'read', document, field):
        return jsonify({"error": "Read access is not allowed for this collection/document/field."}), 403
    
    db = load_json(DATABASE_FILE)

    if main_collection not in db:
        return jsonify({"error": f"Main collection '{main_collection}' does not exist."}), 404

    if document:
        if document not in db[main_collection]:
            return jsonify({"error": f"Document '{document}' does not exist in main collection '{main_collection}'."}), 404

        if field:
            if field not in db[main_collection][document]:
                return jsonify({"error": f"Field '{field}' does not exist in document '{document}'."}), 404
            socketio.emit('log', {'user': uid, 'action': 'read', 'collection': main_collection, 'document': document, 'field': field})
            return jsonify({field: db[main_collection][document][field]}), 200
        
        socketio.emit('log', {'user': uid, 'action': 'read', 'collection': main_collection, 'document': document})
        return jsonify(db[main_collection][document]), 200
    
    socketio.emit('log', {'user': uid, 'action': 'read', 'collection': main_collection})
    return jsonify(db[main_collection]), 200

# Write structure endpoint
@app.route('/write', methods=['POST'])
def write_structure():
    data = request.json
    uid = data.get('uid')
    main_collection = data.get('main_collection')
    document = data.get('document')
    field = data.get('field')
    content = data.get('content')
    
    if not check_permissions(uid, main_collection, 'write', document, field):
        return jsonify({"error": "Write access is not allowed for this collection/document/field."}), 403
    
    db = load_json(DATABASE_FILE)

    if main_collection not in db:
        db[main_collection] = {}
    
    if document not in db[main_collection]:
        db[main_collection][document] = {}
    
    db[main_collection][document][field] = content

    save_json(db, DATABASE_FILE)
    socketio.emit('update', {'collection': main_collection, 'document': document, 'field': field, 'content': content})
    socketio.emit('log', {'user': uid, 'action': 'write', 'collection': main_collection, 'document': document, 'field': field, 'content': content})
    return jsonify({"message": "Data successfully written."}), 200

# WebSocket event handler
@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('authenticate')
def handle_authentication(data):
    uid = data.get('uid')
    if uid in rules:
        join_room(uid)
        emit('authenticated', {'message': 'Authenticated successfully'})
    else:
        emit('error', {'message': 'Authentication failed'})

# Watchdog event handler for rules.json
class RulesHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path == RULES_FILE:
            global rules
            rules = load_json(RULES_FILE)
            print("Rules updated")

# Start the observer to watch for changes in rules.json
observer = Observer()
observer.schedule(RulesHandler(), path=os.path.dirname(RULES_FILE), recursive=False)
observer.start()

if __name__ == '__main__':
    try:
        socketio.run(app, debug=True)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
