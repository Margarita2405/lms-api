from rest_framework import serializers

from users.models import CustomUser, Payment


class PaymentBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ["id", "payment_date", "amount", "payment_method", "course", "lesson"]


class UserProfileSerializer(serializers.ModelSerializer):
    payments = PaymentBriefSerializer(many=True, read_only=True)

    class Meta:
        model = CustomUser
        fields = ["id", "email", "first_name", "last_name", "phone", "city", "avatar", "payments"]
        read_only_fields = ["email"]  # чтобы email нельзя было изменить через профиль


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = "__all__"


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={"input_type": "password"})

    class Meta:
        model = CustomUser
        fields = ["email", "password", "first_name", "last_name", "phone", "city", "avatar"]

    def create(self, validated_data):
        # создаём пользователя с хешированием пароля
        user = CustomUser.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            phone=validated_data.get("phone"),
            city=validated_data.get("city"),
            avatar=validated_data.get("avatar"),
        )
        return user


class UserPublicProfileSerializer(serializers.ModelSerializer):
    # Без поля last_name, без payments
    class Meta:
        model = CustomUser
        fields = ["id", "email", "first_name", "phone", "city", "avatar"]
        read_only_fields = ["email"]
