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
    
    # 상태 선택지
    STATUS_CHOICES = [
        ('draft', '임시저장'),
        ('published', '발행됨'),
        ('scheduled', '예약발행'),
    ]
    
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
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='draft', 
        verbose_name='상태'
    )
    published_at = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name='발행 예정일',
        help_text='예약발행 시 공개될 날짜와 시간'
    )
    views = models.PositiveIntegerField(default=0, verbose_name='조회수')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='작성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    is_public = models.BooleanField(default=True, verbose_name='공개 여부')
    meta_description = models.CharField(
        max_length=160, 
        blank=True, 
        verbose_name='메타 설명',
        help_text='검색 결과에 표시될 설명 (160자 이내)'
    )
    
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
    is_hidden = models.BooleanField(default=False, verbose_name='숨김')
    report_count = models.PositiveIntegerField(default=0, verbose_name='신고 횟수')
    
    class Meta:
        verbose_name = '댓글'
        verbose_name_plural = '댓글 목록'
        ordering = ['created_at']
    
    def __str__(self):
        return f'{self.author.username}: {self.content[:20]}'


class CommentReport(models.Model):
    """댓글 신고 모델"""
    REASON_CHOICES = [
        ('spam', '스팸/광고'),
        ('abuse', '욕설/비방'),
        ('hate', '혐오/차별'),
        ('illegal', '불법 정보'),
        ('other', '기타'),
    ]
    
    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        related_name='reports',
        verbose_name='댓글'
    )
    reporter = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comment_reports',
        verbose_name='신고자'
    )
    reason = models.CharField(
        max_length=10,
        choices=REASON_CHOICES,
        verbose_name='신고 사유'
    )
    detail = models.TextField(blank=True, verbose_name='상세 내용')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='신고일')
    
    class Meta:
        verbose_name = '댓글 신고'
        verbose_name_plural = '댓글 신고 목록'
        unique_together = ['comment', 'reporter']  # 중복 신고 방지
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.reporter.username} → {self.comment.pk}: {self.get_reason_display()}'


class PostImage(models.Model):
    """게시글 이미지"""
    image = models.ImageField(upload_to='posts/%Y/%m/', verbose_name='이미지')
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='uploaded_images',
        verbose_name='업로더'
    )
    alt_text = models.CharField(max_length=200, blank=True, verbose_name='대체 텍스트')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='업로드일')
    
    class Meta:
        verbose_name = '게시글 이미지'
        verbose_name_plural = '게시글 이미지 목록'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.uploaded_by.username} - {self.image.name}'


class UserProfile(models.Model):
    """사용자 프로필"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='사용자'
    )
    bio = models.TextField(blank=True, verbose_name='자기소개')
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        verbose_name='프로필 이미지'
    )
    website = models.URLField(blank=True, verbose_name='웹사이트')
    github = models.CharField(max_length=100, blank=True, verbose_name='GitHub')
    skills = models.TextField(
        blank=True,
        verbose_name='기술 스택',
        help_text='쉼표로 구분하여 입력 (예: Python, Django, JavaScript)'
    )
    location = models.CharField(max_length=100, blank=True, verbose_name='위치')
    
    class Meta:
        verbose_name = '사용자 프로필'
        verbose_name_plural = '사용자 프로필 목록'
    
    def __str__(self):
        return f'{self.user.username}의 프로필'
    
    def get_skills_list(self):
        """기술 스택을 리스트로 반환"""
        if self.skills:
            return [s.strip() for s in self.skills.split(',') if s.strip()]
        return []
