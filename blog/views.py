from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django.http import JsonResponse
import json
from .models import Post, Comment, Category, Tag, CommentReport, PostImage, UserProfile
from .forms import PostForm, CommentForm, SignUpForm, UserProfileForm
from django.contrib.auth.models import User
from django_ratelimit.decorators import ratelimit
from django_ratelimit.exceptions import Ratelimited


def get_published_posts():
    """발행된 게시글만 반환 (예약발행 시간 체크 포함)"""
    now = timezone.now()
    return Post.objects.filter(
        is_public=True,
        status='published'
    ) | Post.objects.filter(
        is_public=True,
        status='scheduled',
        published_at__lte=now
    )


def post_list(request):
    """게시글 목록"""
    posts = get_published_posts()
    
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
    popular_posts = get_published_posts().order_by('-views')[:5]
    
    return render(request, 'blog/post_list.html', {
        'posts': posts,
        'query': query,
        'sort': sort,
        'popular_posts': popular_posts,
    })


def post_detail(request, pk):
    """게시글 상세"""
    post = get_object_or_404(Post, pk=pk)
    
    # 비공개 글 또는 미발행 글은 작성자만 볼 수 있음
    is_author = request.user.is_authenticated and post.author == request.user
    is_viewable = post.is_public and post.status == 'published'
    is_scheduled_published = (
        post.status == 'scheduled' and 
        post.published_at and 
        post.published_at <= timezone.now()
    )
    
    if not is_author and not (is_viewable or is_scheduled_published):
        messages.error(request, '이 글을 볼 권한이 없습니다.')
        return redirect('post_list')
    
    # 댓글 허용 여부 - 발행된 글만 댓글 가능
    can_comment = is_viewable or is_scheduled_published
    
    # 조회수 증가 (세션 기반 중복 방지) - 발행된 글만
    if is_viewable or is_scheduled_published:
        session_key = f'viewed_post_{pk}'
        if not request.session.get(session_key, False):
            post.increment_views()
            request.session[session_key] = True
    
    comments = post.comments.all()
    comment_form = CommentForm()
    
    # 인기글 (조회수 Top 5)
    popular_posts = get_published_posts().order_by('-views')[:5]
    
    # 관련 글 추천 (같은 카테고리 또는 같은 태그)
    related_posts = []
    if post.category or post.tags.exists():
        related_query = get_published_posts().exclude(pk=post.pk)
        
        if post.category:
            # 같은 카테고리 글
            category_posts = related_query.filter(category=post.category)[:3]
            related_posts.extend(category_posts)
        
        if post.tags.exists() and len(related_posts) < 5:
            # 같은 태그를 가진 글 (중복 제외)
            existing_ids = [p.pk for p in related_posts]
            tag_posts = related_query.filter(
                tags__in=post.tags.all()
            ).exclude(pk__in=existing_ids).distinct()[:5 - len(related_posts)]
            related_posts.extend(tag_posts)
    
    return render(request, 'blog/post_detail.html', {
        'post': post,
        'comments': comments,
        'comment_form': comment_form,
        'popular_posts': popular_posts,
        'can_comment': can_comment,
        'related_posts': related_posts,
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
            
            # 상태별 메시지
            if post.status == 'draft':
                messages.success(request, '임시저장되었습니다.')
            elif post.status == 'scheduled':
                messages.success(request, f'예약발행이 설정되었습니다. ({post.published_at.strftime("%Y-%m-%d %H:%M")})')
            else:
                messages.success(request, '게시글이 발행되었습니다.')
            
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
            updated_post = form.save()
            
            # 상태별 메시지
            if updated_post.status == 'draft':
                messages.success(request, '임시저장되었습니다.')
            elif updated_post.status == 'scheduled':
                messages.success(request, f'예약발행이 설정되었습니다. ({updated_post.published_at.strftime("%Y-%m-%d %H:%M")})')
            else:
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
@ratelimit(key='user', rate='30/h', method='POST', block=True)
def comment_create(request, pk):
    """댓글 작성"""
    post = get_object_or_404(Post, pk=pk)
    
    # 발행된 글에만 댓글 허용
    is_published = post.status == 'published'
    is_scheduled_published = (
        post.status == 'scheduled' and 
        post.published_at and 
        post.published_at <= timezone.now()
    )
    
    if not (is_published or is_scheduled_published):
        messages.error(request, '발행된 글에만 댓글을 작성할 수 있습니다.')
        return redirect('post_detail', pk=pk)
    
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


@ratelimit(key='ip', rate='5/h', method='POST', block=True)
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
    
    # 상태별 필터링
    status_filter = request.GET.get('status', 'all')
    if status_filter != 'all':
        posts = posts.filter(status=status_filter)
    
    # 상태별 개수
    status_counts = {
        'all': Post.objects.filter(author=request.user).count(),
        'draft': Post.objects.filter(author=request.user, status='draft').count(),
        'published': Post.objects.filter(author=request.user, status='published').count(),
        'scheduled': Post.objects.filter(author=request.user, status='scheduled').count(),
    }
    
    paginator = Paginator(posts, 10)
    page = request.GET.get('page')
    posts = paginator.get_page(page)
    
    return render(request, 'blog/my_posts.html', {
        'posts': posts,
        'status_filter': status_filter,
        'status_counts': status_counts,
    })


@login_required
def my_comments(request):
    """내 댓글 목록"""
    comments = Comment.objects.filter(author=request.user).order_by('-created_at')
    
    paginator = Paginator(comments, 20)
    page = request.GET.get('page')
    comments = paginator.get_page(page)
    
    return render(request, 'blog/my_comments.html', {
        'comments': comments,
    })


def category_posts(request, slug):
    """카테고리별 게시글 목록"""
    category = get_object_or_404(Category, slug=slug)
    now = timezone.now()
    # 발행된 글만 (status=published 또는 예약발행 시간 지난 글)
    posts = Post.objects.filter(
        category=category, 
        is_public=True,
        status='published'
    ) | Post.objects.filter(
        category=category,
        is_public=True,
        status='scheduled',
        published_at__lte=now
    )
    
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
    popular_posts = get_published_posts().order_by('-views')[:5]
    
    return render(request, 'blog/category_posts.html', {
        'category': category,
        'posts': posts,
        'sort': sort,
        'popular_posts': popular_posts,
    })


def tag_posts(request, slug):
    """태그별 게시글 목록"""
    tag = get_object_or_404(Tag, slug=slug)
    now = timezone.now()
    # 발행된 글만 (status=published 또는 예약발행 시간 지난 글)
    posts = Post.objects.filter(
        tags=tag, 
        is_public=True,
        status='published'
    ) | Post.objects.filter(
        tags=tag,
        is_public=True,
        status='scheduled',
        published_at__lte=now
    )
    
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
    popular_posts = get_published_posts().order_by('-views')[:5]
    
    return render(request, 'blog/tag_posts.html', {
        'tag': tag,
        'posts': posts,
        'sort': sort,
        'popular_posts': popular_posts,
    })


@login_required
def comment_report(request, pk, comment_pk):
    """댓글 신고"""
    comment = get_object_or_404(Comment, pk=comment_pk)
    post = get_object_or_404(Post, pk=pk)
    
    # 자기 댓글은 신고 불가
    if comment.author == request.user:
        messages.error(request, '자신의 댓글은 신고할 수 없습니다.')
        return redirect('post_detail', pk=pk)
    
    # 이미 신고한 경우
    if CommentReport.objects.filter(comment=comment, reporter=request.user).exists():
        messages.warning(request, '이미 신고한 댓글입니다.')
        return redirect('post_detail', pk=pk)
    
    if request.method == 'POST':
        reason = request.POST.get('reason', 'other')
        detail = request.POST.get('detail', '')
        
        # 신고 생성
        CommentReport.objects.create(
            comment=comment,
            reporter=request.user,
            reason=reason,
            detail=detail
        )
        
        # 신고 횟수 증가
        comment.report_count += 1
        
        # 신고 3회 이상 시 자동 숨김
        if comment.report_count >= 3:
            comment.is_hidden = True
        
        comment.save()
        messages.success(request, '신고가 접수되었습니다.')
    
    return redirect('post_detail', pk=pk)


@login_required
def comment_hide(request, pk, comment_pk):
    """댓글 숨김/표시 토글 (관리자 전용)"""
    if not request.user.is_staff:
        messages.error(request, '권한이 없습니다.')
        return redirect('post_detail', pk=pk)
    
    comment = get_object_or_404(Comment, pk=comment_pk)
    comment.is_hidden = not comment.is_hidden
    comment.save()
    
    action = '숨김' if comment.is_hidden else '표시'
    messages.success(request, f'댓글이 {action} 처리되었습니다.')
    
    return redirect('post_detail', pk=pk)


@login_required
@ratelimit(key='user', rate='20/h', method='POST', block=True)
def image_upload(request):
    """AJAX 이미지 업로드"""
    if request.method == 'POST' and request.FILES.get('image'):
        image_file = request.FILES['image']
        
        # 이미지 파일 검증
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        if image_file.content_type not in allowed_types:
            return JsonResponse({
                'error': '지원하지 않는 이미지 형식입니다. (JPG, PNG, GIF, WebP만 가능)'
            }, status=400)
        
        # 파일 크기 제한 (5MB)
        if image_file.size > 5 * 1024 * 1024:
            return JsonResponse({
                'error': '이미지 크기는 5MB 이하여야 합니다.'
            }, status=400)
        
        # 이미지 저장
        post_image = PostImage.objects.create(
            image=image_file,
            uploaded_by=request.user,
            alt_text=request.POST.get('alt_text', '')
        )
        
        return JsonResponse({
            'success': True,
            'url': post_image.image.url,
            'id': post_image.id,
            'markdown': f'![{post_image.alt_text or "image"}]({post_image.image.url})'
        })
    
    return JsonResponse({'error': '이미지를 선택해주세요.'}, status=400)


def user_profile(request, username):
    """사용자 프로필 보기"""
    profile_user = get_object_or_404(User, username=username)
    
    # 프로필이 없으면 생성
    profile, created = UserProfile.objects.get_or_create(user=profile_user)
    
    # 사용자의 발행된 글
    user_posts = get_published_posts().filter(author=profile_user).order_by('-created_at')[:5]
    
    # 통계
    stats = {
        'total_posts': Post.objects.filter(author=profile_user, status='published').count(),
        'total_views': sum(post.views for post in Post.objects.filter(author=profile_user)),
        'total_comments': Comment.objects.filter(author=profile_user).count(),
    }
    
    return render(request, 'blog/profile.html', {
        'profile_user': profile_user,
        'profile': profile,
        'user_posts': user_posts,
        'stats': stats,
    })


@login_required
def profile_edit(request):
    """내 프로필 편집"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, '프로필이 업데이트되었습니다.')
            return redirect('user_profile', username=request.user.username)
    else:
        form = UserProfileForm(instance=profile)
    
    return render(request, 'blog/profile_edit.html', {
        'form': form,
    })


@login_required
def backup_dashboard(request):
    """백업/복구 대시보드 (관리자 전용)"""
    if not request.user.is_staff:
        messages.error(request, '관리자만 접근할 수 있습니다.')
        return redirect('post_list')
    
    # 통계
    stats = {
        'total_posts': Post.objects.count(),
        'published_posts': Post.objects.filter(status='published').count(),
        'draft_posts': Post.objects.filter(status='draft').count(),
        'total_comments': Comment.objects.count(),
        'total_users': User.objects.count(),
        'total_categories': Category.objects.count(),
        'total_tags': Tag.objects.count(),
        'total_images': PostImage.objects.count(),
    }
    
    return render(request, 'blog/backup_dashboard.html', {
        'stats': stats,
    })


@login_required
def export_data(request, data_type):
    """데이터 내보내기 (JSON)"""
    if not request.user.is_staff:
        return JsonResponse({'error': '권한이 없습니다.'}, status=403)
    
    import json
    from django.http import HttpResponse
    from django.core.serializers import serialize
    
    if data_type == 'posts':
        data = serialize('json', Post.objects.all())
    elif data_type == 'comments':
        data = serialize('json', Comment.objects.all())
    elif data_type == 'categories':
        data = serialize('json', Category.objects.all())
    elif data_type == 'tags':
        data = serialize('json', Tag.objects.all())
    elif data_type == 'all':
        # 전체 백업
        all_data = {
            'posts': json.loads(serialize('json', Post.objects.all())),
            'comments': json.loads(serialize('json', Comment.objects.all())),
            'categories': json.loads(serialize('json', Category.objects.all())),
            'tags': json.loads(serialize('json', Tag.objects.all())),
            'exported_at': timezone.now().isoformat(),
        }
        data = json.dumps(all_data, ensure_ascii=False, indent=2)
    else:
        return JsonResponse({'error': '잘못된 데이터 유형입니다.'}, status=400)
    
    response = HttpResponse(data, content_type='application/json')
    response['Content-Disposition'] = f'attachment; filename="blog_backup_{data_type}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.json"'
    return response
