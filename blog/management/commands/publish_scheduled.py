"""
예약발행된 게시글을 자동으로 발행하는 management command

사용법:
    python manage.py publish_scheduled

권장 실행 방법:
    - Windows Task Scheduler로 5분마다 실행
    - 또는 Celery Beat 사용
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from blog.models import Post


class Command(BaseCommand):
    help = '예약발행 시간이 된 게시글을 자동으로 발행합니다.'

    def handle(self, *args, **options):
        now = timezone.now()
        
        # 예약발행 시간이 지난 글 조회
        scheduled_posts = Post.objects.filter(
            status='scheduled',
            published_at__lte=now
        )
        
        count = scheduled_posts.count()
        
        if count == 0:
            self.stdout.write(
                self.style.SUCCESS('발행 대기 중인 게시글이 없습니다.')
            )
            return
        
        # 상태를 published로 변경
        for post in scheduled_posts:
            post.status = 'published'
            post.save(update_fields=['status'])
            self.stdout.write(
                self.style.SUCCESS(f'발행됨: "{post.title}" (예약: {post.published_at})')
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n총 {count}개의 게시글이 발행되었습니다.')
        )
