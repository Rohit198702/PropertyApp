from .models import RoleMenu, Menu

from .models import Menu, RoleMenu

def menu_data(request):
    if request.user.is_authenticated:
        user_groups = request.user.groups.all()

        role_menus = RoleMenu.objects.filter(
            group__in=user_groups
        ).select_related('menu')

        menu_ids = role_menus.values_list('menu_id', flat=True)

        parents = Menu.objects.filter(
            id__in=menu_ids,
            parent__isnull=True
        )

        # attach children
        for parent in parents:
            parent.child_menus = Menu.objects.filter(
                id__in=menu_ids,
                parent=parent
            )

        return {
            'parents': parents
        }

    return {}

from .models import Notification

def notifications(request):
    if request.user.is_authenticated:
        unread_notifications = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).order_by("-created_at")[:5]

        unread_count = unread_notifications.count()

        return {
            "notifications": unread_notifications,
            "unread_count": unread_count,
        }

    return {}
