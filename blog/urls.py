from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # 게시글
    path('', views.post_list, name='post_list'),
    path('post/<int:pk>/', views.post_detail, name='post_detail'),
    path('post/new/', views.post_create, name='post_create'),
    path('post/<int:pk>/edit/', views.post_update, name='post_update'),
    path('post/<int:pk>/delete/', views.post_delete, name='post_delete'),
    
    # 댓글
    path('post/<int:pk>/comment/', views.comment_create, name='comment_create'),
    path('post/<int:pk>/comment/<int:comment_pk>/delete/', views.comment_delete, name='comment_delete'),
    path('post/<int:pk>/comment/<int:comment_pk>/report/', views.comment_report, name='comment_report'),
    path('post/<int:pk>/comment/<int:comment_pk>/hide/', views.comment_hide, name='comment_hide'),
    
    # 카테고리 & 태그
    path('category/<slug:slug>/', views.category_posts, name='category_posts'),
    path('tag/<slug:slug>/', views.tag_posts, name='tag_posts'),
    
    # 내 게시글
    path('my-posts/', views.my_posts, name='my_posts'),
    path('my-comments/', views.my_comments, name='my_comments'),
    
    # 이미지 업로드
    path('upload/image/', views.image_upload, name='image_upload'),
    
    # 프로필
    path('profile/<str:username>/', views.user_profile, name='user_profile'),
    path('profile/settings/edit/', views.profile_edit, name='profile_edit'),
    
    # 인증
    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # 비밀번호 재설정
    path('password_reset/', 
        auth_views.PasswordResetView.as_view(
            template_name='registration/password_reset.html',
            email_template_name='registration/password_reset_email.html',
            subject_template_name='registration/password_reset_subject.txt'
        ), 
        name='password_reset'),
    path('password_reset/done/', 
        auth_views.PasswordResetDoneView.as_view(
            template_name='registration/password_reset_done.html'
        ), 
        name='password_reset_done'),
    path('reset/<uidb64>/<token>/', 
        auth_views.PasswordResetConfirmView.as_view(
            template_name='registration/password_reset_confirm.html'
        ), 
        name='password_reset_confirm'),
    path('reset/done/', 
        auth_views.PasswordResetCompleteView.as_view(
            template_name='registration/password_reset_complete.html'
        ), 
        name='password_reset_complete'),
    
    # 백업 (관리자 전용)
    path('dashboard/backup/', views.backup_dashboard, name='backup_dashboard'),
    path('dashboard/backup/export/<str:data_type>/', views.export_data, name='export_data'),
]
