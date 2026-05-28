import logging

import requests


logger = logging.getLogger(__name__)


def _get_json(url):
    try:
        response = requests.get(url, timeout=4)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        logger.warning("External API request failed for %s: %s", url, exc)
        return None


def load_external_widgets():
    django_repo = _get_json("https://api.github.com/repos/django/django")
    air_quality = _get_json(
        "https://air-quality-api.open-meteo.com/v1/air-quality"
        "?latitude=53.9&longitude=27.5667&current=pm10,pm2_5"
    )
    current_air = (air_quality or {}).get("current") or {}

    return {
        "github_stars": (django_repo or {}).get("stargazers_count", "нет данных"),
        "github_forks": (django_repo or {}).get("forks_count", "нет данных"),
        "github_updated": (django_repo or {}).get("updated_at", "нет данных"),
        "pm10": current_air.get("pm10", "нет данных"),
        "pm25": current_air.get("pm2_5", "нет данных"),
    }
