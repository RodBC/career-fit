"""Errors for LinkedIn browser job map (Camoufox)."""


class BrowserJobError(Exception):
    """Driver/session failure — surface as 400/503, never invent a JD."""

    def __init__(self, message: str, *, status: int = 503) -> None:
        super().__init__(message)
        self.status = status


# Back-compat alias used by older call sites / linkedin_selenium shim
SeleniumJobError = BrowserJobError
