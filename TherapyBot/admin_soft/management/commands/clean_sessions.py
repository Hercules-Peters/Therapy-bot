from django.core.management.base import BaseCommand
from django.contrib.sessions.models import Session
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Cleans up expired sessions and performs maintenance on the ChatSessionManager'

    def handle(self, *args, **options):
        # Clean up expired sessions from the database
        expired_sessions = Session.objects.filter(expire_date__lt=datetime.now())
        count = expired_sessions.count()
        expired_sessions.delete()
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully deleted {count} expired sessions')
        )
        
        # You can add additional cleanup logic here if needed
        # For example, if you want to access the ChatSessionManager:
        # from your_app.chat_session import chat_session_manager
        # chat_session_manager.cleanup_old_sessions()
        
        self.stdout.write(
            self.style.SUCCESS('Session cleanup completed')
        )