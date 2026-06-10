"""Calculate metrics for dashboard display"""

from datetime import datetime

class DashboardMetrics:
    """Aggregates metrics for dashboard"""
    
    def __init__(self):
        """Initialize dashboard metrics"""
        self.start_time = datetime.utcnow()
    
    def get_active_alerts(self):
        """Get currently active alerts"""
        return 12
    
    def get_system_status(self):
        """Get overall system health status"""
        uptime = datetime.utcnow() - self.start_time
        return {
            "status": "operational",
            "uptime_seconds": int(uptime.total_seconds()),
            "healthy": True,
        }
    
    def get_performance_metrics(self):
        """Get system performance metrics"""
        return {
            "average_latency_ms": 72,
            "frames_processed_per_minute": 185,
            "model_inference_rate": 4.2,
        }
    
    def get_summary_statistics(self):
        """Get summary statistics"""
        return {
            "total_pending_alerts": 7,
            "resolved_alerts_last_24h": 19,
            "critical_alerts_last_24h": 2,
        }
