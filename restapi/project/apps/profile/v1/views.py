from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics

from .serializers import (RegisterSerializer, LoginSerializer, ProfileSerializer, ChangePasswordSerializer)
from .models import User, Token


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        account = serializer.save()
        account.is_active = True
        account.save()

        token = Token.objects.create(user=account).key

        data = dict()
        data["token"] = token

        return Response(data, status=status.HTTP_200_OK)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data.get('username')
        password = serializer.validated_data.get('password')

        try:
            account = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({"message": "Incorrect Login credentials"}, status=status.HTTP_403_FORBIDDEN)

        if not account.check_password(password):
            return Response({"message": "Incorrect Login credentials"}, status=status.HTTP_403_FORBIDDEN)

        if account.is_active:
            token = Token.objects.create(user=account).key

            data = dict()
            data["token"] = token

            return Response(data)
        else:
            return Response('Account is not active', status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        request.user.auth_tokens.get(key=request.auth.key).delete()

        return Response(status=status.HTTP_200_OK)


class ProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()
    serializer_class = ProfileSerializer

    def get_object(self):
        queryset = self.get_queryset()
        obj = generics.get_object_or_404(queryset, id=self.request.user.id)
        return obj


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if user.check_password(serializer.validated_data.get('old_pass')):
            Token.objects.filter(user=user).delete()

            user.set_password(serializer.validated_data.get('new_pass'))
            user.save()

            token = Token.objects.create(user=user).key

            data = dict()
            data["token"] = token

            return Response(data, status=status.HTTP_200_OK)
        else:
            return Response({"message": "Your old password is incorrect"}, status=status.HTTP_400_BAD_REQUEST)