from fastapi import status

class DataSourceAccessError(Exception):
    """
    Base class for Plan-related errors.
    Provides a consistent interface to store a message, detail, and status code.
    """
    def __init__(
        self,
        message: str = "An error occurred in the Datasource Access Service",
        detail: str = None,
        status_code: int = status.HTTP_400_BAD_REQUEST
    ):
        self.message = message
        self.detail = detail or message
        self.status_code = status_code
        super().__init__(message)