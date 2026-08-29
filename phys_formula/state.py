"""Chat State: the UI's only bridge to the responder and the store."""

import base64
import uuid

import reflex as rx
from reflex import get_upload_dir

from phys_formula import store
from phys_formula.responder import get_formulae

MAX_IMAGE_BYTES = 5 * 1024 * 1024  # 5 MB cap, stated in the README
ALLOWED_MIMES = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}
TYPE_ERROR = "Only PNG, JPEG or WebP images can be attached."
SIZE_ERROR = "That image is over the 5 MB limit; please attach a smaller one."


class ChatState(rx.State):
    messages: list[dict[str, str]] = []
    question: str = ""
    thinking: bool = False
    pending_image: str = ""  # filename under the upload dir, awaiting submit
    pending_mime: str = ""
    error: str = ""

    @rx.event
    def set_question(self, value: str):
        self.question = value

    @rx.event
    def load_history(self):
        """Reload the shared thread from SQLite (page on_load)."""
        self.messages = store.load_messages()

    # ---- attachments ------------------------------------------------------

    def attach_bytes(self, data: bytes, mime: str) -> None:
        """Validate type + size, save under the upload dir, and mark it pending.

        Shared by the upload and the paste paths so the cap holds for both.
        """
        mime = (mime or "").split(";")[0].strip().lower()
        if mime not in ALLOWED_MIMES:
            self.error = TYPE_ERROR
            return
        if len(data) > MAX_IMAGE_BYTES:
            self.error = SIZE_ERROR
            return
        upload_dir = get_upload_dir()
        upload_dir.mkdir(parents=True, exist_ok=True)
        name = f"{uuid.uuid4().hex}.{ALLOWED_MIMES[mime]}"
        (upload_dir / name).write_bytes(data)
        self.pending_image = name
        self.pending_mime = mime
        self.error = ""

    @rx.event
    async def handle_upload(self, files: list[rx.UploadFile]):
        """Dropzone / file-picker path."""
        for f in files[:1]:
            data = await f.read()
            self.attach_bytes(data, f.content_type or "")

    @rx.event
    def handle_paste(self, items: list[tuple[str, str]]):
        """Clipboard path: binary items arrive as ``data:<mime>;base64,...`` URIs."""
        for mime, payload in items:
            if not mime.startswith("image/"):
                continue
            header, _, b64 = payload.partition(",")
            if not header.startswith("data:") or not b64:
                continue
            self.attach_bytes(base64.b64decode(b64), mime)
            return

    @rx.event
    def upload_rejected(self, rejections):
        """Dropzone rejected the file client-side (type or size)."""
        self.error = f"{TYPE_ERROR} {SIZE_ERROR}"

    @rx.event
    def clear_image(self):
        self.pending_image = ""
        self.pending_mime = ""
        self.error = ""

    # ---- submit -----------------------------------------------------------

    @rx.event
    def submit(self):
        problem = self.question.strip()
        image_name, mime = self.pending_image, self.pending_mime
        if (not problem and not image_name) or self.thinking:
            return
        image_bytes = None
        if image_name:
            image_bytes = (get_upload_dir() / image_name).read_bytes()
        self.question = ""
        self.pending_image = ""
        self.pending_mime = ""
        self.error = ""
        self.messages.append({"role": "user", "content": problem, "image": image_name})
        store.save_message("user", problem, image_name)
        self.thinking = True
        yield  # push the user bubble + thinking indicator before the (slow) responder

        try:
            reply = get_formulae(problem, image_bytes, mime or None)
        finally:
            self.thinking = False
        self.messages.append({"role": "assistant", "content": reply, "image": ""})
        store.save_message("assistant", reply)
