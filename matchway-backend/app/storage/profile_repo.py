import os
from supabase import create_client

def get_setting(name):
    val = os.environ.get(name)
    if val is not None:
        return val

    try:
        with open(".env", "r") as f:
            for line in f:
                if line.startswith(f"{name}="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    except Exception:
        pass
    return None

class MemoryProfileRepository:
    def __init__(self):
        self.profiles = {}
        self.documents = {} # user_id -> list of {doc_type, status, doc_number, image_bytes}
        self.vehicles = {}   # user_id -> {vehicle_type, plate_number}

    def upsert_profile(self, user_id, fields):
        if user_id not in self.profiles:
            self.profiles[user_id] = {}
        self.profiles[user_id].update(fields)
        return self.profiles[user_id]

    def get_profile(self, user_id):
        return self.profiles.get(user_id)

    def list_documents(self, user_id):
        docs = self.documents.get(user_id, [])
        # Return list of {doc_type, status, doc_number} as requested
        return [{"doc_type": d["doc_type"], "status": d["status"], "doc_number": d.get("doc_number")} for d in docs]

    def save_document(self, user_id, doc_type, image_bytes, doc_number, status):
        if user_id not in self.documents:
            self.documents[user_id] = []

        docs = self.documents[user_id]
        for i, doc in enumerate(docs):
            if doc["doc_type"] == doc_type:
                docs[i].update({
                    "image_bytes": image_bytes,
                    "doc_number": doc_number,
                    "status": status
                })
                return docs[i]

        new_doc = {
            "doc_type": doc_type,
            "status": status,
            "doc_number": doc_number,
            "image_bytes": image_bytes
        }
        docs.append(new_doc)
        return new_doc

    def get_vehicle(self, user_id):
        return self.vehicles.get(user_id)

    def upsert_vehicle(self, user_id, vehicle_type, plate_number):
        self.vehicles[user_id] = {
            "vehicle_type": vehicle_type,
            "plate_number": plate_number
        }
        return self.vehicles[user_id]

    def plate_taken(self, plate_number, user_id):
        for uid, vehicle in self.vehicles.items():
            if uid != user_id and vehicle["plate_number"] == plate_number:
                return True
        return False

class SupabaseProfileRepository:
    def __init__(self):
        self.client = create_client(
            get_setting("SUPABASE_URL"),
            get_setting("SUPABASE_SERVICE_KEY")
        )

    def upsert_profile(self, user_id, fields):
        existing = self.get_profile(user_id)
        if existing:
            self.client.table("profiles").update(fields).eq("user_id", user_id).execute()
        else:
            self.client.table("profiles").insert({"user_id": user_id, **fields}).execute()

    def get_profile(self, user_id):
        res = self.client.table("profiles").select("*").eq("user_id", user_id).limit(1).execute()
        if not res.data:
            return None
        profile = res.data[0]
        if "date_of_birth" in profile and profile["date_of_birth"]:
            profile["date_of_birth"] = str(profile["date_of_birth"])
        return profile

    def list_documents(self, user_id):
        res = self.client.table("documents").select("doc_type,status,doc_number").eq("user_id", user_id).execute()
        return res.data

    def save_document(self, user_id, doc_type, image_bytes, doc_number, status):
        content_type = "image/png" if image_bytes.startswith(b"\x89PNG") else "image/jpeg"
        path = f"{user_id}/{doc_type}.jpg"
        self.client.storage.from_("documents").upload(
            path,
            image_bytes,
            {"content-type": content_type, "upsert": "true"}
        )
        self.client.table("documents").upsert(
            {
                "user_id": user_id,
                "doc_type": doc_type,
                "storage_path": path,
                "doc_number": doc_number,
                "status": status
            },
            on_conflict="user_id,doc_type"
        ).execute()

    def get_vehicle(self, user_id):
        res = self.client.table("vehicles").select("*").eq("user_id", user_id).limit(1).execute()
        return res.data[0] if res.data else None

    def upsert_vehicle(self, user_id, vehicle_type, plate_number):
        self.client.table("vehicles").upsert(
            {"user_id": user_id, "vehicle_type": vehicle_type, "plate_number": plate_number},
            on_conflict="user_id"
        ).execute()

    def plate_taken(self, plate_number, user_id):
        res = self.client.table("vehicles").select("user_id").eq("plate_number", plate_number).neq("user_id", user_id).execute()
        return len(res.data) > 0

def get_profile_repository():
    url = get_setting("SUPABASE_URL")
    key = get_setting("SUPABASE_SERVICE_KEY")
    storage_mode = get_setting("MATCHWAY_STORAGE")

    if url and key and storage_mode != "memory":
        return SupabaseProfileRepository()
    return MemoryProfileRepository()
