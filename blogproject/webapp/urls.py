from django.urls import include, path
from rest_framework import routers
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.decorators import api_view
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenBlacklistView
from . import views, api_views
from .api_views import NotificationView

router = routers.DefaultRouter()
router.register('authors', api_views.UserViewSet, basename='authors')
router.register('posts', api_views.BlogPostViewSet, basename='posts')
router.register('comments', api_views.PostCommentViewSet, basename='comments')
urlpatterns = [
    path("", views.index_view, name="index"),
    path("create", views.create_post, name="create"),
    path("post/<int:post_id>/", views.display_post, name="display_post"),
    path("post/<int:post_id>/comment/", views.comment_post, name="comment_post"),
    path("silk/", include("silk.urls", namespace="silk")),
    path("api/", include(router.urls), name="api"),
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/token/blacklist/", TokenBlacklistView.as_view(), name="token_blacklist"),
    path('api/schema/', SpectacularAPIView.as_view(), name="schema"),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/authors/<int:pk>/subscribe/', NotificationView.as_view(), name='author-subscribe'),
    path("api/jwks/", api_views.JWKSView.as_view(), name="jwks")
]