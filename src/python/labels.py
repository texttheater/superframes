import re


class Flexible:

    def __init__(self, arg1, arg2):
        self.arg1 = arg1
        self.arg2 = arg2

    def check_core(self, aspect, mode, role):
        if role == self.arg1:
            return True
        if aspect in ('INIT', 'PREVENTION'):
            return (
                (role.startswith('target-') and role[7:] == self.arg2) or
                (role.startswith('transitory-') and role[11:] == self.arg2)
            )
        if aspect in ('DEINIT', 'CONTINUATION'):
            return (
                (role.startswith('initial-') and role[8:] == self.arg2) or
                (role.startswith('transitory-') and role[11:] == self.arg2)
            )
        if aspect == 'CHANGE':
            return (
                (role.startswith('target-') and role[7:] == self.arg2) or
                (role.startswith('initial-') and role[8:] == self.arg2) or
                (role.startswith('transitory-') and role[11:] == self.arg2)
            )
        return role == self.arg2

    def check_noncore(self, role):
        return (
            (role == self.arg1) or
            (role == self.arg2) or
            (role.startswith('target-') and role[7:] == self.arg2) or
            (role.startswith('initial-') and role[8:] == self.arg2) or
            (role.startswith('transitory-') and role[11:] == self.arg2)
        )


class Rigid:

    def __init__(self, *roles):
        self.roles = roles

    def check_core(self, aspect, mode, role):
        if aspect is not None:
            return False
        return role in self.roles

    def check_noncore(self, role):
        return role in self.roles


FRAMES = {
    'SITUATION': Flexible('situated', 'situator'),
    'SCENE': Flexible('participant', 'scene'),
    'IDENTIFICATION': Flexible('identified', 'identifier'),
    'RANK': Flexible('has-rank', 'rank'),
    'CLASS': Flexible('has-class', 'class'),
    'EXISTENCE': Rigid('exists'),
    'TRANSFORMATION-CREATION': Rigid('material', 'created'),
    'REPRODUCTION': Rigid('original', 'copy'),
    'QUALITY': Flexible('has-quality', 'quality'),
    'STATE': Flexible('has-state', 'state'),
    'DESTRUCTION': Rigid('destroyed'),
    'EXPERIENCE': Flexible('experiencer', 'experienced'),
    'ACTIVITY': Flexible('is-active', 'activity'),
    'MODE': Rigid('has-mode', 'mode'),
    'ACCOMPANIMENT': Flexible('accompanied', 'accompanier'),
    'DEPICTIVE': Rigid('has-depictive', 'depictive'),
    'ATTRIBUTE': Rigid('has-attribute', 'attribute'),
    'ASSET': Rigid('has-asset', 'asset'),
    'COMPARISON': Rigid('compared', 'reference'),
    'CONCESSION': Rigid('asserted', 'conceded'),
    'EXPLANATION': Rigid('explained', 'explanation'),
    'PURPOSE': Rigid('has-purpose', 'purpose'),
    'LOCATION': Flexible('has-location', 'location'),
    'WRAPPING-WEARING': Flexible('worn', 'wearer'),
    'ADORNMENT-TARNISHMENT': Flexible('ornament', 'surface'),
    'HITTING': Rigid('hitting', 'hit'),
    'INGESTION': Rigid('ingested', 'transitory-location', 'ingester'),
    'EXCRETION': Rigid('excreter', 'excreted', 'transitory-location'),
    'UNANCHORED-MOTION': Rigid('in-motion', 'transitory-location'),
    'MEANS': Rigid('has-means', 'means'),
    'MESSAGE': Flexible('topic', 'content'),
    'PART-WHOLE': Flexible('part', 'whole'),
    'POSSESSION': Flexible('possessed', 'possessor'),
    'QUANTITY': Flexible('has-quantity', 'quantity'),
    'SENDING': Rigid('sent', 'sender'),
    'SEQUENCE': Flexible('follows', 'followed'),
    'CAUSATION': Rigid('result', 'causer'),
    'REACTION': Rigid('reaction', 'trigger'),
    'RESULTATIVE': Rigid('has-resultative', 'resultative'),
    'CONDITION': Rigid('has-condition', 'condition'),
    'EXCEPTION': Rigid('has-exception', 'exception'),
    'SOCIAL-RELATION': Flexible('has-social-relation', 'social-relation'),
    'TIME': Rigid('has-time', 'time'),
    'NONCOMP': Rigid('has-noncomp', 'noncomp'),
}
ASPECTS = ('INIT', 'DEINIT', 'CHANGE', 'CONTINUATION', 'PREVENTION')
MODES = ('POSSIBILITY', 'NECESSITY')
POLARITIES = ('NEG',)
FRAME_PATTERN = re.compile('(' + '|'.join(FRAMES.keys()) + ')(?:-(' +
        '|'.join(ASPECTS) + '))?(?:-(' + '|'.join(MODES) + '))?(?:-(' +
        '|'.join(POLARITIES) + '))?$')


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
        return any(v.check_noncore(role) for v in FRAMES.values())
    mtch = FRAME_PATTERN.match(frame)
    f = mtch.group(1)
    a = mtch.group(2)
    m = mtch.group(3)
    return FRAMES[f].check_core(a, m, dep)
