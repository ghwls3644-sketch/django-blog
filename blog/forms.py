from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Post, Comment


class PostForm(forms.ModelForm):
    """게시글 작성/수정 폼"""
    class Meta:
        model = Post
        fields = ['title', 'category', 'tags', 'content', 'meta_description', 'status', 'published_at', 'is_public']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '제목을 입력하세요'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 15,
                'placeholder': '내용을 입력하세요'
            }),
            'meta_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'maxlength': 160,
                'placeholder': '검색 엔진에 표시될 설명을 입력하세요 (160자 이내)'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_status'
            }),
            'published_at': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local',
                'id': 'id_published_at'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'title': '제목',
            'category': '카테고리',
            'tags': '태그',
            'content': '내용',
            'meta_description': '메타 설명 (SEO)',
            'status': '상태',
            'published_at': '발행 예정일',
            'is_public': '공개'
        }


class CommentForm(forms.ModelForm):
    """댓글 작성 폼"""
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '댓글을 입력하세요'
            }),
        }
        labels = {
            'content': '댓글',
        }


class SignUpForm(UserCreationForm):
    """회원가입 폼"""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': '이메일 주소'
        })
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': '사용자명'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': '비밀번호'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': '비밀번호 확인'
        })
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class UserProfileForm(forms.ModelForm):
    """프로필 편집 폼"""
    class Meta:
        from .models import UserProfile
        model = UserProfile
        fields = ['bio', 'avatar', 'website', 'github', 'skills', 'location']
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': '자기소개를 입력하세요'
            }),
            'avatar': forms.FileInput(attrs={
                'class': 'form-control'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com'
            }),
            'github': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'GitHub 사용자명'
            }),
            'skills': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Python, Django, JavaScript'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '서울, 대한민국'
            }),
        }
        labels = {
            'bio': '자기소개',
            'avatar': '프로필 이미지',
            'website': '웹사이트',
            'github': 'GitHub',
            'skills': '기술 스택',
            'location': '위치',
        }
