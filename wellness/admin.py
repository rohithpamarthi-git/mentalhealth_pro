from django.contrib import admin
from .models import Assessment, CounselorRequest, ChatMessage

admin.site.register(Assessment)
admin.site.register(CounselorRequest)
admin.site.register(ChatMessage)
