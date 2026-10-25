"""
Root test runner proxy for test_zone_service
"""
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from backend.tests.test_zone_service import (
    TestZoneServiceUnit,
    TestZoneServiceKnownCoordinates,
    TestZoneApiEndpoint,
)

if __name__ == "__main__":
    import unittest
    unittest.main()
