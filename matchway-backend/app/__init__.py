import os


def _load_env_file():
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(os.path.dirname(here), ".env")
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                name, value = line.split("=", 1)
                name = name.strip()
                value = value.strip().strip('"').strip("'")
                if name and name not in os.environ:
                    os.environ[name] = value
    except OSError:
        pass


_load_env_file()