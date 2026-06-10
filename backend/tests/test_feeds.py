"""Feed route helpers."""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.api.routes.feeds import derive_platform_from_feed_id


def test_derive_platform_from_standard_feed_id():
    assert derive_platform_from_feed_id("CCTV_P1_04") == "Platform 1"
    assert derive_platform_from_feed_id("CCTV_PLATFORM12_04") == "Platform 12"


def test_derive_platform_from_single_number_feed_id():
    assert derive_platform_from_feed_id("CCTV-1") == "Platform 1"
    assert derive_platform_from_feed_id("CAM_01") == "Platform 1"


def test_derive_platform_falls_back_for_ambiguous_feed_id():
    assert derive_platform_from_feed_id("CAM_01_ZONE_02") == "Unknown Platform"
    assert derive_platform_from_feed_id("LOBBY") == "Unknown Platform"
