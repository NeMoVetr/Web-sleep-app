from celery import shared_task
from sleep_tracking_app.services.factory import create_rag_service

@shared_task(bind=True)
def enhance_recommendation_task(self, gemini_response: str, user_data: dict):
    svc = create_rag_service()
    return svc.enhance(gemini_response, user_data)
