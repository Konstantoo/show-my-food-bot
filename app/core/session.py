import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from app.config import Config


@dataclass
class UserSession:
    """Сессия пользователя"""
    user_id: int
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    
    # Состояние анализа фото
    current_photo_analysis: Optional[Any] = None
    advice_shown: List[str] = field(default_factory=list)  # Тексты уже показанных советов
    
    # Состояние диалога
    waiting_for_confirmation: bool = False
    waiting_for_photo: bool = False
    
    def update_activity(self):
        """Обновляет время последней активности"""
        self.last_activity = time.time()
    
    def is_expired(self) -> bool:
        """Проверяет, истекла ли сессия"""
        return (time.time() - self.last_activity) > (Config.SESSION_TIMEOUT_MINUTES * 60)
    
    def reset_photo_state(self):
        """Сбрасывает состояние анализа фото"""
        self.current_photo_analysis = None
        self.waiting_for_confirmation = False
        self.waiting_for_photo = False
    
    def add_advice_shown(self, advice_text: str):
        """Добавляет показанный совет в список"""
        if advice_text not in self.advice_shown:
            self.advice_shown.append(advice_text)
    
    def get_exclude_advice(self) -> List[str]:
        """Возвращает список советов для исключения"""
        return self.advice_shown.copy()


class SessionStore:
    """Хранилище сессий в памяти"""
    
    def __init__(self):
        self._sessions: Dict[int, UserSession] = {}
    
    def get_session(self, user_id: int) -> UserSession:
        """Получает или создает сессию пользователя"""
        if user_id not in self._sessions:
            self._sessions[user_id] = UserSession(user_id=user_id)
        
        session = self._sessions[user_id]
        
        # Проверяем, не истекла ли сессия
        if session.is_expired():
            self._sessions[user_id] = UserSession(user_id=user_id)
            session = self._sessions[user_id]
        
        session.update_activity()
        return session
    
    def cleanup_expired_sessions(self):
        """Удаляет истекшие сессии"""
        current_time = time.time()
        expired_users = []
        
        for user_id, session in self._sessions.items():
            if session.is_expired():
                expired_users.append(user_id)
        
        for user_id in expired_users:
            del self._sessions[user_id]
        
        if expired_users:
            print(f"Удалено {len(expired_users)} истекших сессий")
    
    def get_active_sessions_count(self) -> int:
        """Возвращает количество активных сессий"""
        return len(self._sessions)


