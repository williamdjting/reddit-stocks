"""Shared read-only Supabase client for the dashboard."""
import os
from functools import lru_cache

from supabase import create_client, Client


@lru_cache(maxsize=1)
def get_client() -> Client:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not url or not key:
        raise EnvironmentError(
            "Missing Supabase credentials. "
            "Set SUPABASE_URL and SUPABASE_SERVICE_KEY in Streamlit Cloud → Settings → Secrets."
        )
    return create_client(url, key)
