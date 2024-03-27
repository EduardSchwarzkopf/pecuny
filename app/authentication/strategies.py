from typing import List, Literal, Optional

from fastapi import Response, status
from fastapi.security import APIKeyCookie
from fastapi_users import models
from fastapi_users.authentication import AuthenticationBackend, JWTStrategy, Transport
from fastapi_users.jwt import SecretType, generate_jwt
from fastapi_users.openapi import OpenAPIResponseType

from app.config import settings
from app.models import User


class TokensCookieTransport(Transport):
    scheme: APIKeyCookie

    def __init__(  # pylint: disable=too-many-arguments
        self,
        cookie_name: str = "access_token",
        cookie_refresh_name: str = "refresh_token",
        cookie_max_age: Optional[int] = None,
        cookie_refresh_max_age: Optional[int] = None,
        cookie_path: str = "/",
        cookie_domain: Optional[str] = None,
        cookie_secure: bool = True,
        cookie_httponly: bool = True,
        cookie_samesite: Literal["lax", "strict", "none"] = "lax",
    ):
        self.cookie_name = cookie_name
        self.cookie_max_age = cookie_max_age
        self.cookie_path = cookie_path
        self.cookie_domain = cookie_domain
        self.cookie_secure = cookie_secure
        self.cookie_httponly = cookie_httponly
        self.cookie_samesite = cookie_samesite
        self.scheme = APIKeyCookie(name=self.cookie_name, auto_error=False)

        self.refresh_cookie_name = cookie_refresh_name
        self.cookie_refresh_max_age = cookie_refresh_max_age

    async def get_login_response(
        self, access_token: str, refresh_token: str
    ) -> Response:
        response = Response(status_code=status.HTTP_204_NO_CONTENT)
        return self._set_login_cookie(response, access_token, refresh_token)

    async def get_logout_response(self) -> Response:
        response = Response(status_code=status.HTTP_204_NO_CONTENT)
        return self._set_logout_cookie(response)

    def _set_login_cookie(
        self, response: Response, access_token: str, refresh_token: str
    ) -> Response:

        for name, token, max_age in [
            (self.cookie_name, access_token, self.cookie_max_age),
            (self.refresh_cookie_name, refresh_token, self.cookie_refresh_max_age),
        ]:
            response.set_cookie(
                name,
                token,
                max_age=max_age,
                path=self.cookie_path,
                domain=self.cookie_domain,
                secure=self.cookie_secure,
                httponly=self.cookie_httponly,
                samesite=self.cookie_samesite,
            )

        return response

    def _set_logout_cookie(self, response: Response) -> Response:

        for cookie_name in [self.cookie_name, self.refresh_cookie_name]:
            response.set_cookie(
                cookie_name,
                "",
                max_age=0,
                path=self.cookie_path,
                domain=self.cookie_domain,
                secure=self.cookie_secure,
                httponly=self.cookie_httponly,
                samesite=self.cookie_samesite,
            )

        return response

    @staticmethod
    def get_openapi_login_responses_success() -> OpenAPIResponseType:
        return {status.HTTP_204_NO_CONTENT: {"model": None}}

    @staticmethod
    def get_openapi_logout_responses_success() -> OpenAPIResponseType:
        return {status.HTTP_204_NO_CONTENT: {"model": None}}


class JWTAccessRefreshStrategy(JWTStrategy[models.UP, models.ID]):
    def __init__(  # pylint: disable=too-many-arguments
        self,
        access_token_secret: SecretType,
        refresh_token_secret: SecretType,
        lifetime_seconds: Optional[int],
        refresh_lifetime_seconds: Optional[int],
        token_audience: Optional[List[str]] = None,
        algorithm: str = "HS256",
        public_key: Optional[SecretType] = None,
    ):
        if token_audience is None:
            token_audience = settings.token_audience

        super().__init__(
            secret=access_token_secret,
            lifetime_seconds=lifetime_seconds,
            token_audience=token_audience,
            algorithm=algorithm,
            public_key=public_key,
        )

        self.refresh_lifetime_seconds = refresh_lifetime_seconds
        self.refresh_token_secret = refresh_token_secret

    async def write_refresh_token(self, user: User) -> str:
        """
        Generates a JWT refresh token for the given user.

        Args:
            user: The user object for whom the token is generated.

        Returns:
            str: The generated JWT refresh token.

        Raises:
            Any errors raised by the JWT generation process.
        """

        data = {"sub": str(user.id), "aud": self.token_audience}
        return generate_jwt(
            data,
            self.refresh_token_secret,
            self.refresh_lifetime_seconds,
            algorithm=self.algorithm,
        )

    async def write_token(self, user: models.UP) -> str:
        """
        Generates a JWT token for the given user.

        Args:
            user: The user object for whom the token is generated.

        Returns:
            str: The generated JWT token.

        Raises:
            Any errors raised by the JWT generation process.
        """

        data = {"sub": str(user.id), "aud": self.token_audience}
        return generate_jwt(
            data, self.encode_key, self.lifetime_seconds, algorithm=self.algorithm
        )


class JWTAuthBackend(AuthenticationBackend):
    transport: TokensCookieTransport

    async def login(self, strategy: JWTAccessRefreshStrategy, user: User) -> Response:
        """
        Logs in a user by generating access and refresh tokens using the provided JWT strategy.

        Args:
            strategy: The custom JWT strategy used for token generation.
            user: The user object logging in.

        Returns:
            Response: The HTTP response containing the tokens as cookies.
        """

        access_token = await strategy.write_token(user)
        refresh_token = await strategy.write_refresh_token(user)

        return await self.transport.get_login_response(access_token, refresh_token)
