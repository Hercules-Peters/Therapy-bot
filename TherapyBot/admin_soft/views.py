from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordChangeView, PasswordResetConfirmView
from .forms import LoginForm, RegistrationForm, UserPasswordResetForm, UserSetPasswordForm, UserPasswordChangeForm
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timedelta
import os
import google.generativeai as genai
from google.api_core import exceptions
from dotenv import load_dotenv
from .chat_session import ChatSessionManager
import logging
import random

# Set up logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize ChatSessionManager
chat_session_manager = ChatSessionManager()

# Configure Gemini API
try:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY environment variable is not set")
        model = None
    else:
        genai.configure(api_key=api_key)
        
        model_name = "gemini-1.5-flash" 
        
        generation_config = {
            "temperature": 0.9,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 1000,
        }
        
        safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]
        
        # Create the model
        model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=generation_config,
            safety_settings=safety_settings,  # Pass safety settings separately
            system_instruction=(
                "You are a professional AI therapist providing compassionate, evidence-based, and non-judgmental support. "
                "Use reflective listening, validation, and open-ended questions. Encourage self-reflection instead of direct advice. "
                "If a user expresses distress, offer grounding techniques and recommend professional help."
            )
        )
        
        logger.info(f"Using model: {model_name}")
        
except Exception as e:
    logger.error(f"Error initializing Gemini API: {str(e)}")
    model = None

# Views

def index(request):
    """ Renders the chat page with session history """
    try:
        session_id = chat_session_manager.get_or_create_session_id(request)
        chat_history = chat_session_manager.get_chat_history(session_id)
        return render(request, 'pages/index.html', {'segment': 'index', 'chat_history': chat_history})
    except Exception as e:
        logger.error(f"Error in index view: {str(e)}")
        return render(request, 'pages/index.html', {'segment': 'index', 'chat_history': [], 'error': 'Error loading chat history'})


@csrf_exempt
def chat(request):
    """ Processes user input and generates AI responses """
    if request.method == 'POST':
        try:
            message = request.POST.get('message', '').strip()
            if not message:
                return JsonResponse({'error': 'Message cannot be empty'}, status=400)

            # Get session ID
            try:
                session_id = chat_session_manager.get_or_create_session_id(request)
            except Exception as e:
                logger.error(f"Session error: {str(e)}")
                return JsonResponse({'error': 'Session error. Please refresh the page.'}, status=400)

            # Retrieve chat history
            try:
                chat_history = chat_session_manager.get_chat_history(session_id)
            except Exception as e:
                logger.error(f"Chat history error: {str(e)}")
                chat_history = []  # Fallback to empty history

            # Generate AI response using the model
            try:
                # Start a new chat with the model
                chat = model.start_chat(history=[])
                
                # Add previous messages to the chat
                for msg in chat_history:
                    if msg["role"] == "user":
                        chat.send_message(msg["content"])
                    # Note: We don't need to add model responses as they're tracked automatically
                
                # Send the current message and get response
                response = chat.send_message(message)
                ai_response = response.text
            except Exception as e:
                logger.error(f"Error generating AI response: {str(e)}")
                ai_response = "I'm sorry, I'm having trouble processing your request right now. Could you try again later?"

            # Store messages in session
            try:
                chat_session_manager.add_message(session_id, "user", message)
                chat_session_manager.add_message(session_id, "model", ai_response)
            except Exception as e:
                logger.error(f"Error adding message to session: {str(e)}")

            return JsonResponse({'response': ai_response})

        except Exception as e:
            logger.error(f"Error in chat processing: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=400)


def get_sentiment(history):
    try:
        if model is None:
            return "Unknown", 50  # Default level if AI fails
        
        # System prompt enforcing sentiment format with percentage
        system_prompt = (
            "You are a sentiment analyzer. Analyze the following chat history and determine the emotional sentiment."
            " Provide a sentiment category and an intensity percentage between 0-100."
            " The sentiment should be one of the following: fear, disgust, admiration, sadness, anger, happiness, anxiety,"
            " depression, stress, suicidal, bipolar, or personality disorder."
            " Format your response as follows:\n"
            "Sentiment: [sentiment]\n"
            "Intensity: [percentage]%"
        )
        
        # Create a sentiment analysis model with specific instructions
        sentiment_model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=system_prompt
        )
        
        # Generate sentiment analysis
        response = sentiment_model.generate_content(history)
        
        # Extract sentiment and intensity
        lines = response.text.split('\n')
        sentiment = "Unknown"
        intensity = 50  # Default percentage

        for line in lines:
            if line.startswith("Sentiment:"):
                sentiment = line.split(":")[1].strip()
            elif line.startswith("Intensity:"):
                try:
                    intensity = int(line.split(":")[1].replace('%', '').strip())
                except ValueError:
                    intensity = 50  # Default in case of parsing failure
        
        return sentiment, intensity
    
    except Exception as e:
        logger.error(f"Error in get_sentiment: {str(e)}")
        return "Unknown", 50

def analyze_chat_sentiment(request):
    """ Extracts chat history, runs sentiment analysis, and returns structured sentiment data. """
    session_id = chat_session_manager.get_or_create_session_id(request)
    history = chat_session_manager.get_chat_history(session_id)
    
    # Get username if user is authenticated, otherwise use "Guest"
    username = request.user.username if request.user.is_authenticated else "Guest"

    if not history:
        return None  # Indicate no history available

    history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in history])
    sentiment, level = get_sentiment(history_text)

    status = "Good" if level >= 70 else "Moderate" if level >= 40 else "Low"
    status_color = "success" if status == "Good" else "warning" if status == "Moderate" else "danger"

    return {
        "id": session_id,
        "sentiment": sentiment,
        "username": username,  # Add username to sentiment data
        "level": level,
        "level_description": "excellent" if level >= 80 else "good" if level >= 60 else "okay" if level >= 40 else "concerning",
        "status": status,
        "status_color": status_color,
        "time": datetime.now().strftime("%H:%M"),
    }

def get_screening_data(request):
    try:
        sentiment_data = analyze_chat_sentiment(request)
        if sentiment_data is None:
            return JsonResponse({'error': 'No chat history available'}, status=400)

        return JsonResponse(sentiment_data)
    except Exception as e:
        logger.error(f"Error in get_screening_data: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

def generate_default_sentiments():
    """Generate 7 default sentiments for initial display"""
    sentiments = [
        {"name": "Happiness", "level": 85, "status": "Good", "status_color": "success"},
        {"name": "Anxiety", "level": 45, "status": "Moderate", "status_color": "warning"},
        {"name": "Depression", "level": 30, "status": "Low", "status_color": "danger"},
        {"name": "Stress", "level": 60, "status": "Moderate", "status_color": "warning"},
        {"name": "Anger", "level": 25, "status": "Low", "status_color": "danger"},
        {"name": "Fear", "level": 40, "status": "Moderate", "status_color": "warning"},
        {"name": "Admiration", "level": 75, "status": "Good", "status_color": "success"},
    ]
    
    # Add additional fields
    for i, sentiment in enumerate(sentiments):
        sentiment["id"] = f"default-{i}"
        sentiment["username"] = f"User{i+1}"
        sentiment["level_description"] = "excellent" if sentiment["level"] >= 80 else "good" if sentiment["level"] >= 60 else "okay" if sentiment["level"] >= 40 else "concerning"
        # Generate random times within the last 24 hours
        random_hours = random.randint(0, 23)
        random_minutes = random.randint(0, 59)
        sentiment["time"] = (datetime.now() - timedelta(hours=random_hours, minutes=random_minutes)).strftime("%H:%M")
    
    return sentiments

@login_required
def screening(request):
    """ Displays emotional sentiment analysis """
    try:
        # Get real sentiment data if available
        sentiment_data = analyze_chat_sentiment(request)
        
        # Generate default sentiments
        default_sentiments = generate_default_sentiments()
        
        # If real sentiment data is available, add it to the beginning of the list
        emotional_sentiments = default_sentiments
        if sentiment_data is not None:
            emotional_sentiments = [sentiment_data] + default_sentiments[:6]  # Keep total at 7
        
        return render(request, 'pages/screening.html', {'segment': 'screening', 'emotional_sentiments': emotional_sentiments})
    except Exception as e:
        logger.error(f"Error in tables view: {str(e)}")
        return render(request, 'pages/screening.html', {'segment': 'screening', 'error': 'Error loading data'})

def location(request):
    return render(request, 'pages/location.html', { 'segment': 'location' })

def profile(request):
    return render(request, 'pages/profile.html', { 'segment': 'profile' })

# Authentication
class UserLoginView(LoginView):
    template_name = 'accounts/login.html'
    form_class = LoginForm

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            print('Account created successfully!')
            return redirect('/accounts/login/')
        else:
            print("Register failed!")
    else:
        form = RegistrationForm()

    context = { 'form': form }
    return render(request, 'accounts/register.html', context)

def logout_view(request):
    logout(request)
    return redirect('/accounts/login/')

class UserPasswordResetView(PasswordResetView):
    template_name = 'accounts/password_reset.html'
    form_class = UserPasswordResetForm

class UserPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'accounts/password_reset_confirm.html'
    form_class = UserSetPasswordForm

class UserPasswordChangeView(PasswordChangeView):
    template_name = 'accounts/password_change.html'
    form_class = UserPasswordChangeForm