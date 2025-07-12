# d:\BlogCheatKey\blog_cheatkey_v2\blog_cheatkey\backend\content\models.py

from django.db import models
from django.conf import settings
from backend.key_word.models import Keyword

class BlogContent(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    keyword = models.ForeignKey(Keyword, on_delete=models.CASCADE, related_name='contents')
    title = models.CharField(max_length=255)
    content = models.TextField()
    mobile_formatted_content = models.TextField(blank=True, null=True)
    references = models.JSONField(default=list, blank=True)
    char_count = models.IntegerField(default=0)
    is_optimized = models.BooleanField(default=False)
    meta_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.keyword.keyword} - {self.title}"

    class Meta:
        verbose_name = '블로그 콘텐츠'
        verbose_name_plural = '블로그 콘텐츠'

class MorphemeAnalysis(models.Model):
    content = models.ForeignKey('BlogContent', on_delete=models.CASCADE, related_name='morpheme_analyses')
    morpheme = models.CharField(max_length=100)
    count = models.IntegerField(default=0)
    is_valid = models.BooleanField(default=False)
    # 👇 이 필드가 데이터베이스에 추가되어야 합니다.
    morpheme_type = models.CharField(max_length=20, default='unknown') 

    class Meta:
        unique_together = ('content', 'morpheme')
        verbose_name = '형태소 분석 결과'
        verbose_name_plural = '형태소 분석 결과'

    def __str__(self):
        return f"{self.content.keyword.keyword} - {self.morpheme}: {self.count}회 ({'유효' if self.is_valid else '무효'})"

