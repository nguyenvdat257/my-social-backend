from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from ..models import *
from django.contrib.auth.models import User
from ..serializers import *
from django.db.models import Q
from rest_framework import status
from django.http import QueryDict
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework import pagination
from django.conf import settings