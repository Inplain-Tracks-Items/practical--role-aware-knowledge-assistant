# Test double for OcrProvider: returns fixed text instantly instead of running EasyOCR.
# ICS layer: test
# Called by: tests that ingest the scanned PDF
# Step: added in step 2 (Ingest tagged chunks)


class FakeOcrProvider:
    """Counts its calls and returns the same text for every image."""

    def __init__(self, text: str = "Scanned incident report forklift reversing alarm banksman night loading") -> None:
        self.text = text
        self.calls = 0

    async def read_text(self, png_bytes: bytes) -> str:
        """Record the call and return the fixed text; png_bytes is only checked to be a PNG."""
        assert png_bytes[:4] == b"\x89PNG"
        self.calls += 1
        return self.text
