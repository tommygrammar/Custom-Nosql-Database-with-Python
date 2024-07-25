import socketio

sio = socketio.Client()

@sio.event
def connect():
    print('connection established')
    sio.emit('authenticate', {'uid': 'user1'})

@sio.event
def authenticated(data):
    print('Authenticated:', data)

@sio.event
def update(data):
    print('Update received:', data)

@sio.event
def log(data):
    print('Log entry:', data)

@sio.event
def disconnect():
    print('disconnected from server')

if __name__ == '__main__':
    sio.connect('http://127.0.0.1:5000')
    sio.wait()
