def unread_notifications(request):
    if request.user.is_authenticated:
        unread = request.user.notifications.filter(is_read=False)
        pending_actions = request.user.agent_actions.filter(status='pending').count()
        return {
            'unread_notifications_count': unread.count(),
            'recent_notifications': unread[:5],
            'pending_actions_count': pending_actions,
        }
    return {
        'unread_notifications_count': 0,
        'recent_notifications': [],
        'pending_actions_count': 0,
    }
