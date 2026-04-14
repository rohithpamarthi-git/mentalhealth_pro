from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from .models import Assessment, CounselorRequest, ChatMessage
import json
import traceback
import os
from django.http import JsonResponse
from django.contrib import messages
from django.conf import settings
from google import genai
from google.genai import types
from dotenv import load_dotenv
load_dotenv()

def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'wellness/home.html')

from django.contrib.auth.models import User

def register_view(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '')
        email = request.POST.get('email', '')
        password = request.POST.get('password', '')
        
        if email and password:
            if User.objects.filter(username=email).exists():
                messages.error(request, "An account with this email already exists.")
            else:
                # Use email as the username since that's what we log in with
                user = User.objects.create_user(username=email, email=email, password=password)
                name_parts = full_name.split(' ', 1)
                user.first_name = name_parts[0]
                if len(name_parts) > 1:
                    user.last_name = name_parts[1]
                user.save()
                
                login(request, user)
                return redirect('dashboard')
        else:
            messages.error(request, "Please fill out all the fields.")
            
    return render(request, 'wellness/register.html')

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'wellness/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('home')

@login_required
def dashboard(request):
    assessments = Assessment.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'wellness/dashboard.html', {'assessments': assessments})

@login_required
def assessment(request):
    if request.method == 'POST':
        # Simple scoring logic: each question is 0-3
        stress1 = int(request.POST.get('stress1', 0))
        stress2 = int(request.POST.get('stress2', 0))
        anx1 = int(request.POST.get('anx1', 0))
        anx2 = int(request.POST.get('anx2', 0))
        dep1 = int(request.POST.get('dep1', 0))
        dep2 = int(request.POST.get('dep2', 0))

        stress_score = stress1 + stress2
        anxiety_score = anx1 + anx2
        depression_score = dep1 + dep2
        total_score = stress_score + anxiety_score + depression_score

        category = "Low"
        if total_score > 12:
            category = "High"
            messages.warning(request, "Your score is high. We strongly recommend speaking with a counselor.")
        elif total_score > 6:
            category = "Medium"

        assessment_record = Assessment.objects.create(
            user=request.user,
            stress_score=stress_score,
            anxiety_score=anxiety_score,
            depression_score=depression_score,
            total_score=total_score,
            category=category
        )
        return render(request, 'wellness/assessment_result.html', {'assessment': assessment_record})

    return render(request, 'wellness/assessment.html')

@login_required
def chatbot(request):
    chat_history = ChatMessage.objects.filter(user=request.user).order_by('created_at')
    return render(request, 'wellness/chatbot.html', {'chat_history': chat_history})

# Initialize Gemini Client at module level
GENAI_CLIENT = None

def get_genai_client():
    global GENAI_CLIENT
    if GENAI_CLIENT is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            try:
                GENAI_CLIENT = genai.Client(api_key=api_key)
                
            except Exception as e:
                print(f"Error initializing GenAI Client: {e}")
    return GENAI_CLIENT

def get_chatbot_config():
    # Centralized configuration for the chatbot behavior
    system_instruction = (
        "You are a Support Chatbot for the MindCare platform. Your sole purpose is to provide a safe space "
        "to discuss mental health, psychology, emotions, and well-being.\n\n"
        "Strict Rules:\n"
        "1. BOUNDARY ENFORCEMENT: You are strictly limited to mental health and psychology. "
        "If a user asks about anything unrelated, you MUST politely decline.\n"
        "2. Always be deeply empathetic, professional, and validating.\n"
        "3. Do NOT provide medical diagnoses.\n"
        "4. Keep responses concise, conversational, and split into small easily readable paragraphs."
    )
    return types.GenerateContentConfig(
        system_instruction=system_instruction,
        max_output_tokens=500,
        temperature=0.7,
    )

@login_required
def chatbot_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_text = data.get('text', '').strip()
            if not user_text:
                return JsonResponse({'error': 'No text provided'}, status=400)

            # Save user message
            ChatMessage.objects.create(user=request.user, text=user_text, is_bot=False)

            client = get_genai_client()
            if not client:
                print("Chatbot Error: GEMINI_API_KEY not configured correctly.")
                bot_text = "I'm here for you, but my AI core is currently offline. Please check the API configuration."
            else:
                try:
                    # Use the new SDK syntax for generation
                    response = client.models.generate_content(
                        model="gemini-flash-latest",
                        contents=user_text,
                        config=get_chatbot_config()
                    )
                    
                    if response.text:
                        bot_text = response.text.strip()
                    else:
                        bot_text = "I'm here to listen. Could you tell me more about that?"
                
                except Exception as e:
                    # Log full error for server-side debugging
                    print(f"Chatbot Generation Error ({type(e).__name__}): {e}")
                    traceback.print_exc()
                    
                    # Provide slightly more specific user-facing feedback if it's an API error
                    err_msg = str(e).lower()
                    if "api_key" in err_msg or "authentication" in err_msg or "permission" in err_msg or "403" in err_msg:
                        bot_text = "I'm having trouble connecting to my AI brain (API key issue). Please ensure a valid API key is set."
                    elif "quota" in err_msg or "rate limit" in err_msg or "429" in err_msg:
                        bot_text = "I've been talking a bit too much lately! Let's take a short break and try again in a few minutes."
                    else:
                        bot_text = "I'm sorry, I'm having trouble processing that right now. I'm still here for you."

            # Save bot message
            ChatMessage.objects.create(user=request.user, text=bot_text, is_bot=True)
            return JsonResponse({'response': bot_text})

        except json.JSONDecodeError as e:
            print(f"[chatbot_api] JSON decode error: {e}")
            return JsonResponse({'error': f'Invalid JSON in request body: {e}'}, status=400)

        except Exception as e:
            print(f"[chatbot_api] Unexpected error: {type(e).__name__}: {e}")
            traceback.print_exc()
            return JsonResponse({'error': f'{type(e).__name__}: {str(e)}'}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required
def counselor_request(request):
    if request.method == 'POST':
        message = request.POST.get('message', '')
        if message:
            CounselorRequest.objects.create(user=request.user, message=message)
            messages.success(request, "Your request has been submitted. A counselor will reach out to you soon.")
            return redirect('dashboard')
    return render(request, 'wellness/request_counselor.html')

@login_required
def resources(request):
    return render(request, 'wellness/resources.html')


