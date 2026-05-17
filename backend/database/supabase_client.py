from supabase import create_client, Client
from config import get_settings

settings = get_settings()


def get_supabase_client() -> Client | None:
    """Get Supabase client with anon key (for client-side)"""
    if not settings.supabase_url or not settings.supabase_anon_key:
        return None
    return create_client(settings.supabase_url, settings.supabase_anon_key)


def get_supabase_admin() -> Client | None:
    """Get Supabase client with service role (for server-side operations)"""
    if not settings.supabase_url or not settings.supabase_service_key:
        return None
    return create_client(settings.supabase_url, settings.supabase_service_key)


class DatabaseClient:
    """Wrapper for Supabase database operations.

    API routes use db.client directly for queries. This class provides
    the client and admin instances with lazy initialization.
    """

    def __init__(self):
        self._client = None
        self._admin = None

    @property
    def client(self) -> Client | None:
        """Backend client uses service role key to bypass RLS."""
        if self._client is None:
            self._client = get_supabase_admin()
        return self._client

    @property
    def admin(self) -> Client | None:
        if self._admin is None:
            self._admin = get_supabase_admin()
        return self._admin

    def upsert_opportunity(self, data: dict):
        """Upsert an opportunity by URL (unique constraint)."""
        return self.client.table("opportunities").upsert(data, on_conflict="url").execute()


db = DatabaseClient()
