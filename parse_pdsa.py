import xml.etree.ElementTree as ET

_PC = {'C':0,'D':2,'E':4,'F':5,'G':7,'A':9,'B':11}

def parse_melody(xml_path):
    """MusicXML lead sheet -> (seq[(token,beats)], fifths, composer, title, beat_type).
    Одна мелодическая линия (voice 1), ties слиты, grace/chord пропущены."""
    tree = ET.parse(xml_path); root = tree.getroot()
    title = (root.findtext('.//work/work-title') or '').strip()
    composer = (root.findtext(".//identification/creator[@type='composer']") or '').strip()
    divisions = 256; fifths = 0
    seq = []
    pending_tie = False
    for note in root.iter('note'):
        # divisions/fifths могут лежать в attributes раньше — берём из ближайших <attributes>
        pass
    # divisions & fifths из первого attributes
    attr = root.find('.//attributes')
    if attr is not None:
        d = attr.findtext('divisions');  divisions = int(d) if d else 256
        f = attr.findtext('key/fifths'); fifths = int(f) if f is not None else 0
    for note in root.iter('note'):
        if note.find('grace') is not None:        # форшлаг без длительности — пропуск
            continue
        if note.find('chord') is not None:         # аккордовая нота поверх мелодии — пропуск
            continue
        voice = note.findtext('voice')
        if voice not in (None, '1'):               # только мелодия (голос 1)
            continue
        dur = note.findtext('duration')
        beats = (int(dur)/divisions) if dur else 0
        if beats <= 0:
            continue
        if note.find('rest') is not None:
            seq.append(['R', beats]); pending_tie = False; continue
        p = note.find('pitch')
        if p is None:
            continue
        step = p.findtext('step'); octave = int(p.findtext('octave'))
        alter = int(p.findtext('alter') or 0)
        acc = '#'*alter if alter > 0 else 'b'*(-alter)
        token = f"{step}{acc}{octave}"
        # tie: если предыдущая нота была tie-start и эта tie-stop той же высоты — слить
        ties = [t.get('type') for t in note.findall('tie')]
        if pending_tie and seq and seq[-1][0] == token:
            seq[-1][1] += beats
        else:
            seq.append([token, beats])
        pending_tie = ('start' in ties)
    return [tuple(s) for s in seq], fifths, composer, title

if __name__ == '__main__':
    import sys
    seq, fifths, comp, title = parse_melody(sys.argv[1])
    print(f"title={title!r} composer={comp!r} fifths={fifths} notes={len(seq)}")
    print(seq[:24])
