from django import forms
from .models import PostComment, BlogPost

class BlogPostCreateForm(forms.ModelForm):
    title = forms.CharField()
    text = forms.CharField(widget=forms.Textarea(attrs={"class": 'form-control', "rows": "10"}))
    post_image = forms.ImageField(initial=None, required=False)
    class Meta:
        model = BlogPost
        fields = ["title", "text", "post_image"]

class BlogPostCommentForm(forms.ModelForm):
    text = forms.CharField(widget=forms.Textarea(attrs={"class": 'form-control', "rows": "3"}))
    class Meta:
        model = PostComment
        fields = ["text"]