/**
 * Browser.AI Chat Interface JavaScript
 * Handles WebSocket communication, UI interactions, and real-time updates
 */

class BrowserAIChat {
    constructor() {
        this.ws = null;
        this.currentTaskId = null;
        this.isTaskRunning = false;
        this.config = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.autoRefreshInterval = null;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.connectWebSocket();
        this.loadConfiguration();
        this.startAutoRefresh();
    }
    
    // WebSocket Management
    connectWebSocket() {
        const wsUrl = `ws://${window.location.host}/ws`;
        
        try {
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.updateConnectionStatus('connected');
                this.reconnectAttempts = 0;
                
                // Send initial ping
                this.sendMessage({ type: 'ping' });
            };
            
            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            };
            
            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                this.updateConnectionStatus('disconnected');
                this.attemptReconnect();
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateConnectionStatus('disconnected');
            };
            
        } catch (error) {
            console.error('Failed to connect WebSocket:', error);
            this.updateConnectionStatus('disconnected');
            this.attemptReconnect();
        }
    }
    
    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = Math.pow(2, this.reconnectAttempts) * 1000; // Exponential backoff
            
            this.updateConnectionStatus('connecting');
            setTimeout(() => {
                console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
                this.connectWebSocket();
            }, delay);
        }
    }
    
    sendMessage(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
            return true;
        }
        return false;
    }
    
    handleWebSocketMessage(data) {
        const { type, data: messageData } = data;
        
        switch (type) {
            case 'log_event':
                this.handleLogEvent(messageData);
                break;
            case 'task_started':
                this.handleTaskStarted(messageData);
                break;
            case 'task_stopped':
                this.handleTaskStopped(messageData);
                break;
            case 'task_completed':
                this.handleTaskCompleted(messageData);
                break;
            case 'error':
                this.showToast(data.message, 'error');
                break;
            case 'pong':
                // Heartbeat response
                break;
            default:
                console.log('Unknown message type:', type, messageData);
        }
    }
    
    // Event Listeners
    setupEventListeners() {
        // Configuration
        document.getElementById('llmProvider').addEventListener('change', this.onProviderChange.bind(this));
        document.getElementById('temperature').addEventListener('input', this.onTemperatureChange.bind(this));
        document.getElementById('testConfig').addEventListener('click', this.testConfiguration.bind(this));
        document.getElementById('saveConfig').addEventListener('click', this.saveConfiguration.bind(this));
        document.getElementById('resetConfig').addEventListener('click', this.resetConfiguration.bind(this));
        
        // Config panel toggle
        document.getElementById('toggleConfig').addEventListener('click', this.toggleConfigPanel.bind(this));
        
        // Chat
        document.getElementById('messageInput').addEventListener('keypress', this.onMessageKeyPress.bind(this));
        document.getElementById('messageInput').addEventListener('input', this.onMessageInput.bind(this));
        document.getElementById('sendMessage').addEventListener('click', this.sendChatMessage.bind(this));
        document.getElementById('clearChat').addEventListener('click', this.clearChat.bind(this));
        document.getElementById('stopTask').addEventListener('click', this.stopCurrentTask.bind(this));
        
        // Sidebar
        document.getElementById('autoRefresh').addEventListener('change', this.toggleAutoRefresh.bind(this));
        document.getElementById('refreshLogs').addEventListener('click', this.refreshLogs.bind(this));
        
        // Modal
        document.getElementById('closeModal').addEventListener('click', this.closeModal.bind(this));
        
        // Click outside modal to close
        window.addEventListener('click', (e) => {
            const modal = document.getElementById('modal');
            if (e.target === modal) {
                this.closeModal();
            }
        });
    }
    
    // Configuration Management
    async loadConfiguration() {
        try {
            const response = await fetch('/config/default');
            if (response.ok) {
                this.config = await response.json();
                this.populateConfigForm();
                await this.loadProviders();
            } else {
                this.showToast('Failed to load default configuration', 'error');
            }
        } catch (error) {
            console.error('Error loading configuration:', error);
            this.showToast('Error loading configuration', 'error');
        }
    }
    
    async loadProviders() {
        try {
            const response = await fetch('/config/providers');
            if (response.ok) {
                const providers = await response.json();
                this.populateProviders(providers);
            }
        } catch (error) {
            console.error('Error loading providers:', error);
        }
    }
    
    populateProviders(providers) {
        const providerSelect = document.getElementById('llmProvider');
        const modelSelect = document.getElementById('llmModel');
        
        // Clear existing options
        providerSelect.innerHTML = '';
        modelSelect.innerHTML = '';
        
        // Populate providers
        providers.forEach(provider => {
            const option = document.createElement('option');
            option.value = provider.provider;
            option.textContent = provider.provider.charAt(0).toUpperCase() + provider.provider.slice(1);
            providerSelect.appendChild(option);
        });
        
        // Set current provider and trigger change
        if (this.config && this.config.llm) {
            providerSelect.value = this.config.llm.provider;
            this.onProviderChange();
        }
    }
    
    onProviderChange() {
        const provider = document.getElementById('llmProvider').value;
        this.loadModelsForProvider(provider);
    }
    
    async loadModelsForProvider(provider) {
        try {
            const response = await fetch('/config/providers');
            if (response.ok) {
                const providers = await response.json();
                const providerInfo = providers.find(p => p.provider === provider);
                
                if (providerInfo) {
                    const modelSelect = document.getElementById('llmModel');
                    modelSelect.innerHTML = '';
                    
                    providerInfo.requirements.models.forEach(model => {
                        const option = document.createElement('option');
                        option.value = model;
                        option.textContent = model;
                        modelSelect.appendChild(option);
                    });
                    
                    // Set current model
                    if (this.config && this.config.llm && this.config.llm.model) {
                        modelSelect.value = this.config.llm.model;
                    }
                    
                    // Update API key placeholder based on provider
                    const apiKeyInput = document.getElementById('apiKey');
                    if (providerInfo.requirements.api_key_required) {
                        apiKeyInput.style.display = 'block';
                        apiKeyInput.parentElement.style.display = 'block';
                        apiKeyInput.placeholder = `Enter your ${provider.toUpperCase()} API key`;
                    } else {
                        apiKeyInput.style.display = 'none';
                        apiKeyInput.parentElement.style.display = 'none';
                    }
                }
            }
        } catch (error) {
            console.error('Error loading models:', error);
        }
    }
    
    onTemperatureChange() {
        const tempSlider = document.getElementById('temperature');
        const tempValue = document.getElementById('tempValue');
        tempValue.textContent = tempSlider.value;
    }
    
    populateConfigForm() {
        if (!this.config) return;
        
        const { llm, browser } = this.config;
        
        if (llm) {
            document.getElementById('llmProvider').value = llm.provider || 'openai';
            document.getElementById('temperature').value = llm.temperature || 0;
            document.getElementById('tempValue').textContent = llm.temperature || 0;
            
            if (llm.api_key) {
                document.getElementById('apiKey').value = llm.api_key;
            }
        }
        
        if (browser) {
            document.getElementById('useVision').checked = browser.use_vision !== false;
            document.getElementById('headless').checked = browser.headless !== false;
        }
    }
    
    gatherConfiguration() {
        const provider = document.getElementById('llmProvider').value;
        const model = document.getElementById('llmModel').value;
        const apiKey = document.getElementById('apiKey').value;
        const temperature = parseFloat(document.getElementById('temperature').value);
        const useVision = document.getElementById('useVision').checked;
        const headless = document.getElementById('headless').checked;
        
        return {
            llm: {
                provider,
                model,
                api_key: apiKey,
                temperature
            },
            browser: {
                use_vision: useVision,
                headless
            },
            max_failures: 3
        };
    }
    
    async testConfiguration() {
        const config = this.gatherConfiguration();
        
        try {
            const response = await fetch('/config/test', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ config })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.config = config;
                this.showToast('Configuration test passed!', 'success');
                document.getElementById('sendMessage').disabled = false;
            } else {
                this.showToast(`Configuration test failed: ${result.error}`, 'error');
                document.getElementById('sendMessage').disabled = true;
            }
        } catch (error) {
            console.error('Error testing configuration:', error);
            this.showToast('Error testing configuration', 'error');
        }
    }
    
    saveConfiguration() {
        this.config = this.gatherConfiguration();
        this.showToast('Configuration saved!', 'success');
    }
    
    async resetConfiguration() {
        try {
            await this.loadConfiguration();
            this.showToast('Configuration reset to default', 'info');
        } catch (error) {
            this.showToast('Error resetting configuration', 'error');
        }
    }
    
    toggleConfigPanel() {
        const content = document.getElementById('configContent');
        const toggle = document.getElementById('toggleConfig');
        const icon = toggle.querySelector('i');
        
        if (content.style.display === 'none') {
            content.style.display = 'block';
            icon.className = 'fas fa-chevron-up';
        } else {
            content.style.display = 'none';
            icon.className = 'fas fa-chevron-down';
        }
    }
    
    // Chat Management
    onMessageKeyPress(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            this.sendChatMessage();
        }
    }
    
    onMessageInput() {
        const input = document.getElementById('messageInput');
        const sendBtn = document.getElementById('sendMessage');
        
        sendBtn.disabled = !input.value.trim() || this.isTaskRunning || !this.config;
    }
    
    async sendChatMessage() {
        const input = document.getElementById('messageInput');
        const message = input.value.trim();
        
        if (!message || this.isTaskRunning || !this.config) return;
        
        // Add user message to chat
        this.addChatMessage(message, 'user');
        input.value = '';
        
        // Show thinking message
        const thinkingId = this.addChatMessage('🤔 Processing your request...', 'assistant');
        
        try {
            // Create and start task
            const response = await fetch('/tasks/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    description: message,
                    config: this.config
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                this.currentTaskId = result.task_id;
                
                // Start the task
                const startResponse = await fetch(`/tasks/${this.currentTaskId}/start`, {
                    method: 'POST'
                });
                
                if (startResponse.ok) {
                    this.isTaskRunning = true;
                    this.updateTaskStatus(true, 'Starting automation task...');
                    
                    // Update thinking message
                    this.updateChatMessage(thinkingId, `✅ Starting automation task: ${message}\n\n**Task ID:** \`${this.currentTaskId}\`\n**Status:** Running\n\nI'll keep you updated with real-time progress...`);
                } else {
                    this.updateChatMessage(thinkingId, '❌ Failed to start task. Please try again.');
                }
            } else {
                this.updateChatMessage(thinkingId, '❌ Failed to create task. Please check your configuration.');
            }
        } catch (error) {
            console.error('Error sending message:', error);
            this.updateChatMessage(thinkingId, `❌ Error: ${error.message}`);
        }
        
        this.onMessageInput(); // Update button state
    }
    
    addChatMessage(content, type) {
        const messagesContainer = document.getElementById('chatMessages');
        const messageId = `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        messageDiv.id = messageId;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.innerHTML = this.formatMessageContent(content);
        
        const timestampDiv = document.createElement('div');
        timestampDiv.className = 'message-timestamp';
        timestampDiv.textContent = new Date().toLocaleTimeString();
        
        contentDiv.appendChild(timestampDiv);
        messageDiv.appendChild(contentDiv);
        messagesContainer.appendChild(messageDiv);
        
        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        return messageId;
    }
    
    updateChatMessage(messageId, newContent) {
        const messageElement = document.getElementById(messageId);
        if (messageElement) {
            const contentDiv = messageElement.querySelector('.message-content');
            const timestamp = contentDiv.querySelector('.message-timestamp').textContent;
            contentDiv.innerHTML = this.formatMessageContent(newContent);
            
            const newTimestamp = document.createElement('div');
            newTimestamp.className = 'message-timestamp';
            newTimestamp.textContent = timestamp;
            contentDiv.appendChild(newTimestamp);
        }
    }
    
    formatMessageContent(content) {
        // Simple markdown-like formatting
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');
    }
    
    clearChat() {
        const messagesContainer = document.getElementById('chatMessages');
        const welcomeMessage = messagesContainer.querySelector('.welcome-message');
        
        // Clear all messages except welcome
        messagesContainer.innerHTML = '';
        messagesContainer.appendChild(welcomeMessage);
        
        this.showToast('Chat cleared', 'info');
    }
    
    // Task Management
    updateTaskStatus(running, statusText = '') {
        const taskStatus = document.getElementById('taskStatus');
        const statusTextElement = document.getElementById('statusText');
        const sendButton = document.getElementById('sendMessage');
        
        if (running) {
            taskStatus.style.display = 'block';
            statusTextElement.textContent = statusText;
            sendButton.disabled = true;
        } else {
            taskStatus.style.display = 'none';
            this.onMessageInput(); // Update button state based on input
        }
        
        this.isTaskRunning = running;
    }
    
    async stopCurrentTask() {
        if (!this.currentTaskId) return;
        
        try {
            const response = await fetch(`/tasks/${this.currentTaskId}/stop`, {
                method: 'POST'
            });
            
            if (response.ok) {
                this.isTaskRunning = false;
                this.updateTaskStatus(false);
                this.addChatMessage('🛑 Task stopped by user', 'assistant');
                this.showToast('Task stopped', 'info');
            } else {
                this.showToast('Failed to stop task', 'error');
            }
        } catch (error) {
            console.error('Error stopping task:', error);
            this.showToast('Error stopping task', 'error');
        }
    }
    
    // WebSocket Event Handlers
    handleLogEvent(logData) {
        const { level, message, logger_name, timestamp } = logData;
        
        // Add log to recent logs
        this.addRecentLog(level, message, logger_name, timestamp);
        
        // Add log message to chat if it's from the current task
        if (this.isTaskRunning) {
            const emoji = this.getLogEmoji(level);
            const formattedMessage = `${emoji} **${level}** [${logger_name}]\n${message}`;
            this.addChatMessage(formattedMessage, 'assistant');
        }
    }
    
    handleTaskStarted(data) {
        this.currentTaskId = data.task_id;
        this.isTaskRunning = true;
        this.updateTaskStatus(true, `Running: ${data.description}`);
    }
    
    handleTaskStopped(data) {
        this.isTaskRunning = false;
        this.updateTaskStatus(false);
        this.addChatMessage('🛑 Task was stopped', 'assistant');
    }
    
    handleTaskCompleted(data) {
        this.isTaskRunning = false;
        this.updateTaskStatus(false);
        
        const success = data.success;
        const result = data.result || {};
        
        if (success) {
            const message = `✅ **Task completed successfully!**\n\n**Result:** ${result.extracted_content || 'Task completed'}\n**Status:** ${result.is_done ? 'Done' : 'Completed'}`;
            this.addChatMessage(message, 'assistant');
            this.showToast('Task completed successfully!', 'success');
        } else {
            const error = data.error || 'Unknown error';
            const message = `❌ **Task failed**\n\n**Error:** ${error}`;
            this.addChatMessage(message, 'assistant');
            this.showToast('Task failed', 'error');
        }
        
        this.currentTaskId = null;
    }
    
    getLogEmoji(level) {
        const emojiMap = {
            'ERROR': '❌',
            'WARNING': '⚠️',
            'INFO': 'ℹ️',
            'DEBUG': '🐛'
        };
        return emojiMap[level] || '📋';
    }
    
    // UI Updates
    updateConnectionStatus(status) {
        const indicator = document.getElementById('statusIndicator');
        const statusText = document.getElementById('connectionStatus');
        
        indicator.className = `status-indicator ${status}`;
        
        switch (status) {
            case 'connected':
                statusText.textContent = 'Connected';
                break;
            case 'disconnected':
                statusText.textContent = 'Disconnected';
                break;
            case 'connecting':
                statusText.textContent = 'Connecting...';
                break;
        }
    }
    
    async updateSystemStatus() {
        try {
            const response = await fetch('/health');
            if (response.ok) {
                const health = await response.json();
                
                document.getElementById('connectionCount').textContent = health.active_connections || 0;
                document.getElementById('runningTasks').textContent = health.running_tasks || 0;
                document.getElementById('totalTasks').textContent = health.total_tasks || 0;
            }
        } catch (error) {
            console.error('Error updating system status:', error);
        }
    }
    
    addRecentLog(level, message, loggerName, timestamp) {
        const logsContainer = document.getElementById('recentLogs');
        const noLogs = logsContainer.querySelector('.no-logs');
        
        if (noLogs) {
            noLogs.remove();
        }
        
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry ${level.toLowerCase()}`;
        
        const timeStr = new Date(timestamp).toLocaleTimeString();
        const shortMessage = message.length > 100 ? message.substring(0, 100) + '...' : message;
        
        logEntry.innerHTML = `
            <div style="font-weight: 500; margin-bottom: 2px;">${level} - ${timeStr}</div>
            <div style="font-size: 0.75rem; color: #666;">[${loggerName}] ${shortMessage}</div>
        `;
        
        logsContainer.insertBefore(logEntry, logsContainer.firstChild);
        
        // Keep only last 10 logs
        while (logsContainer.children.length > 10) {
            logsContainer.removeChild(logsContainer.lastChild);
        }
    }
    
    // Auto-refresh
    startAutoRefresh() {
        this.autoRefreshInterval = setInterval(() => {
            const autoRefresh = document.getElementById('autoRefresh').checked;
            if (autoRefresh) {
                this.updateSystemStatus();
            }
        }, 5000);
    }
    
    toggleAutoRefresh() {
        const autoRefresh = document.getElementById('autoRefresh').checked;
        if (!autoRefresh && this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
            this.autoRefreshInterval = null;
        } else if (autoRefresh && !this.autoRefreshInterval) {
            this.startAutoRefresh();
        }
    }
    
    refreshLogs() {
        this.updateSystemStatus();
        this.showToast('Status refreshed', 'info');
    }
    
    // Modal
    showModal(title, content) {
        document.getElementById('modalTitle').textContent = title;
        document.getElementById('modalBody').innerHTML = content;
        document.getElementById('modal').style.display = 'block';
    }
    
    closeModal() {
        document.getElementById('modal').style.display = 'none';
    }
    
    // Toast Notifications
    showToast(message, type = 'info') {
        const container = document.getElementById('toastContainer');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        
        container.appendChild(toast);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (container.contains(toast)) {
                container.removeChild(toast);
            }
        }, 5000);
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.browserAIChat = new BrowserAIChat();
});