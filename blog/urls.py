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
    
    # 내 게시글
    path('my-posts/', views.my_posts, name='my_posts'),
    
    # 인증
    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]
