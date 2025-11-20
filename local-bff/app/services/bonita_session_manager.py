from __future__ import annotations

from typing import Dict

import httpx
from fastapi import HTTPException, status
from structlog import get_logger

from app.core.config import get_settings

logger = get_logger()
settings = get_settings()


class BonitaSession:
    """Representa una sesión autenticada de Bonita para un usuario específico."""

    def __init__(self, username: str, password: str) -> None:
        self.username = username
        self.password = password
        self.base_url = settings.bonita_base_url
        self._client: httpx.AsyncClient | None = None
        self._csrf_token: str | None = None
        self._authenticated = False

    async def authenticate(self) -> str:
        """
        Autentica al usuario en Bonita y devuelve el session ID.

        Returns:
            El X-Bonita-API-Token (session ID) de la sesión autenticada

        Raises:
            HTTPException: Si la autenticación falla
        """
        if self._client is None:
            self._client = httpx.AsyncClient(base_url=self.base_url, timeout=15.0)

        payload = {
            "username": self.username,
            "password": self.password,
            "redirect": "false",
        }

        try:
            response = await self._client.post("/bonita/loginservice", data=payload)

            if response.status_code != status.HTTP_204_NO_CONTENT:
                logger.warning(
                    "Bonita authentication failed",
                    username=self.username,
                    status_code=response.status_code,
                    body=response.text,
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid Bonita credentials",
                )

            self._csrf_token = self._client.cookies.get("X-Bonita-API-Token")
            if not self._csrf_token:
                logger.error("Bonita CSRF token not found in cookies", username=self.username)
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Bonita CSRF token not found",
                )

            self._authenticated = True
            logger.info("Bonita session established", username=self.username, session_id=self._csrf_token[:8] + "...")
            return self._csrf_token

        except httpx.RequestError as exc:
            logger.error("Bonita request error", username=self.username, error=str(exc))
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Unable to connect to Bonita",
            ) from exc

    @property
    def client(self) -> httpx.AsyncClient:
        """Devuelve el cliente HTTP autenticado."""
        if self._client is None:
            raise RuntimeError("Session not initialized. Call authenticate() first.")
        return self._client

    @property
    def auth_headers(self) -> Dict[str, str]:
        """Devuelve los headers de autenticación para las requests a Bonita."""
        headers: Dict[str, str] = {
            "Content-Type": "application/json",
        }
        if self._csrf_token:
            headers["X-Bonita-API-Token"] = self._csrf_token
        return headers

    @property
    def is_authenticated(self) -> bool:
        """Indica si la sesión está autenticada."""
        return self._authenticated

    @property
    def session_id(self) -> str | None:
        """Devuelve el session ID (CSRF token) de Bonita."""
        return self._csrf_token

    async def close(self) -> None:
        """Cierra el cliente HTTP y limpia la sesión."""
        if self._client:
            await self._client.aclose()
            self._client = None
        self._csrf_token = None
        self._authenticated = False
        logger.debug("Bonita session closed", username=self.username)


class BonitaSessionManager:
    """
    Gestor de sesiones de Bonita que mantiene sesiones persistentes por session_id.

    Las sesiones se almacenan en memoria y se reutilizan mientras sean válidas.
    """

    # Almacenamiento de sesiones activas por session_id
    _sessions: Dict[str, BonitaSession] = {}

    @classmethod
    async def create_session(cls, username: str, password: str) -> BonitaSession:
        """
        Crea y autentica una nueva sesión de Bonita.

        Args:
            username: Usuario de Bonita
            password: Contraseña de Bonita

        Returns:
            Una sesión autenticada de Bonita

        Raises:
            HTTPException: Si la autenticación falla
        """
        session = BonitaSession(username, password)
        await session.authenticate()

        # Almacenar la sesión por su session_id
        if session.session_id:
            cls._sessions[session.session_id] = session
            logger.info("Session stored in manager", session_id=session.session_id[:8] + "...", username=username)

        return session

    @classmethod
    async def get_session(cls, session_id: str) -> BonitaSession:
        """
        Obtiene una sesión existente por su session_id.

        Args:
            session_id: El X-Bonita-API-Token de la sesión

        Returns:
            La sesión de Bonita

        Raises:
            HTTPException: Si la sesión no existe o expiró
        """
        session = cls._sessions.get(session_id)

        if session is None:
            logger.warning("Session not found or expired", session_id=session_id[:8] + "...")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Bonita session expired or invalid. Please login again."
            )

        if not session.is_authenticated:
            logger.warning("Session exists but not authenticated", session_id=session_id[:8] + "...")
            # Limpiar la sesión inválida
            cls._sessions.pop(session_id, None)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Bonita session expired. Please login again."
            )

        return session

    @classmethod
    async def remove_session(cls, session_id: str) -> None:
        """
        Remueve y cierra una sesión del manager.

        Args:
            session_id: El X-Bonita-API-Token de la sesión a remover
        """
        session = cls._sessions.pop(session_id, None)
        if session:
            await session.close()
            logger.info("Session removed from manager", session_id=session_id[:8] + "...")

    @classmethod
    def get_active_sessions_count(cls) -> int:
        """Retorna el número de sesiones activas."""
        return len(cls._sessions)
