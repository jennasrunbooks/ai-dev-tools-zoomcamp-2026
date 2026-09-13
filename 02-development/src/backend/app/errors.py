class ApiException(Exception):
    """Raised for expected API error conditions (404, 409, ...).

    Carries a machine-readable `code` and human-readable `message`, matching
    the frontend's `ApiError` type / `ApiRequestError` class — the error
    response body is `{"code": ..., "message": ...}`, not FastAPI's default
    `{"detail": ...}` shape (docs/spec.md 5.4).
    """

    def __init__(self, status_code: int, code: str, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class NotFoundError(ApiException):
    def __init__(self, entry_id: str):
        super().__init__(404, "not_found", f'No waitlist entry with id "{entry_id}".')


class InvalidTransitionError(ApiException):
    def __init__(self, from_status: str, to_status: str, party_name: str):
        super().__init__(
            409,
            "invalid_transition",
            f'Cannot move "{party_name}" from "{from_status}" to "{to_status}".',
        )
