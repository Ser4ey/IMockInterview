from abc import ABC, abstractmethod
from typing import List, Dict, Any

class AIService(ABC):
    @abstractmethod
    async def generate_completion(self, messages: List[Dict[str, str]], temperature: float = 0.5, max_tokens: int = 1000) -> str:
        """
        Generate a text completion using the AI model.
        :param messages: List of messages (e.g., [{"role": "user", "text": "Hello"}])
        :param temperature: Sampling temperature
        :param max_tokens: Maximum tokens to generate
        :return: Generated text
        """
        pass
    
    @abstractmethod
    async def generate_interview_questions(self, position: str, level: str) -> List[str]:
        """
        Generate a list of interview questions.
        :param position: Job position (e.g., "Python Developer")
        :param level: Seniority level (e.g., "Junior", "Middle")
        :return: List of questions
        """
        pass

    @abstractmethod
    async def conduct_interview_step(self, chat_history: List[Dict[str, Any]], message: str) -> str:
        """
        Conduct one step of the interview.
        :param chat_history: Previous messages (list of dicts with 'role' and 'content')
        :param message: Latest user message
        :return: AI response
        """
        pass

    @abstractmethod
    async def analyze_interview(self, chat_history: List[Dict[str, Any]]) -> str:
        """
        Analyze the interview performance.
        :param chat_history: Full chat history
        :return: Feedback report
        """
        pass
