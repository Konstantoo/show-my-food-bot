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
    
    # Состояние анализа блюда
    current_dish: Optional[str] = None
    current_ingredients: List[str] = field(default_factory=list)
    current_weight: Optional[int] = None
    current_cooking_method: str = "варка"
    
    # Результаты анализа
    nutrition_result: Optional[Any] = None
    facts_shown: List[str] = field(default_factory=list)  # Тексты уже показанных фактов
    
    # Состояние диалога
    waiting_for_confirmation: bool = False
    waiting_for_weight: bool = False
    waiting_for_cooking_method: bool = False
    
    def update_activity(self):
        """Обновляет время последней активности"""
        self.last_activity = time.time()
    
    def is_expired(self) -> bool:
        """Проверяет, истекла ли сессия"""
        return (time.time() - self.last_activity) > (Config.SESSION_TIMEOUT_MINUTES * 60)
    
    def reset_dish_state(self):
        """Сбрасывает состояние анализа блюда"""
        self.current_dish = None
        self.current_ingredients = []
        self.current_weight = None
        self.current_cooking_method = "варка"
        self.nutrition_result = None
        self.waiting_for_confirmation = False
        self.waiting_for_weight = False
        self.waiting_for_cooking_method = False
    
    def add_fact_shown(self, fact_text: str):
        """Добавляет показанный факт в список"""
        if fact_text not in self.facts_shown:
            self.facts_shown.append(fact_text)
    
    def get_exclude_facts(self) -> List[str]:
        """Возвращает список фактов для исключения"""
        return self.facts_shown.copy()


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


