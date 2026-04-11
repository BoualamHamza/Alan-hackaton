from datetime import date, timedelta

import httpx
from fastapi import HTTPException

from wearable.config import DEMO_END_USER_ID, THRYVE_BASE_URL, THRYVE_HEADERS, VALUE_TYPES


async def fetch_daily_data(days: int = 30) -> list[dict]:
    end_day = date.today()
    start_day = end_day - timedelta(days=days - 1)

    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            resp = await client.post(
                f"{THRYVE_BASE_URL}/v5/dailyDynamicValues",
                headers=THRYVE_HEADERS,
                data={
                    "authenticationToken": DEMO_END_USER_ID,
                    "startDay": start_day.isoformat(),
                    "endDay": end_day.isoformat(),
                    "valueTypes": VALUE_TYPES,
                    "displayTypeName": "true",
                    "detailed": "true",
                },
            )
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail=f"Thryve unreachable: {exc}")

    if not resp.is_success:
        raise HTTPException(status_code=502, detail=f"Thryve error {resp.status_code}: {resp.text}")

    sources = resp.json()[0].get("dataSources", [])
    if not sources:
        return []
    return sources[0]["data"]


def parse_value(item: dict):
    val = item["value"]
    if item["valueType"] == "LONG":
        return int(val)
    if item["valueType"] == "DOUBLE":
        return float(val)
    return val


def build_dashboard(raw: list[dict]) -> dict:
    # Group by day
    by_day: dict[str, dict] = {}
    for item in raw:
        day = item["day"]
        name = item["dailyDynamicValueTypeName"]
        by_day.setdefault(day, {})[name] = parse_value(item)

    sorted_days = sorted(by_day.keys())

    # Build per-day rows for charts
    daily_rows = []
    for day in sorted_days:
        d = by_day[day]
        sleep_min = d.get("SleepDuration", 0)
        daily_rows.append({
            "date": day,
            "resting_hr": d.get("HeartRateResting"),
            "hrv": round(d.get("Rmssd", 0), 1) or None,
            "sleep_quality": d.get("SleepQuality"),
            "sleep_hours": round(sleep_min / 60, 1) if sleep_min else None,
            "cardiovascular_risk": d.get("ThryveMainSleepRelatedCardiovascularRisk"),
            "stroke_risk": d.get("ThryveMainSleepRelatedStrokeRisk"),
            "mental_health_risk": d.get("ThryveMainSleepRelatedMentalHealthRisk"),
            "dementia_risk": d.get("ThryveMainSleepRelatedDementiaRisk"),
            "life_expectancy_impact": d.get("ThryveMainSleepRelatedLifeExpectancyImpact"),
        })

    # Latest values
    latest = by_day[sorted_days[-1]] if sorted_days else {}
    sleep_min = latest.get("SleepDuration", 0)

    def trend(key: str) -> list:
        return [by_day[d].get(key) for d in sorted_days if by_day[d].get(key) is not None]

    return {
        "source": "Whoop",
        "profile": "Active Gym Guy",
        "last_updated": sorted_days[-1] if sorted_days else None,
        "metrics": {
            "resting_hr": {
                "latest": latest.get("HeartRateResting"),
                "unit": "bpm",
                "trend": trend("HeartRateResting"),
            },
            "hrv": {
                "latest": round(latest.get("Rmssd", 0), 1) or None,
                "unit": "ms",
                "trend": [round(v, 1) for v in trend("Rmssd")],
            },
            "sleep_quality": {
                "latest": latest.get("SleepQuality"),
                "unit": "/100",
                "trend": trend("SleepQuality"),
            },
            "sleep_hours": {
                "latest": round(sleep_min / 60, 1) if sleep_min else None,
                "unit": "hours",
                "trend": [round(m / 60, 1) for m in trend("SleepDuration")],
            },
        },
        "risks": {
            "cardiovascular": latest.get("ThryveMainSleepRelatedCardiovascularRisk"),
            "stroke": latest.get("ThryveMainSleepRelatedStrokeRisk"),
            "mental_health": latest.get("ThryveMainSleepRelatedMentalHealthRisk"),
            "dementia": latest.get("ThryveMainSleepRelatedDementiaRisk"),
            "life_expectancy_impact": latest.get("ThryveMainSleepRelatedLifeExpectancyImpact"),
        },
        "days": daily_rows,
    }
