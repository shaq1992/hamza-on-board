"""Pluggable responder: the only thing the UI State calls to get a reply.

Session 03 replaces the body of ``get_formulae`` with the OpenAI call; the
signature and the module path are the contract the UI depends on.
"""

STUB_REPLY = r"""Here are the formulae you will likely need (stub reply -- no model was called):

- Newton's second law: $F = m a$
- Kinematics (constant acceleration): $v = v_0 + a t$, $\;s = v_0 t + \tfrac{1}{2} a t^2$, $\;v^2 = v_0^2 + 2 a s$
- Kinetic energy: $E_k = \tfrac{1}{2} m v^2$
- Gravitational potential energy: $E_p = m g h$

Identify the knowns, pick the equation containing exactly one unknown, and solve.
"""


def get_formulae(problem: str) -> str:
    """Return the formulae relevant to ``problem`` as Markdown (LaTeX allowed).

    Stub implementation: ignores the problem text and returns a canned reply.
    """
    return STUB_REPLY
