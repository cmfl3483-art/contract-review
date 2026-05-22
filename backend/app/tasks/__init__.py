"""
Celery 异步任务模块
Celery async tasks module
"""

from app.tasks.ai_tasks import generate_ai_summary_task

__all__ = ["generate_ai_summary_task"]
