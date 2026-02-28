"""
Subjective Question Generator using GROQ AI
Generates open-ended, essay-type questions from input text.
"""

import json
import os
import re
import requests


class SubjectiveTest:
    def __init__(self, text_content, no_of_questions, api_key=None):
        self.text_content = text_content
        self.no_of_questions = no_of_questions
        self.api_key = api_key or os.getenv("GROQ_API_KEY")

        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")

    def _make_prompt(self, count: int) -> str:
        return f"""
You are an expert educational content creator.

Generate exactly {count} subjective (essay type) questions from the given text.

Return ONLY JSON in format:
{{
  "questions": [
    {{"question": "...", "answer": "..."}}
  ]
}}

Text:
{self.text_content}
"""

    def _parse_response(self, response_text: str):
        """Parse JSON into (questions, answers) lists. Returns ([], []) on failure."""
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError:
            return [], []
        questions = []
        answers = []
        for item in data.get("questions", []):
            questions.append(item.get("question", ""))
            answers.append(item.get("answer", ""))
        return questions, answers

    def generate_test(self):
        """Generate subjective questions in batches to avoid response truncation."""
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            batch_size = 4
            all_questions = []
            all_answers = []
            remaining = self.no_of_questions

            while remaining > 0:
                count = min(batch_size, remaining)
                prompt = self._make_prompt(count)
                payload = {
                    "model": "llama3-70b-8192",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 4096,
                }
                response = requests.post(url, headers=headers, json=payload, timeout=60)
                response.raise_for_status()
                result = response.json()
                response_text = (result.get("choices") or [{}])[0].get("message", {}).get("content", "") or ""

                q_batch, a_batch = self._parse_response(response_text)
                if not q_batch and remaining == self.no_of_questions:
                    return self._fallback_parse(response_text)
                if not q_batch:
                    all_questions.extend(["Question not generated"] * remaining)
                    all_answers.extend(["Answer not available"] * remaining)
                    return all_questions[:self.no_of_questions], all_answers[:self.no_of_questions]
                all_questions.extend(q_batch[:count])
                all_answers.extend(a_batch[:count])
                remaining -= len(q_batch[:count])

            while len(all_questions) < self.no_of_questions:
                all_questions.append("Question not generated")
                all_answers.append("Answer not available")
            return all_questions[:self.no_of_questions], all_answers[:self.no_of_questions]

        except Exception as e:
            return self._fallback_parse(str(e))

    def _fallback_parse(self, text):
        questions = []
        answers = []

        pattern = r'(\d+\.\s*[^?]+\?)'
        matches = re.findall(pattern, text)

        for i, q in enumerate(matches[:self.no_of_questions]):
            questions.append(q)
            answers.append(f"Answer for {q}")

        while len(questions) < self.no_of_questions:
            questions.append("Question not generated")
            answers.append("Answer not available")

        return questions, answers