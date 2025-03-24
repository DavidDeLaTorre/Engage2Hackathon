class RunwayFAP:
    def __init__(self, latitude_dms, longitude_dms, altitude, height):
        self.latitude = self.dms_to_decimal(latitude_dms)
        self.longitude = self.dms_to_decimal(longitude_dms)
        self.altitude = altitude
        self.height = height

    def dms_to_decimal(self, dms_str):
        direction = dms_str[-1]
        dms = dms_str[:-1]
        if len(dms) == 6:
            deg = int(dms[:2])
            min_ = int(dms[2:4])
            sec = int(dms[4:])
        else:  # longitude with 7 digits
            deg = int(dms[:3])
            min_ = int(dms[3:5])
            sec = int(dms[5:])

        decimal = deg + min_ / 60 + sec / 3600
        if direction in ('S', 'W'):
            decimal *= -1
        return decimal

    def __repr__(self):
        return (f"RunwayFAP(lat={self.latitude:.6f}, long={self.longitude:.6f}, "
                f"alt={self.altitude}, height={self.height})")

# Dictionary of runway FAPs
FAP_position = {
    "18R": RunwayFAP("404619N", "0033434W", 7000, 5009),
    "18L": RunwayFAP("404226N", "0033337W", 5500, 3578),
    "32L": RunwayFAP("402252N", "0032815W", 4000, 2067),
    "32R": RunwayFAP("402100N", "0032440W", 5000, 3114)
}
