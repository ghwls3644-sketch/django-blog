from django.apps import AppConfig


class BlogConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'blog'
    verbose_name = '블로그'
    
    def ready(self):
        import blog.signals  # noqa: F401
