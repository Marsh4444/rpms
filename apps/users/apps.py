from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'   #This is the default primary key field type for models in Django 3.2 and later.
    name = 'apps.users'      #This tells Django the app is now at apps.users instead of just users.

