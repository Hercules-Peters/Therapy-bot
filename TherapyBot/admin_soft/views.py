from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordChangeView, PasswordResetConfirmView
from admin_soft.forms import RegistrationForm, LoginForm, UserPasswordResetForm, UserSetPasswordForm, UserPasswordChangeForm
from django.contrib.auth import logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
import json
from datetime import datetime, timedelta
import os
import google.generativeai as genai
from google.api_core import exceptions
from dotenv import load_dotenv
from .chat_session import ChatSessionManager
from django.contrib.auth.decorators import login_required

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Create the model
generation_config = {
    "temperature": 0.9,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens":1000,
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
    },
]

model = genai.GenerativeModel(
    model_name="gemini-1.0-pro",
    generation_config=generation_config,
    safety_settings=safety_settings
)

# Initialize ChatSessionManager
chat_session_manager = ChatSessionManager()

# Pages
def index(request):
    session_id = chat_session_manager.get_or_create_session_id(request)
    chat_history = chat_session_manager.get_chat_history(session_id)
    return render(request, 'pages/index.html', {'segment': 'index', 'chat_history': chat_history})

@csrf_exempt
def chat(request):
    if request.method == 'POST':
        message = request.POST.get('message', '')
        
        session_id = chat_session_manager.get_or_create_session_id(request)
        chat_history = chat_session_manager.get_chat_history(session_id)
        
        # Prepare the conversation for Gemini
        conversation = [
            {"role": "user" if msg["role"] == "user" else "model", "parts": [msg["content"]]}
            for msg in chat_history
        ]
        conversation.append({"role": "user", "parts": [message]})
        
        try:
            chat = model.start_chat(history=conversation)
            response = chat.send_message(message)
            
            chat_session_manager.add_message(session_id, "user", message)
            chat_session_manager.add_message(session_id, "model", response.text)
            
            return JsonResponse({'response': response.text})
        except exceptions.ResourceExhausted:
            return JsonResponse({'error': 'API quota exceeded. Please try again later.'}, status=429)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)

def get_sentiment(history):
    conversation = [
        {"role": "user", "parts": ["Analyze the following chat history and determine the emotional sentiment. Provide a brief reason for your assessment. The sentiment should be one of the following: fear, disgust, admiration, sadness, anger, happiness, anxiety, depression, stress, suicidal, bipolar, or personality disorder. Format your response as 'Sentiment: [sentiment]\nReason: [reason]'"]},
        {"role": "model", "parts": ["Understood. I'll analyze the chat history you provide and determine the emotional sentiment, choosing from fear, disgust, admiration, sadness, anger, happiness, anxiety, depression, stress, suicidal, bipolar, or personality disorder. I'll also provide a brief reason for my assessment. I'll format the response as requested."]},
        {"role": "user", "parts": [history]}
    ]
    
    try:
        chat = model.start_chat(history=conversation)
        response = chat.send_message(history)
        
        lines = response.text.split('\n', 1)
        sentiment = lines[0].split(': ')[1].strip()
        reason = lines[1].split(': ')[1].strip()
        
        return sentiment, reason
    except exceptions.ResourceExhausted:
        return "Unknown", "API quota exceeded"
    except Exception as e:
        return "Unknown", str(e)

def get_screening_data(request):
    session_id = chat_session_manager.get_or_create_session_id(request)
    history = chat_session_manager.get_chat_history(session_id)
    
    if not history:
        return JsonResponse({'error': 'No chat history available'})
    
    history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in history])
    
    sentiment, reason = get_sentiment(history_text)
    
    level = {
        "fear": 30,
        "disgust": 20,
        "admiration": 80,
        "sadness": 10,
        "anger": 40,
        "happiness": 90,
        "anxiety": 20,
        "depression": 10,
        "stress": 30,
        "suicidal": 5,
        "bipolar": 15,
        "personality disorder": 50
    }.get(sentiment.lower(), 50)
    
    status = "Good" if level >= 70 else "Moderate" if level >= 40 else "Low"
    status_color = "success" if status == "Good" else "warning" if status == "Moderate" else "danger"
    
    data = {
        "id": session_id,
        "username": request.user.username if request.user.is_authenticated else "Anonymous",
        "sentiment": sentiment,
        "level": level,
        "level_description": "excellent" if level >= 80 else "good" if level >= 60 else "okay" if level >= 40 else "concerning",
        "status": status,
        "status_color": status_color,
        "time": datetime.now().strftime("%H:%M"),
        "reason": reason
    }
    
    return JsonResponse(data)

@login_required
def tables(request):
    emotional_sentiments = [
        {"name": "Fear", "level": 30, "description": "concerning", "status": "Low", "status_color": "danger"},
        {"name": "Disgust", "level": 20, "description": "concerning", "status": "Low", "status_color": "danger"},
        {"name": "Admiration", "level": 80, "description": "excellent", "status": "Good", "status_color": "success"},
        {"name": "Sadness", "level": 10, "description": "concerning", "status": "Low", "status_color": "danger"},
        {"name": "Anger", "level": 40, "description": "okay", "status": "Moderate", "status_color": "warning"},
        {"name": "Happiness", "level": 90, "description": "excellent", "status": "Good", "status_color": "success"},
        {"name": "Anxiety", "level": 20, "description": "concerning", "status": "Low", "status_color": "danger"},
        {"name": "Depression", "level": 10, "description": "concerning", "status": "Low", "status_color": "danger"},
        {"name": "Stress", "level": 30, "description": "concerning", "status": "Low", "status_color": "danger"},
        {"name": "Suicidal", "level": 5, "description": "critical", "status": "Low", "status_color": "danger"},
        {"name": "Bipolar", "level": 15, "description": "concerning", "status": "Low", "status_color": "danger"},
        {"name": "Personality disorder", "level": 50, "description": "okay", "status": "Moderate", "status_color": "warning"},
    ]
    return render(request, 'pages/tables.html', {'segment': 'tables', 'emotional_sentiments': emotional_sentiments})

def billing(request):
    return render(request, 'pages/billing.html', { 'segment': 'billing' })

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

