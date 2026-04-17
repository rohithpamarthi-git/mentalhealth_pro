from django.db import models
from django.contrib.auth.models import User

class Assessment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stress_score = models.IntegerField(default=0)
    anxiety_score = models.IntegerField(default=0)
    depression_score = models.IntegerField(default=0)
    total_score = models.IntegerField(default=0)
    category = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.category} - {self.created_at.strftime('%Y-%m-%d')}"

class CounselorRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Request from {self.user.username} - Resolved: {self.is_resolved}"

class ChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    is_bot = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {'Bot' if self.is_bot else 'User'} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

class DailyMood(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    mood_score = models.IntegerField(default=3) # 1 to 5
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - Mood: {self.mood_score} - {self.created_at.strftime('%Y-%m-%d')}"
