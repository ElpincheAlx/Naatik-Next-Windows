"""Next-owned MeCab/UniDic analysis. No OCR, HTTP, grammar/JLPT guesses or translation."""
from .i18n import tr
import json
from pathlib import Path
import shlex
import os
import signal
import sys
from .ocr import stop


def hiragana(value):
    return ''.join(chr(ord(c)-0x60) if '\u30a1' <= c <= '\u30f6' else c for c in value)


def mecab_quote(path):
    # MeCab parses double quoted options, not POSIX shell single quotes.
    value = str(path).replace('\\', '/')
    if '"' in value: raise ValueError(tr('Ruta de diccionario no válida.'))
    return '"' + value + '"'


class Analyzer:
    def __init__(self):
        import fugashi
        import unidic_lite
        # Explicit dictionary and empty system rc: never discover global MeCab config.
        self.tagger = fugashi.Tagger('-r ' + mecab_quote(os.devnull) + ' -d ' + mecab_quote(unidic_lite.DICDIR))

    def analyze(self, text):
        if not text.strip() or len(text) > 10000:
            raise ValueError(tr('Escribe entre 1 y 10 000 caracteres.'))
        tokens, cursor = [], 0
        for word in self.tagger(text):
            if len(tokens) >= 1000:
                raise ValueError(tr('Máximo 1 000 palabras por análisis; divide la frase.'))
            surface, feature = word.surface, word.feature
            start = text.find(surface, cursor)
            if start < cursor:
                raise ValueError(tr('No se pudo asociar el análisis al texto original.'))
            reading = getattr(feature, 'kana', '') or ''
            if word.is_unk or reading == '*':
                reading = ''
            base = getattr(feature, 'orthBase', '') or surface
            if base == '*': base = surface
            tokens.append(dict(surface=surface, base=base, reading=hiragana(reading),
                               pos=getattr(feature, 'pos1', '') or '', start=start, end=start+len(surface),
                               unknown=bool(word.is_unk)))
            cursor = start + len(surface)
        return dict(sentence=text, tokens=tokens, resource='Fugashi 1.5.2 / UniDic Lite 1.0.8 (UniDic 2.1.2)')


def main():
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    analyzer = None
    for line in sys.stdin:
        try:
            request = json.loads(line)
            if request['action'] != 'phrase': raise ValueError(tr('Acción desconocida.'))
            if analyzer is None: analyzer = Analyzer()
            result = analyzer.analyze(request['text'])
            print(json.dumps({'result': {'popup_generation': request['popup_generation'], 'value': result}}, ensure_ascii=False), flush=True)
        except Exception as error:
            print(json.dumps({'error': tr('Análisis no disponible: {p0}. Prepara los recursos lingüísticos de Next.', p0=f'{error}')}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
