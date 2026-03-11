from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from decouple import config
from .forms import BlogPostCreateForm, BlogPostCommentForm
from .models import BlogPost, PostComment

def index_view(request):
    if request.user.is_anonymous:
        user = authenticate(request, username=config('BLOG_USER'), password=config('BLOG_PASS'))
        login(request, user)
    posts = (
        BlogPost.objects.select_related("author").order_by("-last_modified")
    )
    return render(request, "blog.html", {"blog_posts": posts})

@login_required
def create_post(request):
    if request.method == "POST":
        form = BlogPostCreateForm(request.POST, request.FILES)
        if form.is_valid():
            post: BlogPost = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect("index")
    else:
        form = BlogPostCreateForm()
    return render(
        request,
        "create_post.html",
        {"form": form, "title": "Створення нового допису"}
    )

def display_post(request, post_id):
    post = get_object_or_404(
        BlogPost.objects.select_related("author"),
        pk=post_id
    )
    comments = (
        PostComment.objects.select_related("author")
        .filter(post=post)
        .order_by("last_modified")
    )
    form = BlogPostCommentForm()
    return render(
        request,
        "read_post.html",
        {"post": post, "comments": comments, "form": form}
    )

@login_required
def comment_post(request, post_id):
    post = get_object_or_404(BlogPost, pk=post_id)
    comments = PostComment.objects.filter(post=post)
    if request.method == "POST":
        form = BlogPostCommentForm(request.POST)
        if form.is_valid():
            comment: PostComment = form.save(commit=False)
            comment.author = request.user
            comment.post = post
            comment.save()
            return redirect("display_post", post_id)
    else:
        form = BlogPostCommentForm()
    return render(
        request,
        "read_post.html",
        {"post": post, "comments": comments, "form": form}
    )
