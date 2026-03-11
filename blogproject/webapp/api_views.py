from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions, viewsets
from rest_framework.decorators import permission_classes
from rest_framework.views import APIView
from rest_framework.authentication import BasicAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.views import TokenObtainPairView

from silk.profiling.profiler import silk_profile
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from django.contrib.auth import get_user_model

from .events import NotificationProducer
from .models import BlogPost, PostComment
from .serializers import BlogPostSerializer, PostCommentSerializer, UserSerializer

User = get_user_model()

class IsAuthorOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user

class LoginView(TokenObtainPairView):
    authentication_classes = [BasicAuthentication]

class UserViewSet(viewsets.ModelViewSet):
    authentication_classes = [JWTAuthentication]
    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

class BlogPostViewSet(viewsets.ModelViewSet):
    authentication_classes = [JWTAuthentication]
    serializer_class = BlogPostSerializer
    queryset = BlogPost.objects.select_related('author').prefetch_related('postcomment_set').all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]

    @method_decorator(cache_page(60, key_prefix="post_list"))
    @silk_profile(name="blog_post_list")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

class PostCommentViewSet(viewsets.ModelViewSet):
    authentication_classes = [JWTAuthentication]
    queryset = PostComment.objects.all()
    serializer_class = PostCommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]

class NotificationView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, pk):
        user_email = request.data.get("email")

        if not user_email:
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

        notification = NotificationProducer()
        notification.send_event("SubscribeNotifications", request.user, pk, user_email)
        return Response(status=status.HTTP_200_OK)

    def delete(self, request, pk):
        notification = NotificationProducer()
        notification.send_event("UnsubscribeNotifications", request.user, pk)
        return Response(status=status.HTTP_200_OK)

