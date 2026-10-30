class ApiException(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        headers: dict[str, str] | None = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.headers = headers


class NotFoundException(ApiException):
    def __init__(
        self, message: str = "요청한 리소스를 찾을 수 없습니다.", *, code: str = "NOT_FOUND"
    ):
        super().__init__(status_code=404, code=code, message=message)


class UnauthorizedException(ApiException):
    def __init__(self, message: str = "인증이 필요합니다.", *, code: str = "UNAUTHORIZED"):
        super().__init__(
            status_code=401,
            code=code,
            message=message,
            headers={"WWW-Authenticate": "Bearer"},
        )


class ForbiddenException(ApiException):
    def __init__(self, message: str = "접근 권한이 없습니다.", *, code: str = "FORBIDDEN"):
        super().__init__(status_code=403, code=code, message=message)


class ConflictException(ApiException):
    def __init__(
        self, message: str = "요청이 현재 상태와 충돌합니다.", *, code: str = "CONFLICT"
    ):
        super().__init__(status_code=409, code=code, message=message)
