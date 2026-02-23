from pyannote.core import Annotation


def select_human_speakers(speakers_info, limit=1):
    humans = [
        s for s in speakers_info
        if not s["robot"]["is_robot"] and s["segments"]
    ]

    if not humans:
        return []

    humans_sorted = sorted(humans, key=lambda x: x["segments"][0][0])

    return [h["speaker"] for h in humans_sorted[:limit]]