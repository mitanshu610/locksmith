from fastapi import status


class TeamError(Exception):
    """
    Base class for Plan-related errors.
    Provides a consistent interface to store a message, detail, and status code.
    """
    def __init__(
        self,
        message: str = "An error occurred in the Teams Service",
        detail: str = None,
        status_code: int = status.HTTP_400_BAD_REQUEST
    ):
        self.message = message
        self.detail = detail or message
        self.status_code = status_code
        super().__init__(message)


class TeamNotFoundError(TeamError):
    """
    Base class for Plan-related errors.
    Provides a consistent interface to store a message, detail, and status code.
    """
    def __init__(
        self,
        message: str = "An error occurred in the Teams Service",
        detail: str = None,
        status_code: int = status.HTTP_404_NOT_FOUND
    ):
        self.message = message
        self.detail = detail or message
        self.status_code = status_code
        super().__init__(message)