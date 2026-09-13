from rest_framework import permissions


class IsModerator(permissions.BasePermission):
    """Разрешение только для пользователей, входящих в группу 'moderators'."""

    def has_permission(self, request, view):
        return (
            request.user and request.user.is_authenticated and request.user.groups.filter(name="moderators").exists()
        )


class IsOwner(permissions.BasePermission):
    """Разрешение только владельцу объекта (поле 'owner')."""

    def has_object_permission(self, request, view, obj):
        # Объект должен иметь атрибут 'owner' и он должен совпадать с текущим пользователем
        return obj.owner == request.user


class IsOwnerProfile(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj == request.user


class IsNotModerator(permissions.BasePermission):
    """Разрешение для пользователей, которые НЕ являются модераторами."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and not request.user.groups.filter(name="moderators").exists()
        )
