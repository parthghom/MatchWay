import os
from app.storage.profile_repo import get_setting, MemoryProfileRepository
from app.storage.memory_repo import MemoryRepository

def get_repository(repo=None):
    if repo is not None:
        return repo

    url = get_setting("SUPABASE_URL")
    key = get_setting("SUPABASE_KEY")
    storage_mode = get_setting("MATCHWAY_STORAGE")

    if url and key and storage_mode != "memory":
        from app.storage.supabase_repo import SupabaseRepository
        return SupabaseRepository()
    return MemoryRepository()
