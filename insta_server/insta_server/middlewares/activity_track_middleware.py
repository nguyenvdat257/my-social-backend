from django.utils import timezone

class LastActivityTraceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.user:
            profile = request.user.profile
            profile.last_active = timezone.now()
            profile.save()
        return response