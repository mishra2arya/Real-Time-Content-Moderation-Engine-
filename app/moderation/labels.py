"""Label definitions and policy category taxonomies for content moderation."""

from enum import Enum
from typing import Dict, Set


class ModerationDecision(str, Enum):
    """Business/policy decision for moderated content."""

    ALLOW = "allow"
    BLOCK = "block"
    FLAG_REVIEW = "flag_review"


class ContentLabel(str, Enum):
    """Primary classification label."""

    NON_TOXIC = "non_toxic"
    TOXIC = "toxic"


class PolicyCategory(str, Enum):
    """Granular violation categories."""

    TOXICITY = "toxicity"
    SEVERE_TOXICITY = "severe_toxicity"
    INSULT = "insult"
    IDENTITY_ATTACK = "identity_attack"
    THREAT = "threat"
    SEXUAL_EXPLICIT = "sexual_explicit"


# Mapping from integer model classes to label strings
ID2LABEL: Dict[int, str] = {
    0: ContentLabel.NON_TOXIC.value,
    1: ContentLabel.TOXIC.value,
}

LABEL2ID: Dict[str, int] = {
    ContentLabel.NON_TOXIC.value: 0,
    ContentLabel.TOXIC.value: 1,
}

# Subcategory keywords for fine-grained policy tagging
POLICY_KEYWORDS: Dict[PolicyCategory, Set[str]] = {
    PolicyCategory.THREAT: {
        "kill",
        "murder",
        "shoot",
        "stab",
        "execute",
        "destroy you",
        "hunt you",
        "strangle",
        "beat up",
        "put a bullet",
        "break your neck",
    },
    PolicyCategory.IDENTITY_ATTACK: {
        "subhuman",
        "vermin",
        "infidel",
        "race traitor",
        "scum like you",
        "go back to your country",
        "filthy immigrant",
        "degenerates",
    },
    PolicyCategory.INSULT: {
        "stupid",
        "idiot",
        "moron",
        "loser",
        "clown",
        "pathetic",
        "worthless",
        "dumb",
        "imbecile",
        "trash",
        "retard",
        "disgrace",
    },
    PolicyCategory.SEVERE_TOXICITY: {
        "die",
        "burn in hell",
        "go die",
        "kill yourself",
        "kys",
        "drop dead",
        "suffer and die",
    },
    PolicyCategory.SEXUAL_EXPLICIT: {
        "naked pics",
        "send nudes",
        "rape",
        "molest",
        "grope",
    },
}
