from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
import json
from .models import Post, Comment, Category, Tag
from .forms import PostForm, CommentForm, SignUpForm


def post_list(request):
    """게시글 목록"""
    posts = Post.objects.filter(is_public=True)
    
    # 검색 기능
    query = request.GET.get('q')
    if query:
        posts = posts.filter(
            Q(title__icontains=query) | Q(content__icontains=query)
        )
    
    # 정렬 기능
    sort = request.GET.get('sort', 'latest')  # 기본값: 최신순
    if sort == 'views':
        posts = posts.order_by('-views', '-created_at')
    else:  # latest
        posts = posts.order_by('-created_at')
    
    # 페이지네이션
    paginator = Paginator(posts, 10)
    page = request.GET.get('page')
    posts = paginator.get_page(page)
    
    # 인기글 (조회수 Top 5)
    popular_posts = Post.objects.filter(is_public=True).order_by('-views')[:5]
    
    return render(request, 'blog/post_list.html', {
        'posts': posts,
        'query': query,
        'sort': sort,
        'popular_posts': popular_posts,
    })


def post_detail(request, pk):
    """게시글 상세"""
    post = get_object_or_404(Post, pk=pk)
    
    # 비공개 글은 작성자만 볼 수 있음
    if not post.is_public and post.author != request.user:
        messages.error(request, '이 글을 볼 권한이 없습니다.')
        return redirect('post_list')
    
    # 조회수 증가 (세션 기반 중복 방지)
    session_key = f'viewed_post_{pk}'
    if not request.session.get(session_key, False):
        post.increment_views()
        request.session[session_key] = True
    
    comments = post.comments.all()
    comment_form = CommentForm()
    
    # 인기글 (조회수 Top 5)
    popular_posts = Post.objects.filter(is_public=True).order_by('-views')[:5]
    
    return render(request, 'blog/post_detail.html', {
        'post': post,
        'comments': comments,
        'comment_form': comment_form,
        'popular_posts': popular_posts,
    })


@login_required
def post_create(request):
    """게시글 작성"""
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            form.save_m2m()  # ManyToMany 필드 저장
            messages.success(request, '게시글이 작성되었습니다.')
            return redirect('post_detail', pk=post.pk)
    else:
        form = PostForm()
    
    # 카테고리별 태그 데이터 전달
    categories = Category.objects.all()
    tags_by_category = {cat.id: list(cat.tags.values('id', 'name')) for cat in categories}
    
    return render(request, 'blog/post_form.html', {
        'form': form,
        'action': '작성',
        'tags_by_category': json.dumps(tags_by_category)
    })


@login_required
def post_update(request, pk):
    """게시글 수정"""
    post = get_object_or_404(Post, pk=pk)
    
    # 작성자만 수정 가능
    if post.author != request.user:
        messages.error(request, '수정 권한이 없습니다.')
        return redirect('post_detail', pk=pk)
    
    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, '게시글이 수정되었습니다.')
            return redirect('post_detail', pk=post.pk)
    else:
        form = PostForm(instance=post)
    
    # 카테고리별 태그 데이터 전달
    categories = Category.objects.all()
    tags_by_category = {cat.id: list(cat.tags.values('id', 'name')) for cat in categories}
    
    return render(request, 'blog/post_form.html', {
        'form': form,
        'action': '수정',
        'tags_by_category': json.dumps(tags_by_category)
    })


@login_required
def post_delete(request, pk):
    """게시글 삭제"""
    post = get_object_or_404(Post, pk=pk)
    
    # 작성자만 삭제 가능
    if post.author != request.user:
        messages.error(request, '삭제 권한이 없습니다.')
        return redirect('post_detail', pk=pk)
    
    if request.method == 'POST':
        post.delete()
        messages.success(request, '게시글이 삭제되었습니다.')
        return redirect('post_list')
    
    return render(request, 'blog/post_confirm_delete.html', {'post': post})


@login_required
def comment_create(request, pk):
    """댓글 작성"""
    post = get_object_or_404(Post, pk=pk)
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            messages.success(request, '댓글이 작성되었습니다.')
    
    return redirect('post_detail', pk=pk)


@login_required
def comment_delete(request, pk, comment_pk):
    """댓글 삭제"""
    comment = get_object_or_404(Comment, pk=comment_pk)
    
    # 작성자만 삭제 가능
    if comment.author != request.user:
        messages.error(request, '삭제 권한이 없습니다.')
    else:
        comment.delete()
        messages.success(request, '댓글이 삭제되었습니다.')
    
    return redirect('post_detail', pk=pk)


def signup(request):
    """회원가입"""
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, '회원가입이 완료되었습니다.')
            return redirect('post_list')
    else:
        form = SignUpForm()
    
    return render(request, 'registration/signup.html', {'form': form})


@login_required
def my_posts(request):
    """내 게시글 목록"""
    posts = Post.objects.filter(author=request.user)
    paginator = Paginator(posts, 10)
    page = request.GET.get('page')
    posts = paginator.get_page(page)
    
    return render(request, 'blog/my_posts.html', {'posts': posts})


def category_posts(request, slug):
    """카테고리별 게시글 목록"""
    category = get_object_or_404(Category, slug=slug)
    posts = Post.objects.filter(category=category, is_public=True)
    
    # 정렬 기능
    sort = request.GET.get('sort', 'latest')
    if sort == 'views':
        posts = posts.order_by('-views', '-created_at')
    else:
        posts = posts.order_by('-created_at')
    
    # 페이지네이션
    paginator = Paginator(posts, 10)
    page = request.GET.get('page')
    posts = paginator.get_page(page)
    
    # 인기글
    popular_posts = Post.objects.filter(is_public=True).order_by('-views')[:5]
    
    return render(request, 'blog/category_posts.html', {
        'category': category,
        'posts': posts,
        'sort': sort,
        'popular_posts': popular_posts,
    })


def tag_posts(request, slug):
    """태그별 게시글 목록"""
    tag = get_object_or_404(Tag, slug=slug)
    posts = Post.objects.filter(tags=tag, is_public=True)
    
    # 정렬 기능
    sort = request.GET.get('sort', 'latest')
    if sort == 'views':
        posts = posts.order_by('-views', '-created_at')
    else:
        posts = posts.order_by('-created_at')
    
    # 페이지네이션
    paginator = Paginator(posts, 10)
    page = request.GET.get('page')
    posts = paginator.get_page(page)
    
    # 인기글
    popular_posts = Post.objects.filter(is_public=True).order_by('-views')[:5]
    
    return render(request, 'blog/tag_posts.html', {
        'tag': tag,
        'posts': posts,
        'sort': sort,
        'popular_posts': popular_posts,
    })
