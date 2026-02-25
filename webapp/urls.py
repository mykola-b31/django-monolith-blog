from django.urls import path
from . import views
urlpatterns = [
    path("", views.index_view, name="index"),
    path("create", views.create_post, name="create"),
    path("post/<int:post_id>/", views.display_post, name="display_post"),
    path("post/<int:post_id>/comment/", views.comment_post, name="comment_post")
]