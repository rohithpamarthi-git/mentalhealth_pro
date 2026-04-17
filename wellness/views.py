from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from .models import Assessment, CounselorRequest, ChatMessage, DailyMood
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
    raw_assessments = Assessment.objects.filter(user=request.user).order_by('-created_at')
    assessments = []
    for asm in raw_assessments:
        # Determine if it's a legacy record and normalize for display
        if "Stress" not in asm.category or asm.total_score > 10:
            normalized = round(asm.total_score * 10 / 18)
            asm.total_score = normalized
            if normalized >= 8:
                asm.category = "High Stress"
            elif normalized >= 4:
                asm.category = "Moderate Stress"
            else:
                asm.category = "Low Stress"
        assessments.append(asm)
    return render(request, 'wellness/dashboard.html', {'assessments': assessments})

@login_required
def assessment(request):
    if request.method == 'POST':
        # Sum raw scores (0-3 for each of 10 questions)
        raw_total = 0
        for i in range(1, 11):
            raw_total += int(request.POST.get(f'q{i}', 0))

        # Normalize to 10-point scale: (raw_total / 30) * 10 = raw_total / 3
        # We'll store it as an integer 0-10
        total_score = min(10, round(raw_total / 3))

        # New category logic (0-3 Low, 4-7 Moderate, 8-10 High)
        category = "Low Stress"
        if total_score >= 8:
            category = "High Stress"
            messages.warning(request, "Your score is high. We strongly recommend speaking with a counselor.")
        elif total_score >= 4:
            category = "Moderate Stress"

        assessment_record = Assessment.objects.create(
            user=request.user,
            stress_score=0, # Deprecated but kept for model compatibility
            anxiety_score=0,
            depression_score=0,
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
        "4. Keep responses concise and balanced.\n"
        "5. Always respond in 1 to 2 short paragraphs only and hightligh main points.\n"
        "6. Do NOT exceed 2 paragraphs.\n"
        "7. Each paragraph should be clear, simple english, and easy to read."
    )
    return types.GenerateContentConfig(
        system_instruction=system_instruction,
        max_output_tokens=800,
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
                    models_to_try = [
                        "models/gemini-flash-latest",
                        "models/gemini-2.5-flash",
                        "models/gemini-2.5-flash-lite"
                    ]
                    
                    bot_text = None

                    for model_name in models_to_try:
                        try:
                            response = client.models.generate_content(
                                model=model_name,
                                contents=user_text,
                                config=get_chatbot_config()
                            )

                            if response.text:
                                bot_text = response.text.strip()
                                break

                        except Exception as e:
                            err_msg = str(e).lower()

                            # If rate limit → try next model
                            if "quota" in err_msg or "rate limit" in err_msg or "429" in err_msg:
                                continue
                            else:
                                raise e

                    # fallback if all models fail
                    if not bot_text:
                        bot_text = "I'm currently busy due to high demand. Please try again later."
                
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
        subject = request.POST.get('subject', 'General Support')
        urgency = request.POST.get('urgency', 'Medium')
        original_message = request.POST.get('message', '')
        
        if original_message:
            message = f"Subject: {subject}\nUrgency: {urgency}\n\n{original_message}"
            CounselorRequest.objects.create(user=request.user, message=message)
            messages.success(request, "Request submitted successfully. Status: Pending - We will contact you soon.")
            return redirect('dashboard')
    return render(request, 'wellness/request_counselor.html')

@login_required
def resources(request):
    return render(request, 'wellness/resources.html')


@login_required
def progress_view(request):
    from datetime import date
    import math
    
    # Handle Daily Mood submission
    if request.method == 'POST' and 'mood_score' in request.POST:
        mood_score = int(request.POST.get('mood_score', 3))
        # Ensure only ONE mood entry per user per day
        today = date.today()
        # Check if already submitted today
        if not DailyMood.objects.filter(user=request.user, created_at__date=today).exists():
            DailyMood.objects.create(user=request.user, mood_score=mood_score)
            messages.success(request, "Daily mood logged successfully!")
        else:
            # Optionally update the existing entry
            mood_entry = DailyMood.objects.filter(user=request.user, created_at__date=today).first()
            mood_entry.mood_score = mood_score
            mood_entry.save()
            messages.success(request, "Daily mood updated!")
        return redirect('progress')

    raw_assessments = Assessment.objects.filter(user=request.user).order_by('-created_at')
    
    assessments = []
    for asm in raw_assessments:
        is_legacy = "Stress" not in asm.category or asm.total_score > 10
        if is_legacy:
            normalized = round(asm.total_score * 10 / 18)
            asm.total_score = normalized
            if normalized >= 8:
                asm.category = "High Stress"
            elif normalized >= 4:
                asm.category = "Moderate Stress"
            else:
                asm.category = "Low Stress"
        assessments.append(asm)

    total_assessments = len(assessments)
    avg_score = 0
    avg_label = "N/A"
    last_assessment = None
    chart_stress_data = []
    chart_mood_data = []
    chart_labels = []

    if total_assessments > 0:
        # Weighted Stress Calculation using last 5 assessments
        recent_5 = assessments[:5]
        weights = [5, 4, 3, 2, 1]
        weighted_sum = 0
        weight_total = 0
        for i, asm in enumerate(recent_5):
            weight = weights[i] if i < len(weights) else 1
            weighted_sum += asm.total_score * weight
            weight_total += weight
        
        base_stress = weighted_sum / weight_total if weight_total > 0 else 0
        
        # Mood Adjustment
        today_mood = DailyMood.objects.filter(user=request.user).order_by('-created_at').first()
        mood_adjustment = 0
        if today_mood:
            mood_val = today_mood.mood_score
            if mood_val == 1: mood_adjustment = 1.5
            elif mood_val == 2: mood_adjustment = 1.0
            elif mood_val == 3: mood_adjustment = 0
            elif mood_val == 4: mood_adjustment = -0.5
            elif mood_val == 5: mood_adjustment = -1.0
            
        final_stress = base_stress + mood_adjustment
        
        # Clamp final stress between 0-10
        avg_score = round(max(0, min(10, final_stress)), 1)
        
        if avg_score >= 7:
            avg_label = "High Stress"
        elif avg_score >= 4:
            avg_label = "Moderate Stress"
        else:
            avg_label = "Low Stress"
        
        last_assessment = assessments[0].created_at
        
        # Chart Data
        recent_10_assess = assessments[:10][::-1]
        chart_stress_data = [asm.total_score for asm in recent_10_assess]
        chart_labels = [asm.created_at.strftime("%b %d") for asm in recent_10_assess]
        
        # Fetch corresponding moods for the chart (for simplicity, we'll get latest 10 moods to overlay)
        recent_moods = DailyMood.objects.filter(user=request.user).order_by('-created_at')[:10][::-1]
        
        # We need a mood value for each chart point, or just pass the recent 10 moods
        # Let's just create an array of mood scores, normalized for the chart (mood_score * 2)
        chart_mood_data = [(m.mood_score * 2) for m in recent_moods]
        
        # If lengths don't match, just pad mood data with Nones or previous values so Chart.js handles it gracefully
        while len(chart_mood_data) < len(chart_stress_data):
            chart_mood_data.insert(0, None)

    context = {
        'assessments': assessments,
        'total_assessments': total_assessments,
        'avg_score': avg_score,
        'avg_label': avg_label,
        'last_assessment': last_assessment,
        'chart_labels': json.dumps(chart_labels),
        'chart_stress_data': json.dumps(chart_stress_data),
        'chart_mood_data': json.dumps(chart_mood_data),
    }
    return render(request, 'wellness/progress.html', context)


