from django.apps import AppConfig


class AnswersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.answers'
    verbose_name = '答案管理'
    
    def ready(self):
        import apps.answers.signals