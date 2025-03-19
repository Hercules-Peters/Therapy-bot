from datetime import datetime, timedelta
from django.contrib.auth.models import AnonymousUser
import threading
import logging

# Set up logging
logger = logging.getLogger(__name__)

class ChatSessionManager:
    def __init__(self):
        self.sessions = {}
        self.last_sentiment_analysis = {}
        self.sentiment_data = {}
        self.lock = threading.Lock()  # Add thread lock for synchronization

    def get_or_create_session_id(self, request):
        try:
            if request.user.is_authenticated:
                return str(request.user.id)
            else:
                session_id = request.session.get('anonymous_session_id')
                if not session_id:
                    session_id = f"anon_{datetime.now().timestamp()}"
                    request.session['anonymous_session_id'] = session_id
                    # Save session to ensure it's properly stored
                    request.session.save()
                return session_id
        except Exception as e:
            logger.error(f"Error in get_or_create_session_id: {str(e)}")
            # Fallback to a temporary session ID if there's an error
            return f"temp_{datetime.now().timestamp()}"

    def get_chat_history(self, session_id):
        with self.lock:  # Use lock for thread safety
            if session_id not in self.sessions:
                self.sessions[session_id] = []
            return self.sessions[session_id].copy()  # Return a copy to prevent concurrent modification

    def add_message(self, session_id, role, content):
        with self.lock:  # Use lock for thread safety
            try:
                if session_id not in self.sessions:
                    self.sessions[session_id] = []
                
                self.sessions[session_id].append({
                    "role": role,
                    "content": content,
                    "timestamp": datetime.now()
                })
                
                # Remove messages older than 30 minutes (increased from 10)
                self.sessions[session_id] = [
                    msg for msg in self.sessions[session_id]
                    if datetime.now() - msg["timestamp"] < timedelta(minutes=30)
                ]

                # Delete anonymous user data after 15 minutes (increased from 5 seconds)
                if session_id.startswith("anon_"):
                    self.schedule_anonymous_data_deletion(session_id)
            except Exception as e:
                logger.error(f"Error in add_message: {str(e)}")

    def schedule_anonymous_data_deletion(self, session_id):
        try:
            # Increase timeout from 5 seconds to 15 minutes
            timer = threading.Timer(15 * 60, self.delete_session, args=[session_id])
            timer.daemon = True  # Make thread daemon so it doesn't block app shutdown
            timer.start()
        except Exception as e:
            logger.error(f"Error scheduling deletion for session {session_id}: {str(e)}")

    def delete_session(self, session_id):
        with self.lock:  # Use lock for thread safety
            try:
                self.sessions.pop(session_id, None)
                self.last_sentiment_analysis.pop(session_id, None)
                self.sentiment_data.pop(session_id, None)
                logger.info(f"Session {session_id} deleted successfully")
            except Exception as e:
                logger.error(f"Error deleting session {session_id}: {str(e)}")

    def should_perform_sentiment_analysis(self, session_id):
        with self.lock:  # Use lock for thread safety
            if session_id not in self.last_sentiment_analysis:
                return True
            
            time_since_last_analysis = datetime.now() - self.last_sentiment_analysis[session_id]
            return time_since_last_analysis >= timedelta(minutes=2)

    def update_last_sentiment_analysis(self, session_id):
        with self.lock:  # Use lock for thread safety
            self.last_sentiment_analysis[session_id] = datetime.now()

    def update_sentiment_data(self, session_id, sentiment_data):
        with self.lock:  # Use lock for thread safety
            self.sentiment_data[session_id] = sentiment_data

    def get_sentiment_data(self, session_id):
        with self.lock:  # Use lock for thread safety
            return self.sentiment_data.get(session_id)