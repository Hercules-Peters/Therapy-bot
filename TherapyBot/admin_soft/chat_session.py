from datetime import datetime, timedelta
from django.contrib.auth.models import AnonymousUser

class ChatSessionManager:
    def __init__(self):
        self.sessions = {}
        self.last_sentiment_analysis = {}
        self.sentiment_data = {}

    def get_or_create_session_id(self, request):
        if request.user.is_authenticated:
            return str(request.user.id)
        else:
            session_id = request.session.get('anonymous_session_id')
            if not session_id:
                session_id = f"anon_{datetime.now().timestamp()}"
                request.session['anonymous_session_id'] = session_id
            return session_id

    def get_chat_history(self, session_id):
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        return self.sessions[session_id]

    def add_message(self, session_id, role, content):
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        
        self.sessions[session_id].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now()
        })
        
        # Remove messages older than 10 minutes
        self.sessions[session_id] = [
            msg for msg in self.sessions[session_id]
            if datetime.now() - msg["timestamp"] < timedelta(minutes=10)
        ]

        # Delete anonymous user data after 5 seconds
        if session_id.startswith("anon_"):
            self.schedule_anonymous_data_deletion(session_id)

    def schedule_anonymous_data_deletion(self, session_id):
        from threading import Timer
        Timer(5, self.delete_session, args=[session_id]).start()

    def delete_session(self, session_id):
        self.sessions.pop(session_id, None)
        self.last_sentiment_analysis.pop(session_id, None)
        self.sentiment_data.pop(session_id, None)

    def should_perform_sentiment_analysis(self, session_id):
        if session_id not in self.last_sentiment_analysis:
            return True
        
        time_since_last_analysis = datetime.now() - self.last_sentiment_analysis[session_id]
        return time_since_last_analysis >= timedelta(minutes=2)

    def update_last_sentiment_analysis(self, session_id):
        self.last_sentiment_analysis[session_id] = datetime.now()

    def update_sentiment_data(self, session_id, sentiment_data):
        self.sentiment_data[session_id] = sentiment_data

    def get_sentiment_data(self, session_id):
        return self.sentiment_data.get(session_id)

