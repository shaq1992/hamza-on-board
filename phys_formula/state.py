"""Chat State: the UI's only bridge to the responder and the store."""

import reflex as rx

from phys_formula import store
from phys_formula.responder import get_formulae


class ChatState(rx.State):
    messages: list[dict[str, str]] = []
    question: str = ""
    thinking: bool = False

    @rx.event
    def set_question(self, value: str):
        self.question = value

    @rx.event
    def load_history(self):
        """Reload the shared thread from SQLite (page on_load)."""
        self.messages = store.load_messages()

    @rx.event
    def submit(self):
        problem = self.question.strip()
        if not problem or self.thinking:
            return
        self.question = ""
        self.messages.append({"role": "user", "content": problem})
        store.save_message("user", problem)
        self.thinking = True
        yield  # push the user bubble + thinking indicator before the (slow) responder

        try:
            reply = get_formulae(problem)
        finally:
            self.thinking = False
        self.messages.append({"role": "assistant", "content": reply})
        store.save_message("assistant", reply)
