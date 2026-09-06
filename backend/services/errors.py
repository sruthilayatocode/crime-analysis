"""
API error types shared by the service layer.

Routes and the Flask app translate these into
consistent JSON error responses.
"""


class ApiError(Exception):
    """Base class for expected API errors."""

    status_code = 500

    def __init__(
        self,
        message,
        status_code=None,
        details=None
    ):
        super().__init__(message)

        self.message = message

        if status_code is not None:
            self.status_code = status_code

        self.details = details

    def to_dict(self):

        payload = {
            "success": False,
            "message": self.message
        }

        if self.details:
            payload["details"] = self.details

        return payload


class ValidationError(ApiError):
    """Invalid client input (HTTP 400)."""

    status_code = 400


class NotFoundError(ApiError):
    """Requested resource does not exist (HTTP 404)."""

    status_code = 404


class StorageError(ApiError):
    """Database/storage failure (HTTP 500)."""

    status_code = 500