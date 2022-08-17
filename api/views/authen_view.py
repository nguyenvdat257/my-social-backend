from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from .my_imports import *


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['username'] = user.username
        # ...

        return token


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


@api_view(['POST'])
def user_signup(request):
    serializer = UserSerializer(data=request.data)
    is_valid, error_fields = serializer.is_valid()
    if is_valid:
        user = serializer.save()
        refresh_token = MyTokenObtainPairSerializer().get_token(user)
        access_token = refresh_token.access_token
        return Response(
            {'refresh': str(refresh_token),
             'access': str(access_token)}
            )
    else:
        return Response(error_fields, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def validate_user_signup(request):
    serializer = UserSerializer(data=request.data)
    is_valid, error_fields = serializer.is_valid()
    if is_valid:
        return Response('Valid form data')
    else:
        return Response(error_fields, status=status.HTTP_400_BAD_REQUEST)
