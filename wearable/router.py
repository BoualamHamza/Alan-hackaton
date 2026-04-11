from fastapi import APIRouter, Query

from wearable.thryve_client import build_dashboard, fetch_daily_data

router = APIRouter(prefix="/api/v1/wearable", tags=["Wearable"])


@router.get(
    "/dashboard",
    summary="Tableau de bord wearable (Whoop — Active Gym Guy)",
    response_description="Métriques santé + scores de risque, prêts à afficher",
)
async def get_dashboard(days: int = Query(default=30, ge=7, le=90)):
    """
    Retourne les métriques wearable formatées pour le dashboard patient.

    - **days** : nombre de jours d'historique (7–90, défaut 30)

    Réponse :
    - `metrics` : resting_hr, hrv, sleep_quality, sleep_hours — valeur latest + tendance
    - `risks` : cardiovascular, stroke, mental_health, dementia, life_expectancy_impact
    - `days` : tableau complet jour par jour pour les graphiques
    """
    raw = await fetch_daily_data(days)
    return build_dashboard(raw)
