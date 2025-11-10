class UserProxy:
    def __init__(self, id, username, email):
        self.id = id
        self.username = username
        self.email = email

    @classmethod
    def from_api(cls, data):
        return cls(
            id=data["id"],
            username=data.get("username", ""),
            email=data.get("email", ""),
        )
