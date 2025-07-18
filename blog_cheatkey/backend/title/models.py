from django.db import models
from backend.content.models import BlogContent

class TitleSuggestion(models.Model):
    """제목 추천 모델"""
    TYPE_CHOICES = (
        ('general', '일반 상식 반박형'),
        ('approval', '인정욕구 자극형'),
        ('secret', '숨겨진 비밀형'),
        ('trend', '트렌드 제시형'),
        ('failure', '실패담 공유형'),
        ('comparison', '비교형'),
        ('warning', '경고형'),
        ('blame', '남탓 공감형'),
        ('beginner', '초보자 가이드형'),
        ('benefit', '효과 제시형'),
    )
    
    content = models.ForeignKey(BlogContent, on_delete=models.CASCADE, related_name='title_suggestions', verbose_name="콘텐츠")
    title_type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name="제목 유형")
    suggestion = models.CharField(max_length=300, verbose_name="추천 제목")
    selected = models.BooleanField(default=False, verbose_name="선택 여부")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    
    class Meta:
        verbose_name = "제목 추천"
        verbose_name_plural = "제목 추천 목록"
        ordering = ['title_type', '-created_at']
    
    def __str__(self):
        return self.suggestion
