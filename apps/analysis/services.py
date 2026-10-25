"""Price analysis - plain Python functions, easy to test.

Input is always a list of prices (oldest first).
"""
import statistics


def moving_average(values, window):
    """Average of the last `window` prices at each point (None until enough data)."""
    result = []
    for i in range(len(values)):
        if i + 1 < window:
            result.append(None)
        else:
            result.append(round(sum(values[i + 1 - window:i + 1]) / window, 4))
    return result


def percent_change(old, new):
    if not old:
        return None
    return round((new - old) / old * 100, 2)


def volatility(values):
    """Standard deviation of the percent changes between consecutive prices."""
    returns = [(b - a) / a * 100 for a, b in zip(values, values[1:]) if a]
    if len(returns) < 2:
        return None
    return round(statistics.stdev(returns), 2)


def detect_trend(values, short=7, long=21, threshold=1.0):
    """'up' / 'down' / 'flat' by comparing the short and long average prices."""
    if len(values) < 2:
        return "flat"
    short_avg = statistics.mean(values[-short:])
    long_avg = statistics.mean(values[-long:])
    diff = percent_change(long_avg, short_avg)
    if diff is None or abs(diff) < threshold:
        return "flat"
    return "up" if diff > 0 else "down"


def summarize(values):
    """Key numbers for one price series."""
    if not values:
        return None
    return {
        "latest": values[-1],
        "min": min(values),
        "max": max(values),
        "average": round(statistics.mean(values), 2),
        "change_percent": percent_change(values[0], values[-1]),
        "volatility": volatility(values),
        "trend": detect_trend(values),
        "points": len(values),
    }
