class TestAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            class FakeUser:
                id = 1
                is_authenticated = True

            request.user = FakeUser()

        response = self.get_response(request)
        return response
