from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.text import slugify


class Category(models.Model):
    """카테고리 모델"""
    name = models.CharField(max_length=100, unique=True, verbose_name='카테고리명')
    slug = models.SlugField(max_length=100, unique=True, verbose_name='슬러그')
    description = models.TextField(blank=True, verbose_name='설명')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    
    class Meta:
        verbose_name = '카테고리'
        verbose_name_plural = '카테고리 목록'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('category_posts', kwargs={'slug': self.slug})


class Tag(models.Model):
    """태그 모델"""
    name = models.CharField(max_length=50, verbose_name='태그명')
    slug = models.SlugField(max_length=50, verbose_name='슬러그')
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='tags',
        verbose_name='카테고리',
        help_text='이 태그가 속한 카테고리'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    
    class Meta:
        verbose_name = '태그'
        verbose_name_plural = '태그 목록'
        ordering = ['category', 'name']
        unique_together = ['category', 'name']  # 같은 카테고리 내에서 태그명 중복 방지
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f'{self.category.slug}-{self.name}', allow_unicode=True)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('tag_posts', kwargs={'slug': self.slug})


class Post(models.Model):
    """게시글 모델"""
    title = models.CharField(max_length=200, verbose_name='제목')
    slug = models.SlugField(max_length=200, unique=True, blank=True, verbose_name='슬러그')
    content = models.TextField(verbose_name='내용')
    author = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='posts',
        verbose_name='작성자'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='posts',
        verbose_name='카테고리'
    )
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name='posts',
        verbose_name='태그'
    )
    views = models.PositiveIntegerField(default=0, verbose_name='조회수')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='작성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    is_public = models.BooleanField(default=True, verbose_name='공개 여부')
    
    class Meta:
        verbose_name = '게시글'
        verbose_name_plural = '게시글 목록'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)
            # 중복 slug 방지
            original_slug = self.slug
            counter = 1
            while Post.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f'{original_slug}-{counter}'
                counter += 1
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('post_detail', kwargs={'pk': self.pk})
    
    def increment_views(self):
        """조회수 증가"""
        self.views += 1
        self.save(update_fields=['views'])


class Comment(models.Model):
    """댓글 모델"""
    post = models.ForeignKey(
        Post, 
        on_delete=models.CASCADE, 
        related_name='comments',
        verbose_name='게시글'
    )
    author = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='comments',
        verbose_name='작성자'
    )
    content = models.TextField(verbose_name='내용')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='작성일')
    
    class Meta:
        verbose_name = '댓글'
        verbose_name_plural = '댓글 목록'
        ordering = ['created_at']
    
    def __str__(self):
        return f'{self.author.username}: {self.content[:20]}'
