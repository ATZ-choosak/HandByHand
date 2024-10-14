import socketio

sio = socketio.AsyncServer(async_mode="asgi")

# Define the event handlers
@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")
    await sio.emit("message", {"data": "Connected!"}, to=sid)

@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")

@sio.event
async def message(sid, data):
    print(f"Message from {sid}: {data}")
    await sio.emit("response", {"data": f"Message received: {data}"}, to=sid)

@sio.on('send_message')
async def handle_send_message(sid, data):
    room = data['room']
    await sio.emit('new_message', {'room' : room})

@sio.on('join_room')
async def handle_join_room(sid, data):
    room = data['room']
    sio.enter_room(sid, room)
    print(F"{sid} joined {room}")
    await sio.emit('new_message', {'msg': f'{sid} has joined room {room}'}, room=room)