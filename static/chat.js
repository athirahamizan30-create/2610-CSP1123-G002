let socket = io();
let currentRoom = "General"
let username = document.getElementById("username").textContent;
let roomMessages = {};

const userList = document.getElementById('active-users');

// Socket Event Listeners
socket.on('connect', () => {

    if (!currentRoom) {
        currentRoom = "General";
    }

    joinRoom(currentRoom);
});

socket.on('message', (data) =>{
    addMessage(
        data.username, 
        data.msg, 
        data.username === username ? 'own' : 'other'
    );
})

socket.on('private_message', (data) => {
    addMessage(data.from, `[Private] ${data.msg}`, 'private');
});

socket.on('status', (data) => {
    addMessage('System', data.msg, 'system');
});

socket.on('active_users', (data) => { // Note: Changed 'active.users' to 'active_users' to match your backend emit
    userList.innerHTML = data.users.map(
    (user) => 
        `<div class="user-item" onclick="openPrivateChat('${user}')">
            ${user}
        </div>`
).join('');
});

//Socket function

function addMessage(sender, message, type) {
    if (! roomMessages [currentRoom]) {
        roomMessages [currentRoom] = [];
    }

    roomMessages[currentRoom].push({ sender, message, type});

    const chat = document.getElementById('chat');
    const messageDiv = document.createElement('div');

    messageDiv.className = `message ${type}`;
    messageDiv.textContent = `${sender}: ${message}`;

    chat.appendChild(messageDiv);
    chat.scrollTop = chat.scrollHeight;
}


function sendMessage(){
    const input = document.getElementById('message');
    const message = input.value.trim();

    if (!message) return;

    const isPrivate =
        currentRoom.startsWith('dm_');

    socket.emit('message', {
        msg: message,
        room: currentRoom,
        type: isPrivate
            ? 'private'
            : 'message',

        target: isPrivate
            ? currentRoom
                .replace('dm_', '')
                .replace(username, '')
                .replace('_', '')
            : null
    });

    input.value = '';
}

// Join the room

function joinRoom(room){
    socket.emit('leave', {
        room: currentRoom
    });
    currentRoom = room;

    document.getElementById(
        'chat-title'
    ).textContent = room;

    socket.emit('join', {
        room
    });

    loadMessages(room);

    console.log(
        "Current room:",
        currentRoom
    );
}


// insert pry msg
function openPrivateChat(user){

    const roomName =
        [username, user]
        .sort()
        .join('_');

    currentRoom = `dm_${roomName}`;

    socket.emit('join_private', {
        target: user
    });

    loadMessages(currentRoom);
}


// initialise chat
let chat;
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.room-item').forEach(item => {
        if (item.textContent.trim() === currentRoom){
            item.classList.add('active-room')
        }
    })
})

async function loadMessages(room) {

    const response =
        await fetch(`/get_messages/${room}`);

    const data =
        await response.json();

    const chat =
        document.getElementById('chat');

    chat.innerHTML = "";

    data.messages.forEach(msg => {

        addMessage(
            msg.sender,
            msg.message,
            msg.sender === username
                ? 'own'
                : 'other'
        );
    });
}







