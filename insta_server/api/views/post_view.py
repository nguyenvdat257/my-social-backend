from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import api_view
from ..models import Profile, Post, Follow
from django.contrib.auth.models import User
from ..serializers import ProfileSerializer
from django.db.models import Q

@api_view(['GET'])
def getPost(request, code):
    post = get_object_or_404(Post, code=code)