import re


FRAMES = {
    'SCENE': ['initial-scene', 'participant', 'scene', 'scene', 'transitory-scene', 'target-scene'],
    'IDENTIFICATION': ['identified', 'identifier'],
    'RANK': ['has-rank', 'rank'],
    'CLASS': ['initial-class', 'has-class', 'class', 'target-class'],
    'EXISTENCE': ['exists'],
    'TRANSFORMATION-CREATION': ['material', 'created'],
    'REPRODUCTION': ['original', 'copy'],
    'QUALITY': ['has-quality', 'quality'],
    'STATE': ['initial-state', 'has-state', 'state', 'target-state'],
    'DESTRUCTION': ['destroyed'],
    'EXPERIENCE': ['experiencer', 'experienced'],
    'ACTIVITY': ['is-active', 'activity'],
    'FOCUS': ['has-focus', 'focus'],
    'MODE': ['has-mode', 'mode'],
    'ACCOMPANIMENT': ['accompanied', 'accompanier'],
    'DEPICTIVE': ['has-depictive', 'depictive'],
    'ATTRIBUTE': ['has-attribute', 'attribute'],
    'ASSET': ['has-asset', 'asset'],
    'COMPARISON': ['compared', 'reference'],
    'CONCESSION': ['asserted', 'conceded'],
    'EXPLANATION': ['explained', 'explanation'],
    'LOCATION': ['initial-location', 'has-location', 'location', 'transitory-location', 'target-location'],
    'WRAPPING-WEARING': ['initial-wearer', 'worn', 'wearer', 'target-wearer'],
    'ADORNMENT-TARNISHMENT': ['initial-surface', 'ornament', 'surface', 'target-surface'],
    'HITTING': ['hitting', 'hit'],
    'INGESTION': ['ingested', 'transitory-location', 'ingester'],
    'EXCRETION': ['excreter', 'excreted', 'transitory-location'],
    'UNANCHORED-MOTION': ['in-motion', 'transitory-location'],
    'MEANS': ['has-means', 'means'],
    'MESSAGE': ['topic', 'content'],
    'PART-WHOLE': ['initial-whole', 'part', 'whole', 'target-whole'],
    'POSSESSION': ['initial-possessor', 'possessed', 'possessor', 'target-possessor'],
    'QUANTITY': ['has-quantity', 'quantity'],
    'SENDING': ['sent', 'sender'],
    'SEQUENCE': ['follows', 'followed'],
    'CAUSATION': ['result', 'causer'],
    'REACTION': ['reaction', 'trigger'],
    'RESULTATIVE': ['has-resultative', 'resultative'],
    'CONDITION': ['has-condition', 'condition'],
    'EXCEPTION': ['has-exception', 'exception'],
    'SOCIAL-RELATION': ['initial-social-relation', 'has-social-relation', 'social-relation', 'target-social-relation'],
    'TIME': ['has-time', 'time'],
    'NONCOMP': ['has-noncomp', 'noncomp'],
}
ASPECTS = ('INIT', 'DEINIT', 'CHANGE', 'CONTINUATION')
MODES = ('POSSIBILITY', 'NECESSITY', 'NEG')
FRAME_PATTERN = re.compile('(' + '|'.join(FRAMES.keys()) + ')(-(' +
        '|'.join(ASPECTS) + '))?(-(' + '|'.join(MODES) + '))?$')


def check_frame_label(frame):
    return all(check_frame_label_part(p) for p in re.split(r' (?:>>|\|\|) ', frame))


def check_frame_label_part(frame):
    return FRAME_PATTERN.match(frame)


def check_dep_label(dep, frame):
    frame_label_parts = re.split(r' (?:>>|\|\|) ', frame)
    dep_label_parts = re.split(r' (?:>>|\|\|) ', dep)
    if len(dep_label_parts) == 1:
        dep_label_parts *= len(frame_label_parts)
    if len(frame_label_parts) == 1:
        frame_label_parts *= len(dep_label_parts)
    if len(dep_label_parts) != len(frame_label_parts):
        return False
    for f, d in zip(frame_label_parts, dep_label_parts):
        if check_dep_label_part(d, f):
            return True
    return False


def check_dep_label_part(dep, frame):
    if dep[:2] in ('m-', 'x-'):
        role = dep[2:]
        return any(role in v for v in FRAMES.values())
    m = FRAME_PATTERN.match(frame)
    f = m.group(1)
    if dep not in FRAMES[f]:
        return False
    return True
