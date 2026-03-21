from django.urls import path, include

urlpatterns = [
    path('auth/', include('apps.authentication.urls')),
    path('questions/', include('apps.questions.urls')),
    path('answers/', include('apps.answers.urls')),
    path('categories/', include('apps.categories.urls')),
    path('search/', include('apps.search.urls')),
    path('system/', include('apps.system.urls')),
]