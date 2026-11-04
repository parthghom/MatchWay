import pytest
from app.storage import profile_repo

class FakeQuery:
    def __init__(self, table, shared_log):
        self.table = table
        self.shared_log = shared_log
        self.method = None
        self.args = None

    def _record(self, method, *args, **kwargs):
        self.method = method
        self.args = (args, kwargs)
        self.shared_log.append((self.table, method, args, kwargs))
        return self

    def select(self, *args): return self._record("select", *args)
    def eq(self, *args): return self._record("eq", *args)
    def neq(self, *args): return self._record("neq", *args)
    def limit(self, *args): return self._record("limit", *args)
    def update(self, *args): return self._record("update", *args)
    def insert(self, *args): return self._record("insert", *args)
    def upsert(self, *args, **kwargs): return self._record("upsert", *args, **kwargs)
    def execute(self):
        class Result:
            def __init__(self): self.data = []
        return Result()

class FakeClient:
    def __init__(self, shared_log):
        self.shared_log = shared_log
        self.storage = self

    def table(self, name):
        return FakeQuery(name, self.shared_log)

    def from_(self, bucket):
        class StorageBucket:
            def __init__(self, shared_log): self.shared_log = shared_log
            def upload(self, path, content, options):
                self.shared_log.append(("storage", "upload", (path, content, options), {}))
        return StorageBucket(self.shared_log)

def test_get_profile_repository_memory(monkeypatch):
    monkeypatch.setenv("MATCHWAY_STORAGE", "memory")
    repo = profile_repo.get_profile_repository()
    assert isinstance(repo, profile_repo.MemoryProfileRepository)

def test_get_profile_repository_supabase(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://fake.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "fake-key")
    monkeypatch.delenv("MATCHWAY_STORAGE", raising=False)

    shared_log = []
    monkeypatch.setattr(profile_repo, "create_client", lambda url, key: FakeClient(shared_log))

    repo = profile_repo.get_profile_repository()
    assert isinstance(repo, profile_repo.SupabaseProfileRepository)

    # Test get_profile recording
    repo.get_profile("u1")
    found_eq = any(item[1] == "eq" and item[0] == "profiles" and item[2] == ("user_id", "u1") for item in shared_log)
    assert found_eq, f"Expected eq call on profiles, got {shared_log}"

    # Test upsert_vehicle recording
    repo.upsert_vehicle("u1", "car", "ABC-123")
    found_upsert = any(item[1] == "upsert" and item[0] == "vehicles" and item[3].get("on_conflict") == "user_id" for item in shared_log)
    assert found_upsert, f"Expected upsert with on_conflict='user_id', got {shared_log}"
