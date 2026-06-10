"""
DEPRECATED: This module should be removed.

The legacy ObjectTracker class has been removed and its export removed from cv/__init__.py.

Current architecture:
- VideoProcessor directly uses Ultralytics BYTETracker for object tracking
- BYTETracker is initialized with proper configuration arguments
- Track IDs are persistent and numeric

Why ObjectTracker was removed:
- It was an empty placeholder with no implementation
- VideoProcessor was already using BYTETracker directly
- No need for an unnecessary abstraction layer

References have been cleaned up from:
- cv/__init__.py (removed from exports)
- tests/test_cv.py (tests replaced with import tests)

This file can be safely deleted.
"""
