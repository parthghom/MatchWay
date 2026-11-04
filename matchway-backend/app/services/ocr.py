import io

def extract_text(image_bytes):
    """
    Extracts text from image bytes using Tesseract OCR.
    """
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        raise RuntimeError("OCR is not installed")

    try:
        image = Image.open(io.BytesIO(image_bytes))
        return pytesseract.image_to_string(image)
    except Exception as e:
        if "tesseract is not installed" in str(e).lower():
            raise RuntimeError("OCR is not installed")
        raise e
