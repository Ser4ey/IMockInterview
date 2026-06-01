from app.models.interview import InterviewSession, InterviewType, Message, MessageSender, Question
from app.services.serialization import loads_list


class PromptBuilder:
    def build_question_generation_messages(
        self,
        interview_type: InterviewType,
        level: str,
        requested_count: int,
    ) -> list[dict[str, str]]:
        system_prompt = (
            "Ты методист технических mock-собеседований. Верни только валидный JSON-объект с полем questions. "
            "Не добавляй Markdown, пояснения или текст вне JSON."
        )
        user_prompt = (
            "Сформируй банк вопросов для mock-собеседования.\n"
            f"Название: {interview_type.title}\n"
            f"Роль: {interview_type.role}\n"
            f"Стек: {interview_type.technology_stack}\n"
            f"Уровень: {level}\n"
            f"Количество вопросов: {requested_count}\n\n"
            "Если используется AI Studio Agent с Web Search, используй встроенный поиск агента для актуализации тем.\n\n"
            "Верни объект {\"questions\": [...]}. Каждый элемент questions должен иметь поля: question_text, level, tags, expected_answer, "
            "evaluation_criteria, source_title, source_url. evaluation_criteria и tags должны быть массивами строк."
        )
        return [{"role": "system", "text": system_prompt}, {"role": "user", "text": user_prompt}]

    def build_interviewer_reply_messages(
        self,
        session: InterviewSession,
        question: Question,
        history: list[Message],
    ) -> list[dict[str, str]]:
        transcript = self._format_history(history)
        criteria = ", ".join(loads_list(question.evaluation_criteria)) or "общая полнота и корректность ответа"
        system_prompt = (
            "Ты AI-интервьюер в специализированном сервисе mock-собеседований. "
            "Работай строго в рамках текущего вопроса из банка. Не придумывай новую тему, "
            "если ответ кандидата можно уточнить по текущим критериям. Говори на русском языке."
        )
        user_prompt = (
            f"Тип интервью: {session.interview_type.title}\n"
            f"Роль: {session.interview_type.role}\n"
            f"Стек: {session.interview_type.technology_stack}\n"
            f"Уровень: {session.level}\n\n"
            f"Вопрос из банка: {question.question_text}\n"
            f"Эталонный ответ: {question.expected_answer}\n"
            f"Критерии оценки: {criteria}\n\n"
            f"История диалога:\n{transcript}\n\n"
            "Сформулируй один уточняющий вопрос или короткую реакцию интервьюера. "
            "Не ставь итоговую оценку и не раскрывай эталонный ответ полностью."
        )
        return [{"role": "system", "text": system_prompt}, {"role": "user", "text": user_prompt}]

    def build_evaluation_messages(
        self,
        session: InterviewSession,
        questions: list[Question],
        history: list[Message],
    ) -> list[dict[str, str]]:
        transcript = self._format_history(history)
        question_block = "\n\n".join(
            (
                f"Вопрос {index + 1}: {question.question_text}\n"
                f"Эталонный ответ: {question.expected_answer}\n"
                f"Критерии: {', '.join(loads_list(question.evaluation_criteria))}"
            )
            for index, question in enumerate(questions)
        )
        system_prompt = (
            "Ты аналитик технических mock-собеседований. Верни только JSON с полями: "
            "score, correctness, completeness, depth, communication, strengths, weaknesses, recommendations, summary. "
            "Числа должны быть от 0 до 100. strengths и weaknesses - массивы строк."
        )
        user_prompt = (
            f"Тип интервью: {session.interview_type.title}\n"
            f"Роль: {session.interview_type.role}\n"
            f"Стек: {session.interview_type.technology_stack}\n"
            f"Уровень: {session.level}\n\n"
            f"Вопросы банка и критерии:\n{question_block}\n\n"
            f"История диалога:\n{transcript}\n\n"
            "Оцени ответы кандидата по критериям вопросов."
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
