"""
Local question generator.

Generates objective and subjective questions from input text without using
external AI APIs. Optionally uses a SentencePiece model (spiece.model) if
available to score sentences, but it is not required.
"""

import os
import re
from pathlib import Path
from typing import List, Tuple

try:
    import sentencepiece as spm  # type: ignore
except ImportError:
    spm = None


def _load_spiece_model():
    """
    Try to load a SentencePiece model from:
    - environment variable SPM_MODEL_PATH
    - Django setting SPM_MODEL_PATH
    - local ./spiece.model next to this file
    Returns a SentencePieceProcessor instance or None.
    """
    model_path = os.getenv("SPM_MODEL_PATH")

    if not model_path:
        try:
            from django.conf import settings

            model_path = getattr(settings, "SPM_MODEL_PATH", None)
        except Exception:
            model_path = None

    if not model_path:
        candidate = Path(__file__).resolve().parent / "spiece.model"
        if candidate.exists():
            model_path = str(candidate)

    if not model_path or not spm:
        return None

    if not os.path.exists(model_path):
        return None

    proc = spm.SentencePieceProcessor()
    proc.load(model_path)
    return proc


_SPIECE = _load_spiece_model()


def _split_sentences(text: str) -> List[str]:
    text = re.sub(r"\s+", " ", text.strip())
    if not text:
        return []
    parts = re.split(r"(?<=[.!?])\s+", text)
    sentences = [p.strip() for p in parts if len(p.strip()) > 20]
    return sentences


def _score_sentence(sent: str) -> int:
    if not _SPIECE:
        return len(sent)
    try:
        return len(_SPIECE.encode(sent, out_type=int))
    except Exception:
        return len(sent)


def generate_objective_test(text_content: str, no_of_questions: int) -> Tuple[List[str], List[str]]:
    """
    Generate objective (MCQ) questions locally.

    Each question string is formatted as:
    "<question>\\nA) ...\\nB) ...\\nC) ...\\nD) ..."
    The answers list contains the correct option text.
    """
    no_of_questions = max(int(no_of_questions or 0), 1)
    text_content = text_content or ""

    sentences = _split_sentences(text_content)
    if not sentences:
        questions: List[str] = []
        answers: List[str] = []
        for i in range(no_of_questions):
            questions.append(f"Question {i+1} could not be generated.")
            answers.append("Answer not available.")
        return questions, answers

    sentences.sort(key=_score_sentence, reverse=True)
    selected = sentences[:no_of_questions]

    questions: List[str] = []
    answers: List[str] = []

    for sent in selected:
        base_q = re.sub(r"^\d+[\).\s]+", "", sent).strip()
        if not base_q.endswith("?"):
            question_text = f"What is the key idea of the following statement?\n{base_q}"
        else:
            question_text = base_q

        correct_option = base_q
        distractors = [
            "This option is unrelated to the passage.",
            "This option only partially reflects the passage.",
            "This option contradicts the passage.",
        ]
        options = [correct_option] + distractors

        formatted_question = (
            f"{question_text}\n"
            f"A) {options[0]}\n"
            f"B) {options[1]}\n"
            f"C) {options[2]}\n"
            f"D) {options[3]}"
        )

        questions.append(formatted_question)
        # Since the correct option is always option A in our list,
        # return just the option label "A" instead of full text.
        answers.append("A")

    while len(questions) < no_of_questions:
        i = len(questions) + 1
        questions.append(f"Question {i} could not be generated.")
        answers.append("Answer not available.")

    return questions[:no_of_questions], answers[:no_of_questions]


def generate_subjective_test(text_content: str, no_of_questions: int) -> Tuple[List[str], List[str]]:
    """
    Generate short-form subjective questions locally.

    Questions will be of styles such as:
    - "Define ..."
    - "Answer in brief ..."
    - "Write a one-line answer ..."

    All questions are derived from the provided description text.
    Returns two lists: questions and brief reference answers.
    """
    no_of_questions = max(int(no_of_questions or 0), 1)
    text_content = text_content or ""

    sentences = _split_sentences(text_content)
    if not sentences:
        questions: List[str] = []
        answers: List[str] = []
        for i in range(no_of_questions):
            questions.append(f"Question {i+1} could not be generated.")
            answers.append("Answer not available.")
        return questions, answers

    sentences.sort(key=_score_sentence, reverse=True)
    selected = sentences[:no_of_questions]

    questions: List[str] = []
    answers: List[str] = []

    def extract_topic(sentence: str) -> str:
        clean = re.sub(r"^\d+[\).\s]+", "", sentence).strip()
        clean = re.sub(r"[.?!]+$", "", clean).strip()
        lower = clean.lower()
        for kw in [" is ", " are ", " was ", " were ", " means ", " refers to "]:
            idx = lower.find(kw)
            if idx > 0:
                return clean[:idx].strip()
        words = clean.split()
        return " ".join(words[: min(len(words), 6)])

    patterns = [
        "Define {topic}.",
        "Answer in brief: {topic}.",
        "Write a one-line answer on {topic}.",
        "What do you understand by {topic}?",
    ]

    for idx, sent in enumerate(selected, start=1):
        topic = extract_topic(sent) or f"the concept in: {sent[:60]}..."
        template = patterns[(idx - 1) % len(patterns)]
        q = template.format(topic=topic)
        questions.append(q)
        answers.append(sent.strip())

    while len(questions) < no_of_questions:
        i = len(questions) + 1
        questions.append(f"Question {i} could not be generated.")
        answers.append("Answer not available.")

    return questions[:no_of_questions], answers[:no_of_questions]

