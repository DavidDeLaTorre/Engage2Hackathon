class RunwayThreshold:
    def __init__(self, latitude, longitude):
        self.latitude = latitude
        self.longitude = longitude

    def __repr__(self):
        return f"RunwayThreshold(lat={self.latitude:.6f}, long={self.longitude:.6f})"

threshold_position = {
    "18R": RunwayThreshold(40.530218500159428, -3.574838439918973),
    "32L": RunwayThreshold(40.45647777995444, -3.547191670444303),
    "32R": RunwayThreshold(40.470008330215407, -3.532580559771673),
    "18L": RunwayThreshold(40.532622220224376, -3.55938056019154)
}