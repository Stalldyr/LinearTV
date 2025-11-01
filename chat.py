from flask_socketio import emit, join_room, leave_room
from flask import request
from datetime import datetime

# Chat state - i minnet (eller kan flyttes til database senere)
chat_rooms = {
    '#nostalgic-tv': [],
    '#random': [],
    '#help': []
}

connected_users = {}  # {session_id: {nick, room}}

def register_socket_events(socketio):
    """
    Registrer alle Socket.io event handlers
    Kalles fra app.py under oppstart
    """
    
    @socketio.on('connect')
    def handle_connect():
        """Når en bruker kobler til"""
        print(f'Client connected: {request.sid}')
        
        # Send welcome messages
        emit('system_message', {
            'text': '*** Welcome to NostalgicTV IRC Server ***',
            'time': get_current_time()
        })
        emit('system_message', {
            'text': '*** Type /help for available commands ***',
            'time': get_current_time()
        })

    @socketio.on('disconnect')
    def handle_disconnect():
        """Når en bruker kobler fra"""
        print(f'Client disconnected: {request.sid}')
        
        if request.sid in connected_users:
            user_info = connected_users[request.sid]
            
            # Notify room about user leaving
            emit('user_left', {
                'user': user_info['nick'],
                'channel': user_info['room'],
                'time': get_current_time()
            }, room=user_info['room'])
            
            del connected_users[request.sid]

    @socketio.on('join_channel')
    def handle_join_channel(data):
        """Når en bruker blir med i en kanal"""
        channel = data.get('channel', '#nostalgic-tv')
        nick = data.get('nick', f'gjest{request.sid[:4]}')
        
        # Leave old room if exists
        if request.sid in connected_users:
            old_room = connected_users[request.sid]['room']
            leave_room(old_room)
            emit('user_left', {
                'user': nick,
                'channel': old_room,
                'time': get_current_time()
            }, room=old_room)
        
        # Join new room
        join_room(channel)
        connected_users[request.sid] = {'nick': nick, 'room': channel}
        
        # Create room if doesn't exist
        if channel not in chat_rooms:
            chat_rooms[channel] = []
        
        # Notify room
        emit('user_joined', {
            'user': nick,
            'channel': channel,
            'time': get_current_time()
        }, room=channel)
        
        # Send recent messages to new user
        emit('message_history', {
            'messages': chat_rooms[channel][-50:]  # Last 50 messages
        })

    @socketio.on('send_message')
    def handle_send_message(data):
        """Når en bruker sender en melding"""
        if request.sid not in connected_users:
            return
        
        user_info = connected_users[request.sid]
        message = data.get('message', '').strip()
        
        if not message:
            return
        
        msg_data = {
            'user': user_info['nick'],
            'text': message,
            'time': get_current_time(),
            'channel': user_info['room']
        }
        
        # Save to room history
        chat_rooms[user_info['room']].append(msg_data)
        
        # Keep only last 100 messages per room
        if len(chat_rooms[user_info['room']]) > 100:
            chat_rooms[user_info['room']] = chat_rooms[user_info['room']][-100:]
        
        # Broadcast to room
        emit('new_message', msg_data, room=user_info['room'])

    @socketio.on('change_nick')
    def handle_change_nick(data):
        """Når en bruker endrer nickname"""
        if request.sid not in connected_users:
            return
        
        old_nick = connected_users[request.sid]['nick']
        new_nick = data.get('nick', old_nick).strip()
        
        if not new_nick or new_nick == old_nick:
            return
        
        room = connected_users[request.sid]['room']
        connected_users[request.sid]['nick'] = new_nick
        
        # Notify room
        emit('nick_changed', {
            'old_nick': old_nick,
            'new_nick': new_nick,
            'time': get_current_time()
        }, room=room)

    @socketio.on('send_action')
    def handle_send_action(data):
        """Når en bruker sender en /me action"""
        if request.sid not in connected_users:
            return
        
        user_info = connected_users[request.sid]
        action = data.get('action', '').strip()
        
        if not action:
            return
        
        emit('user_action', {
            'user': user_info['nick'],
            'action': action,
            'time': get_current_time()
        }, room=user_info['room'])

    @socketio.on('get_user_list')
    def handle_get_user_list():
        """Hent liste over brukere i gjeldende kanal"""
        if request.sid not in connected_users:
            return
        
        room = connected_users[request.sid]['room']
        users = [info['nick'] for sid, info in connected_users.items() 
                 if info['room'] == room]
        
        emit('user_list', {'users': users})


# Helper functions
def get_current_time():
    """Returnerer nåværende tid i HH:MM format"""
    return datetime.now().strftime('%H:%M')


def get_room_users(room):
    """Hent alle brukere i et spesifikt rom"""
    return [info['nick'] for sid, info in connected_users.items() 
            if info['room'] == room]


def get_user_count():
    """Totalt antall tilkoblede brukere"""
    return len(connected_users)


def clear_room_history(room):
    """Tøm chat-historikk for en kanal (admin-funksjon)"""
    if room in chat_rooms:
        chat_rooms[room] = []
        return True
    return False