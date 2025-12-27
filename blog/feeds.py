"""
RSS 피드 클래스
최신 블로그 게시글을 RSS 형식으로 제공
"""
from django.contrib.syndication.views import Feed
from django.utils import timezone
from .models import Post


class LatestPostsFeed(Feed):
    """최신 게시글 RSS 피드"""
    title = "서로소식 블로그"
    link = "/"
    description = "최신 블로그 게시글을 확인하세요"
    
    def items(self):
        """발행된 게시글 최신 10개 반환"""
        now = timezone.now()
        # status=published 또는 예약발행 시간이 지난 글
        published = Post.objects.filter(
            status='published',
            is_public=True
        )
        scheduled_published = Post.objects.filter(
            status='scheduled',
            is_public=True,
            published_at__lte=now
        )
        return (published | scheduled_published).order_by('-created_at')[:10]
    
    def item_title(self, item):
        return item.title
    
    def item_description(self, item):
        # 메타 설명이 있으면 사용, 없으면 본문 앞부분
        if item.meta_description:
            return item.meta_description
        return item.content[:200] + '...' if len(item.content) > 200 else item.content
    
    def item_link(self, item):
        return item.get_absolute_url()
    
    def item_pubdate(self, item):
        return item.created_at
    
    def item_author_name(self, item):
        return item.author.username


class CategoryFeed(Feed):
    """카테고리별 RSS 피드"""
    
    def get_object(self, request, slug):
        from .models import Category
        return Category.objects.get(slug=slug)
    
    def title(self, obj):
        return f"서로소식 블로그 - {obj.name}"
    
    def link(self, obj):
        return obj.get_absolute_url()
    
    def description(self, obj):
        return f"{obj.name} 카테고리의 최신 게시글"
    
    def items(self, obj):
        now = timezone.now()
        published = Post.objects.filter(
            category=obj,
            status='published',
            is_public=True
        )
        scheduled_published = Post.objects.filter(
            category=obj,
            status='scheduled',
            is_public=True,
            published_at__lte=now
        )
        return (published | scheduled_published).order_by('-created_at')[:10]
    
    def item_title(self, item):
        return item.title
    
    def item_description(self, item):
        if item.meta_description:
            return item.meta_description
        return item.content[:200] + '...' if len(item.content) > 200 else item.content
    
    def item_link(self, item):
        return item.get_absolute_url()
    
    def item_pubdate(self, item):
        return item.created_at
