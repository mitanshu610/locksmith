from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import loaded_config


class ConnectionHandler:

    def __init__(self, connection_manager=None, event_bridge=None):
        self._session: Optional[AsyncSession] = None
        self._connection_manager = connection_manager

    @property
    def session(self):
        if not self._session:
            session_factory = self._connection_manager.get_session_factory()
            self._session = session_factory()
        return self._session

    async def session_commit(self):
        await self.session.commit()

    async def close(self):
        if self._session:
            await self._session.close()


async def get_connection_handler_for_app():
    connection_handler = ConnectionHandler(
        connection_manager=loaded_config.connection_manager
    )
    try:
        yield connection_handler
    finally:
        await connection_handler.close()


