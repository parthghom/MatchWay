import tempfile
import os

def faces_match(id_image_bytes, selfie_bytes):
    """
    Verifies if two images match using DeepFace.
    """
    try:
        from deepface import DeepFace
    except ImportError:
        raise RuntimeError("Face check is not installed")

    tmp1 = None
    tmp2 = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as f1:
            f1.write(id_image_bytes)
            tmp1 = f1.name
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as f2:
            f2.write(selfie_bytes)
            tmp2 = f2.name

        result = DeepFace.verify(img1_path=tmp1, img2_path=tmp2)
        return bool(result["verified"])
    finally:
        if tmp1 and os.path.exists(tmp1):
            os.remove(tmp1)
        if tmp2 and os.path.exists(tmp2):
            os.remove(tmp2)
