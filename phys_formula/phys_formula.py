"""Physics-formula chat page."""

import reflex as rx

from phys_formula.state import MAX_IMAGE_BYTES, ChatState

UPLOAD_ID = "problem_image"


def bubble(msg: dict) -> rx.Component:
    is_user = msg["role"] == "user"
    return rx.box(
        rx.cond(
            msg["image"] != "",
            rx.image(
                src=rx.get_upload_url(msg["image"]),
                alt="attached screenshot",
                max_height="240px",
                max_width="100%",
                border_radius="8px",
                margin_bottom="0.4em",
            ),
        ),
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


def attachment_row() -> rx.Component:
    """Pending thumbnail + remove button, and any attach error."""
    return rx.vstack(
        rx.cond(
            ChatState.pending_image != "",
            rx.hstack(
                rx.image(
                    src=rx.get_upload_url(ChatState.pending_image),
                    alt="pending screenshot",
                    max_height="120px",
                    border_radius="8px",
                ),
                rx.button(
                    "Remove image",
                    on_click=ChatState.clear_image,
                    variant="soft",
                    color_scheme="gray",
                    size="1",
                    id="remove_image",
                ),
                align="center",
            ),
        ),
        rx.cond(
            ChatState.error != "",
            rx.text(ChatState.error, color="red", size="2", id="attach_error"),
        ),
        width="100%",
        spacing="2",
    )


def index() -> rx.Component:
    return rx.container(
        rx.vstack(
            rx.heading("Physics formula helper", size="6"),
            rx.text(
                "Describe a physics problem, attach a screenshot of one, or both; "
                "you get the formulae you need.",
                color="gray",
            ),
            rx.vstack(
                rx.foreach(ChatState.messages, bubble),
                thinking_indicator(),
                width="100%",
                spacing="3",
                min_height="50vh",
            ),
            attachment_row(),
            rx.clipboard(
                rx.form(
                    rx.hstack(
                        rx.upload(
                            rx.button(
                                "Attach image",
                                type="button",
                                variant="soft",
                                id="attach",
                            ),
                            id=UPLOAD_ID,
                            multiple=False,
                            max_files=1,
                            max_size=MAX_IMAGE_BYTES,
                            accept={
                                "image/png": [".png"],
                                "image/jpeg": [".jpg", ".jpeg"],
                                "image/webp": [".webp"],
                            },
                            on_drop=ChatState.handle_upload(rx.upload_files(upload_id=UPLOAD_ID)),
                            on_drop_rejected=ChatState.upload_rejected,
                            padding="0",
                            border="none",
                        ),
                        rx.input(
                            value=ChatState.question,
                            on_change=ChatState.set_question,
                            placeholder="Type a problem, or paste (Ctrl+V) a screenshot here...",
                            width="100%",
                            id="problem",
                        ),
                        rx.button("Ask", type="submit", loading=ChatState.thinking, id="submit"),
                        width="100%",
                    ),
                    on_submit=ChatState.submit,
                    width="100%",
                    id="ask_form",
                ),
                on_paste=ChatState.handle_paste,
            ),
            width="100%",
            spacing="4",
        ),
        size="3",
        padding_y="2em",
    )


app = rx.App()
app.add_page(index, title="Physics formulae", on_load=ChatState.load_history)
