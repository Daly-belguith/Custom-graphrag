/* 
   ========================================
   GraphRAG Platform - Frontend Logic
   ========================================
*/

const API_BASE = '/api/v1';

// State
let currentUser = null;
let currentToken = localStorage.getItem('graphrag_jwt');

// --- Initialization ---

document.addEventListener('DOMContentLoaded', () => {
    // Configure marked for code highlighting
    marked.setOptions({
        highlight: function(code, lang) {
            const language = hljs.getLanguage(lang) ? lang : 'plaintext';
            return hljs.highlight(code, { language }).value;
        }
    });

    if (currentToken) {
        checkAuth();
    }

    setupEventListeners();
});

// --- Auth & Profile ---

async function checkAuth() {
    try {
        const res = await fetch(`${API_BASE}/auth/me`, {
            headers: { 'Authorization': `Bearer ${currentToken}` }
        });
        if (res.ok) {
            currentUser = await res.json();
            showDashboard();
        } else {
            handleLogout();
        }
    } catch (e) {
        console.error('Auth check failed', e);
        handleLogout();
    }
}

document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const u = document.getElementById('username').value;
    const p = document.getElementById('password').value;
    const errorEl = document.getElementById('login-error');
    
    try {
        const res = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: u, password: p })
        });
        
        if (res.ok) {
            const data = await res.json();
            currentToken = data.access_token;
            currentUser = data.user;
            localStorage.setItem('graphrag_jwt', currentToken);
            errorEl.classList.add('hidden');
            showDashboard();
        } else {
            errorEl.classList.remove('hidden');
        }
    } catch (e) {
        errorEl.textContent = "Network error. Please try again.";
        errorEl.classList.remove('hidden');
    }
});

function handleLogout() {
    currentToken = null;
    currentUser = null;
    localStorage.removeItem('graphrag_jwt');
    document.getElementById('app-view').classList.remove('active');
    setTimeout(() => {
        document.getElementById('app-view').classList.add('hidden');
        document.getElementById('login-view').classList.remove('hidden');
        setTimeout(() => document.getElementById('login-view').classList.add('active'), 50);
    }, 500);
}

document.getElementById('btn-logout').addEventListener('click', handleLogout);

function showDashboard() {
    document.getElementById('login-view').classList.remove('active');
    setTimeout(() => {
        document.getElementById('login-view').classList.add('hidden');
        document.getElementById('app-view').classList.remove('hidden');
        setTimeout(() => document.getElementById('app-view').classList.add('active'), 50);
        
        // Setup user UI
        document.getElementById('nav-username').textContent = currentUser.username;
        document.getElementById('nav-role').textContent = currentUser.role;
        
        if (currentUser.role === 'superadmin') {
            document.querySelector('.admin-only').classList.remove('hidden');
        } else {
            document.querySelector('.admin-only').classList.add('hidden');
        }
        
        // Initial data loads
        loadToken();
        loadDocuments();
    }, 500);
}

// --- Navigation ---

function setupEventListeners() {
    // Tabs
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const tabId = item.getAttribute('data-tab');
            if(!tabId) return;
            
            // Update active nav
            document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
            item.classList.add('active');
            
            // Update title
            document.getElementById('current-tab-title').textContent = item.textContent.trim();
            
            // Show tab
            document.querySelectorAll('.tab-pane').forEach(t => t.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            
            // Tab-specific loading
            if(tabId === 'tab-admin-users') loadUsers();
            if(tabId === 'tab-admin-settings') loadEnvVars();
        });
    });

    // Chat
    document.getElementById('chat-form').addEventListener('submit', handleChatSubmit);
    
    // Search
    document.getElementById('btn-execute-search').addEventListener('click', executeSearch);

    // Notifications toggle
    document.getElementById('btn-notifications').addEventListener('click', () => {
        const panel = document.getElementById('notifications-panel');
        panel.classList.toggle('hidden');
    });
    
    // Token Management
    document.getElementById('btn-copy-token').addEventListener('click', () => {
        const val = document.getElementById('api-token-value').value;
        navigator.clipboard.writeText(val);
        alert('Token copied to clipboard');
    });
    document.getElementById('btn-regen-token').addEventListener('click', async () => {
        if(!confirm('Are you sure? This invalidates the old token immediately.')) return;
        try {
            const res = await fetch(`${API_BASE}/tokens/regen`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${currentToken}` }
            });
            const data = await res.json();
            document.getElementById('api-token-value').value = data.token_key;
        } catch(e) { console.error(e); }
    });
}

// --- Chat ---
async function handleChatSubmit(e) {
    e.preventDefault();
    const input = document.getElementById('chat-input');
    const msg = input.value.trim();
    if (!msg) return;
    
    input.value = '';
    
    const historyEl = document.getElementById('chat-history');
    
    // Add user message
    const userDiv = document.createElement('div');
    userDiv.className = 'chat-message user';
    userDiv.innerHTML = `
        <div class="message-avatar"><i class="fa-solid fa-user"></i></div>
        <div class="message-bubble">${escapeHtml(msg)}</div>
    `;
    historyEl.appendChild(userDiv);
    historyEl.scrollTop = historyEl.scrollHeight;
    
    // Loading indicator
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'chat-message assistant';
    loadingDiv.innerHTML = `
        <div class="message-avatar"><i class="fa-solid fa-robot fa-bounce"></i></div>
        <div class="message-bubble text-muted">Searching knowledge graph...</div>
    `;
    historyEl.appendChild(loadingDiv);
    historyEl.scrollTop = historyEl.scrollHeight;
    
    try {
        const res = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${currentToken}`
            },
            body: JSON.stringify({ message: msg })
        });
        
        const data = await res.json();
        
        // Replace loading with real response
        historyEl.removeChild(loadingDiv);
        
        const astDiv = document.createElement('div');
        astDiv.className = 'chat-message assistant';
        astDiv.innerHTML = `
            <div class="message-avatar"><i class="fa-solid fa-robot"></i></div>
            <div class="message-bubble markdown-body">${marked.parse(data.response)}</div>
        `;
        historyEl.appendChild(astDiv);
        
        // syntax highlight
        astDiv.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightElement(block);
        });
        
        historyEl.scrollTop = historyEl.scrollHeight;
        
    } catch (e) {
        loadingDiv.querySelector('.message-bubble').textContent = "Error connecting to server.";
        loadingDiv.querySelector('.message-bubble').classList.add('text-danger');
        loadingDiv.querySelector('i').classList.remove('fa-bounce');
    }
}

// --- Search Playground ---
async function executeSearch() {
    const query = document.getElementById('search-query').value.trim();
    const type = document.getElementById('search-type').value;
    if(!query) return;
    
    const btn = document.getElementById('btn-execute-search');
    const resBox = document.getElementById('search-results-box');
    const resContent = document.getElementById('search-result-content');
    const resTime = document.getElementById('res-time');
    const resType = document.getElementById('res-type');
    
    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Searching...';
    resBox.classList.add('hidden');
    
    try {
        const res = await fetch(`${API_BASE}/query/${type}`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${currentToken}`
            },
            body: JSON.stringify({ query: query })
        });
        
        const data = await res.json();
        
        resType.textContent = type.toUpperCase();
        resTime.textContent = data.completion_time ? data.completion_time.toFixed(2) : '0.00';
        resContent.innerHTML = marked.parse(data.response);
        
        resBox.classList.remove('hidden');
    } catch (e) {
        resContent.innerHTML = `<div class="text-danger">Failed to execute search: ${e.message}</div>`;
        resBox.classList.remove('hidden');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fa-solid fa-search"></i> Search';
    }
}


// --- API Requests ---

async function loadToken() {
    try {
        const res = await fetch(`${API_BASE}/tokens/my-token`, {
            headers: { 'Authorization': `Bearer ${currentToken}` }
        });
        const data = await res.json();
        document.getElementById('api-token-value').value = data.token_key || 'No token found';
    } catch(e) { console.error(e); }
}

async function loadDocuments() {
    try {
        const res = await fetch(`${API_BASE}/documents`, {
            headers: { 'Authorization': `Bearer ${currentToken}` }
        });
        const data = await res.json();
        const tbody = document.getElementById('documents-table-body');
        
        if (!data.documents || data.documents.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">No documents uploaded yet.</td></tr>';
            return;
        }
        
        tbody.innerHTML = '';
        data.documents.forEach(doc => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><i class="fa-regular fa-file text-muted mr-2"></i> ${doc.filename}</td>
                <td>${(doc.size_bytes / 1024).toFixed(2)} KB</td>
                <td>${new Date(doc.modified_at).toLocaleString()}</td>
                <td>
                    <button class="btn btn-ghost btn-sm text-danger" onclick="deleteDocument('${doc.filename}')">
                        <i class="fa-solid fa-trash"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch(e) { console.error(e); }
}

async function loadUsers() {
    try {
        const res = await fetch(`${API_BASE}/users`, {
            headers: { 'Authorization': `Bearer ${currentToken}` }
        });
        const users = await res.json();
        const tbody = document.getElementById('admin-users-table');
        tbody.innerHTML = '';
        
        users.forEach(u => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${u.username} <br><small class="text-muted">${u.email || ''}</small></td>
                <td><span class="badge ${u.role === 'superadmin' ? 'badge-primary' : 'badge-outline'}">${u.role}</span></td>
                <td>${u.is_active ? '<span class="text-accent">Active</span>' : '<span class="text-danger">Inactive</span>'}</td>
                <td>${new Date(u.created_at).toLocaleDateString()}</td>
                <td>
                    <button class="btn btn-ghost btn-sm text-danger" onclick="deleteUser('${u.id}')" ${u.id === currentUser.id ? 'disabled' : ''}>
                        <i class="fa-solid fa-trash"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch(e) { console.error(e); }
}

async function loadEnvVars() {
    try {
        const res = await fetch(`${API_BASE}/settings/env`, {
            headers: { 'Authorization': `Bearer ${currentToken}` }
        });
        const data = await res.json();
        const container = document.getElementById('env-vars-container');
        container.innerHTML = '';
        
        Object.entries(data.env).forEach(([key, val]) => {
            const div = document.createElement('div');
            div.className = 'form-group mb-3';
            div.innerHTML = `
                <label>${key}</label>
                <div class="flex gap-2">
                    <input type="text" class="form-input text-monospace text-muted" value="${val}" readonly>
                </div>
            `;
            container.appendChild(div);
        });
    } catch(e) { console.error(e); }
}


// --- Modal Utils ---
function closeModal(id) {
    document.getElementById(id).classList.add('hidden');
    document.getElementById('modal-backdrop').classList.add('hidden');
}

document.getElementById('btn-show-create-user').addEventListener('click', () => {
    document.getElementById('modal-backdrop').classList.remove('hidden');
    document.getElementById('modal-create-user').classList.remove('hidden');
});

// Utils
function escapeHtml(unsafe) {
    return unsafe
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
}
