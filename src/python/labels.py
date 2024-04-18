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
    'UNANCHORED-MOTION': ['mover', 'transitory-location'],
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
}
ASPECTS = ('INIT', 'DEINIT', 'CHANGE', 'CONTINUATION')
MODES = ('POSSIBILITY', 'NECESSITY', 'NEG')
FRAME_PATTERN = re.compile('(' + '|'.join(FRAMES.keys()) + ')(-(' +
        '|'.join(ASPECTS) + '))?(-(' + '|'.join(MODES) + '))?$')


def check_frame_label(frame):
    return FRAME_PATTERN.match(frame)


def check_dep_label(dep, frame):
    if dep[:2] in ('m-', 'x-'):
        role = dep[2:]
        return any(role in v for v in FRAMES.values())
    m = FRAME_PATTERN.match(frame)
    f = m.group(1)
    if dep not in FRAMES[f]:
        return False
    return True
