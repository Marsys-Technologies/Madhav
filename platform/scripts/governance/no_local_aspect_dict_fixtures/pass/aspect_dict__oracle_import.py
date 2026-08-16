# PASS fixture — uses the canonical oracle from brahmagyan.aspects
# No local graha-to-aspect dict defined here.

from brahmagyan.aspects import get_graha_aspects, NODE_PARASHARI_ASPECTS  # noqa: F401


def check_aspect(graha: str, house_offset: int) -> bool:
    aspects = get_graha_aspects(graha)
    return house_offset in aspects
