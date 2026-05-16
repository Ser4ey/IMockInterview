from app.models.interview import InterviewSession, InterviewStage, Message, MessageSender


class PromptBuilder:
    def build_stage_messages(
        self,
        session: InterviewSession,
        stage: InterviewStage,
        history: list[Message],
    ) -> list[dict[str, str]]:
        transcript = self._format_history(history)
        system_prompt = (
            "Ты профессиональный интервьюер для mock-собеседований. "
            "Веди диалог на русском языке, задавай один понятный вопрос за раз, "
            "не раскрывай итоговую оценку до финального этапа."
        )
        user_prompt = (
            f"Специализация: {session.specialization}\n"
            f"Уровень: {session.level}\n"
            f"Тип интервью: {session.interview_type}\n"
            f"Текущий этап: {stage.value}\n"
            f"История диалога:\n{transcript}\n\n"
            "Сформулируй следующий вопрос или реплику интервьюера для этого этапа."
        )
        return [{"role": "system", "text": system_prompt}, {"role": "user", "text": user_prompt}]

    def build_evaluation_messages(self, session: InterviewSession, history: list[Message]) -> list[dict[str, str]]:
        transcript = self._format_history(history)
        system_prompt = (
            "Ты аналитик технических собеседований. Верни только JSON с полями "
            "score, correctness, completeness, depth, communication, recommendations. "
            "Все числовые значения должны быть от 0 до 100."
        )
        user_prompt = (
            "Оцени mock-собеседование.\n"
            f"Специализация: {session.specialization}\n"
            f"Уровень: {session.level}\n"
            f"История:\n{transcript}"
        )
        return [{"role": "system", "text": system_prompt}, {"role": "user", "text": user_prompt}]

    def _format_history(self, history: list[Message]) -> str:
        if not history:
            return "История пока пустая."

        labels = {
            MessageSender.USER.value: "Кандидат",
            MessageSender.AI.value: "Интервьюер",
            MessageSender.SYSTEM.value: "Система",
        }
        lines = []
        for message in history:
            label = labels.get(message.sender, message.sender)
            lines.append(f"{label}: {message.content}")
        return "\n".join(lines)


prompt_builder = PromptBuilder()
