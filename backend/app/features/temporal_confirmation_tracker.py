"""Track temporal confirmation of sustained high-risk classifications."""

import time


class TemporalConfirmationTracker:
    """Tracks how many consecutive seconds each track has been classified as high-risk."""

    def __init__(self, confirmation_seconds=15):
        self.confirmation_seconds = confirmation_seconds
        self.consecutive_seconds = {}
        self.last_update_time = {}

    def update(self, track_id, is_above_threshold, current_time):
        if track_id not in self.consecutive_seconds:
            self.consecutive_seconds[track_id] = 0
            self.last_update_time[track_id] = current_time

        if is_above_threshold:
            self.consecutive_seconds[track_id] += current_time - self.last_update_time[track_id]
        else:
            self.consecutive_seconds[track_id] = 0

        self.last_update_time[track_id] = current_time

    def is_confirmed(self, track_id):
        return self.consecutive_seconds.get(track_id, 0) >= self.confirmation_seconds

    def clear_track(self, track_id):
        self.consecutive_seconds.pop(track_id, None)
        self.last_update_time.pop(track_id, None)
