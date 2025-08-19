document.addEventListener('DOMContentLoaded', () => {
    const userList = document.getElementById('user-list');
    const chatWelcome = document.getElementById('chat-welcome');
    const chatWindow = document.getElementById('chat-window');
    const chatHeader = document.getElementById('chat-with-user');
    const messageList = document.getElementById('message-list');
    const replyForm = document.getElementById('reply-form');
    const replyMessageInput = document.getElementById('reply-message');

    let activeUserId = null;

    // --- WebSocket Connection ---
    const socket = io();

    socket.on('connect', () => {
        console.log('Connected to WebSocket server!');
    });

    socket.on('new_message', (msg) => {
        console.log('Received new message:', msg);
        // Only append the message if the chat for that user is currently active
        if (msg.user_id === activeUserId) {
            appendMessage(msg);
            messageList.scrollTop = messageList.scrollHeight;
        }
        // TODO: Add a notification indicator to the user list if the chat is not active
    });

    socket.on('disconnect', () => {
        console.log('Disconnected from WebSocket server.');
    });


    // --- REST API Functions ---

    async function fetchUsers() {
        try {
            const response = await fetch('/dashboard/users');
            if (!response.ok) {
                if (response.status === 401) alert('Authentication failed.');
                throw new Error('Failed to fetch users');
            }
            const users = await response.json();
            userList.innerHTML = '';
            users.forEach(user => {
                const li = document.createElement('li');
                li.textContent = user.whatsapp_id;
                li.dataset.userId = user.id;
                li.addEventListener('click', () => selectUser(user.id, user.whatsapp_id));
                userList.appendChild(li);
            });
        } catch (error) {
            console.error(error);
            userList.innerHTML = '<li class="error">Failed to load users.</li>';
        }
    }

    async function fetchMessages(userId) {
        try {
            const response = await fetch(`/dashboard/users/${userId}/messages`);
            if (!response.ok) throw new Error('Failed to fetch messages');
            const messages = await response.json();
            renderMessages(messages);
        } catch (error) {
            console.error(error);
            messageList.innerHTML = '<li class="error">Failed to load messages.</li>';
        }
    }

    // --- UI Manipulation ---

    function selectUser(userId, whatsappId) {
        activeUserId = userId;
        chatWelcome.classList.add('hidden');
        chatWindow.classList.remove('hidden');

        document.querySelectorAll('#user-list li').forEach(li => {
            li.classList.remove('active');
            if(li.dataset.userId == userId) li.classList.add('active');
        });

        chatHeader.textContent = `Chat with ${whatsappId}`;
        messageList.innerHTML = '<li>Loading messages...</li>';
        fetchMessages(userId);
    }

    function renderMessages(messages) {
        messageList.innerHTML = '';
        messages.forEach(appendMessage);
        messageList.scrollTop = messageList.scrollHeight;
    }

    function appendMessage(msg) {
        const div = document.createElement('div');
        div.classList.add('message', msg.direction);
        div.textContent = msg.content;
        messageList.appendChild(div);
    }

    // --- Event Listeners ---

    replyForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        if (!activeUserId) return;
        const text = replyMessageInput.value;
        if (!text.trim()) return;

        // The message is sent via POST, and the server will emit it back via WebSocket
        // This means we don't need to manually append it here anymore.
        try {
            const response = await fetch(`/dashboard/users/${activeUserId}/messages`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text })
            });

            if (!response.ok) throw new Error('Failed to send message');

            // Clear the input field after successful sending
            replyMessageInput.value = '';
        } catch (error) {
            console.error(error);
            alert('Failed to send message. Please try again.');
        }
    });

    // Initial fetch
    fetchUsers();
});
