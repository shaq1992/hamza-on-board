"""Physics-formula chat page."""

import reflex as rx

from phys_formula.state import ChatState


def bubble(msg: dict) -> rx.Component:
    is_user = msg["role"] == "user"
    return rx.box(
        rx.cond(
            is_user,
            rx.text(msg["content"], white_space="pre-wrap"),
            rx.markdown(msg["content"]),
        ),
        background_color=rx.cond(is_user, rx.color("accent", 4), rx.color("gray", 3)),
        padding="0.6em 1em",
        border_radius="12px",
        max_width="80%",
        align_self=rx.cond(is_user, "flex-end", "flex-start"),
    )


def thinking_indicator() -> rx.Component:
    return rx.cond(
        ChatState.thinking,
        rx.hstack(rx.spinner(size="2"), rx.text("Thinking...", color="gray"), align="center"),
    )


def index() -> rx.Component:
    return rx.container(
        rx.vstack(
            rx.heading("Physics formula helper", size="6"),
            rx.text("Describe a physics problem; you get the formulae you need.", color="gray"),
            rx.vstack(
                rx.foreach(ChatState.messages, bubble),
                thinking_indicator(),
                width="100%",
                spacing="3",
                min_height="50vh",
            ),
            rx.form(
                rx.hstack(
                    rx.input(
                        value=ChatState.question,
                        on_change=ChatState.set_question,
                        placeholder="e.g. A 2 kg block slides down a 30 degree incline...",
                        width="100%",
                        id="problem",
                    ),
                    rx.button("Ask", type="submit", loading=ChatState.thinking, id="submit"),
                    width="100%",
                ),
                on_submit=ChatState.submit,
                width="100%",
            ),
            width="100%",
            spacing="4",
        ),
        size="3",
        padding_y="2em",
    )


app = rx.App()
app.add_page(index, title="Physics formulae", on_load=ChatState.load_history)
