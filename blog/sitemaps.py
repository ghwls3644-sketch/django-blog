"""
Sitemap 클래스
검색 엔진 크롤링 최적화를 위한 sitemap.xml 생성
"""
from django.contrib.sitemaps import Sitemap
from django.utils import timezone
from .models import Post, Category


class PostSitemap(Sitemap):
    """게시글 사이트맵"""
    changefreq = 'weekly'
    priority = 0.9
    
    def items(self):
        """발행된 게시글 반환"""
        now = timezone.now()
        published = Post.objects.filter(
            status='published',
            is_public=True
        )
        scheduled_published = Post.objects.filter(
            status='scheduled',
            is_public=True,
            published_at__lte=now
        )
        return published | scheduled_published
    
    def lastmod(self, obj):
        return obj.updated_at
    
    def location(self, obj):
        return obj.get_absolute_url()


class CategorySitemap(Sitemap):
    """카테고리 사이트맵"""
    changefreq = 'weekly'
    priority = 0.7
    
    def items(self):
        return Category.objects.all()
    
    def location(self, obj):
        return obj.get_absolute_url()


class StaticViewSitemap(Sitemap):
    """정적 페이지 사이트맵"""
    priority = 0.5
    changefreq = 'monthly'
    
    def items(self):
        return ['post_list']
    
    def location(self, item):
        from django.urls import reverse
        return reverse(item)
