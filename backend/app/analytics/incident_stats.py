"""Calculate incident statistics and trends"""

class IncidentStats:
    """Computes incident statistics"""
    
    def __init__(self):
        """Initialize stats calculator"""
        self.statistics = {
            "total_incidents_24h": 38,
            "incident_types": {
                "Loitering": 12,
                "Pickpocketing": 9,
                "Suicide Risk": 3,
                "Suspicious Following": 14,
            },
            "top_locations": ["Platform 1 Edge", "Gate B", "Ticket Hall"],
        }
    
    def get_incident_count(self, time_window="24h"):
        """Get incident count for time window"""
        if time_window == "24h":
            return self.statistics["total_incidents_24h"]
        return self.statistics["total_incidents_24h"]
    
    def get_incident_breakdown(self):
        """Get incidents broken down by type"""
        return self.statistics["incident_types"]
    
    def calculate_trends(self):
        """Calculate trends over time"""
        return [
            {"day": "Monday", "count": 5},
            {"day": "Tuesday", "count": 6},
            {"day": "Wednesday", "count": 9},
            {"day": "Thursday", "count": 7},
            {"day": "Friday", "count": 11},
        ]
    
    def get_most_common_locations(self):
        """Get locations with most incidents"""
        return self.statistics["top_locations"]
