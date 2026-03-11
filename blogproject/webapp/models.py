from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class BlogPost(models.Model):
    title = models.CharField('Заголовок допису', max_length=56)
    text = models.TextField('Текст допису')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    last_modified = models.DateTimeField(auto_now_add=True)
    post_image = models.ImageField('Зображення допису', null=True, blank=True, upload_to='blog_images/')

class PostComment(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE)
    text = models.TextField(max_length=1024)
    last_modified = models.DateTimeField(auto_now_add=True)
