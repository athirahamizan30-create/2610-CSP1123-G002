let socket = io();
let currentRoom = "General"
let roomMessages = {};

const userList = document.getElementById('active-users');

// Socket Event Listeners
socket.on('connect', () =>{
    joinRoom(currentRoom);
});

socket.on('message', (data) =>{
    addMessage(
        data.username, 
        data.msg, 
        data.username === username ? 'own' : 'other',
        data.timestamp
    );
})

socket.on('private_message', (data) => {
    addMessage(data.from, `[Private] ${data.msg}`, 'private');
});

socket.on('status', (data) => {
    addMessage('System', data.msg, 'system');
});

socket.on('active_users', (data) => { 

    userList.innerHTML = data.users.map(
    (user) => 
        
        `<div class="user-item" onclick="openPrivateChat('${user}')">
            ${user}
        </div>`
).join('');
});

//Socket function

function addMessage(sender, message, type, timestamp) {
    if (! roomMessages [currentRoom]) {
        roomMessages [currentRoom] = [];
    }

    roomMessages[currentRoom].push({ sender, message, type, timestamp});

    const chat = document.getElementById('chat');
    const messageDiv = document.createElement('div');

    messageDiv.className = `message ${type}`;

     const time = timestamp
        ? new Date(timestamp).toLocaleString()
        : "";

    messageDiv.innerHTML = `
    <div class="sender">${sender}</div>
    <div class="text">${message}</div>
    <div class="time">${time}</div>
    `;

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

    document
    .getElementById(
        'view-profile-btn'
    ).style.display =
    'none';

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

    document.getElementById('chat-title').textContent =user;
    
    const profileBtn =document.getElementById('view-profile-btn');
    profileBtn.style.display =
        'block';

    profileBtn.onclick =
    function () {
        openProfilePopup(user);
    };

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
            msg.sender === username ? 'own' : 'other',
            msg.timestamp
        );
    });
}

async function loadRecentChats() {

    const response =
        await fetch('/private_chats');

    const data =
        await response.json();

    const chatList =
        document.getElementById(
            'recent-chats'
        );

    chatList.innerHTML =
        data.chats.map(user => `
            <div
                class="user-item"
                onclick="openPrivateChat('${user}')"
            >
                ${user}
            </div>
        `).join('');
}

document.addEventListener(
    'DOMContentLoaded',
    () => {

    loadRecentChats();

    document
    .querySelectorAll(
        '.room-item'
    )
    .forEach(item => {

        if (
            item.textContent.trim()
            === currentRoom
        ) {
            item.classList
            .add(
                'active-room'
            );
        }
    });
});

async function openProfilePopup(user){

    const response =
        await fetch(
            `/get_profile/${user}`
        );

    const data =
        await response.json();

    document.getElementById(
        'popup-profile-pic'
    ).src =
        data.image;

    document.getElementById(
        'popup-username'
    ).textContent =
        data.username;

    document.getElementById(
        'popup-fullname'
    ).textContent =
        data.full_name
        || 'Not Set';

    document.getElementById(
        'popup-email'
    ).textContent =
        data.email
        || 'Not Set';

    document.getElementById(
        'popup-about'
    ).textContent =
        data.about_me
        || 'No description';

    document.getElementById(
        'profile-popup'
    ).style.display =
        'flex';
}

function closeProfilePopup(){

    document.getElementById(
        'profile-popup'
    ).style.display =
        'none';
}

