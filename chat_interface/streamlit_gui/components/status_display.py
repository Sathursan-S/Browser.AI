"""
Status Display Component for Streamlit

Shows real-time task status, logs, and progress information.
"""

import streamlit as st
import requests
from typing import Dict, Any, List
from datetime import datetime
import time


class StatusDisplay:
    """Displays real-time task status and logs"""
    
    def __init__(self):
        # Initialize session state
        if 'last_log_update' not in st.session_state:
            st.session_state.last_log_update = datetime.now()
        if 'log_auto_refresh' not in st.session_state:
            st.session_state.log_auto_refresh = True
    
    def render(self):
        """Render the status display"""
        with st.sidebar:
            st.markdown("## 📊 Status Dashboard")
            
            self._render_system_status()
            self._render_active_tasks()
            self._render_recent_logs()
    
    def _render_system_status(self):
        """Render system health status"""
        try:
            response = requests.get("http://localhost:8000/health")
            if response.status_code == 200:
                health_data = response.json()
                
                st.success("🟢 System Online")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Connections", health_data.get('active_connections', 0))
                with col2:
                    st.metric("Running Tasks", health_data.get('running_tasks', 0))
                
                st.metric("Total Tasks", health_data.get('total_tasks', 0))
                
            else:
                st.error("🔴 System Offline")
                
        except requests.exceptions.RequestException:
            st.error("🔴 Backend Unavailable")
    
    def _render_active_tasks(self):
        """Render currently active/running tasks"""
        st.markdown("### 🏃 Active Tasks")
        
        try:
            response = requests.get("http://localhost:8000/tasks")
            if response.status_code == 200:
                tasks = response.json()
                active_tasks = [t for t in tasks if t['status'] == 'running']
                
                if active_tasks:
                    for task in active_tasks:
                        with st.container():
                            st.markdown(f"**Task:** {task['description'][:50]}...")
                            st.markdown(f"**ID:** `{task['task_id'][:8]}...`")
                            st.markdown(f"**Started:** {task['started_at'][:19] if task['started_at'] else 'N/A'}")
                            
                            # Add stop button
                            if st.button(f"🛑 Stop", key=f"stop_{task['task_id']}"):
                                self._stop_task(task['task_id'])
                            
                            st.markdown("---")
                else:
                    st.info("No active tasks")
            else:
                st.error("Failed to get tasks")
                
        except requests.exceptions.RequestException:
            st.error("Backend unavailable")
    
    def _render_recent_logs(self):
        """Render recent log entries"""
        st.markdown("### 📋 Recent Logs")
        
        # Auto-refresh toggle
        auto_refresh = st.checkbox(
            "Auto-refresh",
            value=st.session_state.log_auto_refresh,
            help="Automatically refresh logs every 5 seconds"
        )
        st.session_state.log_auto_refresh = auto_refresh
        
        # Manual refresh button
        if st.button("🔄 Refresh Logs"):
            st.session_state.last_log_update = datetime.now()
            st.rerun()
        
        # Display logs
        try:
            # Get recent tasks and their logs
            response = requests.get("http://localhost:8000/tasks")
            if response.status_code == 200:
                tasks = response.json()
                recent_tasks = sorted(tasks, key=lambda x: x['created_at'], reverse=True)[:3]
                
                for task in recent_tasks:
                    task_id = task['task_id']
                    
                    # Get logs for this task
                    log_response = requests.get(f"http://localhost:8000/tasks/{task_id}/logs")
                    if log_response.status_code == 200:
                        logs = log_response.json()
                        recent_logs = logs[-5:]  # Show last 5 logs
                        
                        if recent_logs:
                            st.markdown(f"**{task['description'][:30]}...**")
                            for log in recent_logs:
                                level = log['level']
                                message = log['message'][:100]
                                timestamp = log['timestamp'][:19]
                                
                                # Color-code by level
                                if level == 'ERROR':
                                    st.error(f"`{timestamp}` {message}")
                                elif level == 'WARNING':
                                    st.warning(f"`{timestamp}` {message}")
                                elif level == 'INFO':
                                    st.info(f"`{timestamp}` {message}")
                                else:
                                    st.text(f"`{timestamp}` {message}")
                            
                            st.markdown("---")
            
        except requests.exceptions.RequestException:
            st.error("Failed to get logs")
        
        # Auto-refresh logic
        if auto_refresh:
            # Check if 5 seconds have passed
            now = datetime.now()
            time_diff = (now - st.session_state.last_log_update).total_seconds()
            
            if time_diff >= 5:
                st.session_state.last_log_update = now
                st.rerun()
    
    def _stop_task(self, task_id: str):
        """Stop a specific task"""
        try:
            response = requests.post(f"http://localhost:8000/tasks/{task_id}/stop")
            if response.status_code == 200:
                st.success(f"Task {task_id[:8]}... stopped")
                st.rerun()
            else:
                st.error("Failed to stop task")
        except requests.exceptions.RequestException:
            st.error("Backend unavailable")
    
    def render_detailed_logs(self, task_id: str = None):
        """Render detailed logs view"""
        st.markdown("## 📋 Detailed Logs")
        
        if task_id:
            # Show logs for specific task
            try:
                response = requests.get(f"http://localhost:8000/tasks/{task_id}/logs")
                if response.status_code == 200:
                    logs = response.json()
                    
                    if logs:
                        for log in logs:
                            level = log['level']
                            message = log['message']
                            logger_name = log['logger_name']
                            timestamp = log['timestamp']
                            
                            # Create expandable log entry
                            with st.expander(f"{level} - {timestamp} - {logger_name}"):
                                st.code(message, language='text')
                    else:
                        st.info("No logs available for this task")
                else:
                    st.error("Failed to get logs")
            except requests.exceptions.RequestException:
                st.error("Backend unavailable")
        else:
            # Show all recent logs
            st.info("Select a task to view its detailed logs")
    
    def render_task_history(self):
        """Render task history"""
        st.markdown("## 📚 Task History")
        
        try:
            response = requests.get("http://localhost:8000/tasks")
            if response.status_code == 200:
                tasks = response.json()
                
                if tasks:
                    # Sort by creation time (newest first)
                    tasks = sorted(tasks, key=lambda x: x['created_at'], reverse=True)
                    
                    for task in tasks:
                        status = task['status']
                        
                        # Status emoji mapping
                        status_emoji = {
                            'pending': '⏳',
                            'running': '🔄',
                            'completed': '✅',
                            'failed': '❌',
                            'cancelled': '🛑'
                        }
                        
                        emoji = status_emoji.get(status, '❓')
                        
                        with st.expander(f"{emoji} {task['description'][:50]}... [{status.upper()}]"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write(f"**Task ID:** `{task['task_id']}`")
                                st.write(f"**Status:** {status}")
                                st.write(f"**Created:** {task['created_at'][:19]}")
                                
                            with col2:
                                if task['started_at']:
                                    st.write(f"**Started:** {task['started_at'][:19]}")
                                if task['completed_at']:
                                    st.write(f"**Completed:** {task['completed_at'][:19]}")
                                if task['error']:
                                    st.error(f"**Error:** {task['error']}")
                            
                            st.write(f"**Description:** {task['description']}")
                            
                            if task['result']:
                                st.write("**Result:**")
                                st.json(task['result'])
                            
                            # Action buttons
                            button_col1, button_col2 = st.columns(2)
                            with button_col1:
                                if st.button(f"📋 View Logs", key=f"logs_{task['task_id']}"):
                                    self.render_detailed_logs(task['task_id'])
                            
                            with button_col2:
                                if status == 'running':
                                    if st.button(f"🛑 Stop", key=f"stop_hist_{task['task_id']}"):
                                        self._stop_task(task['task_id'])
                else:
                    st.info("No tasks found")
            else:
                st.error("Failed to get task history")
                
        except requests.exceptions.RequestException:
            st.error("Backend unavailable")