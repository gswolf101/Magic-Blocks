"""Gera a pasta versions/ (um .md por versao + README com o indice) a partir de versoes.txt e dos textos detalhados
de versoes_detalhes.md. Rode de dentro da pasta site:  python gerar_versoes.py"""
import io
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'versions')


def read(name):
    return io.open(os.path.join(HERE, name), encoding='utf-8').read()


# ---- resumos curtos (versoes.txt): "1.0.x[ – 1.0.y]   texto" com continuacao recuada ----
entries = []
for line in read('versoes.txt').splitlines():
    m = re.match(r'^(1\.\d+\.\d+(?:\s*[–-]\s*1\.\d+\.\d+)?)\s*(.*)$', line)
    if m:
        entries.append([re.sub(r'\s*[–-]\s*', '–', m.group(1).strip()), m.group(2).strip()])
    elif entries and line.startswith(' ') and line.strip():
        entries[-1][1] += ' ' + line.strip()

# ---- textos detalhados (versoes_detalhes.md): secoes "## 1.0.x" ----
details = {}
cur = None
for line in read('versoes_detalhes.md').splitlines():
    m = re.match(r'^## (1\.\d+\.\d+)\s*$', line)
    if m:
        cur = m.group(1)
        details[cur] = []
    elif cur:
        details[cur].append(line)
details = {k: '\n'.join(v).strip() + '\n' for k, v in details.items()}

os.makedirs(OUT, exist_ok=True)
index = []
for label, summary in entries:
    name = label.replace('–', '_a_')
    body = details.get(label) or (summary + '\n' if summary else '')
    if not body.strip():
        continue
    title = 'Magic Blocks ' + label.replace('–', ' a ')
    io.open(os.path.join(OUT, name + '.md'), 'w', encoding='utf-8', newline='\n').write(
        '# ' + title + '\n\n*Forge 1.20.1*\n\n' + body)
    short = summary or body.strip().splitlines()[0].lstrip('#- *').strip()
    index.append('| [%s](%s.md) | %s |' % (label.replace('–', ' a '), name, short.replace('|', '/')))

index.reverse()   # mais nova primeiro
io.open(os.path.join(OUT, 'README.md'), 'w', encoding='utf-8', newline='\n').write(
    '# Versões do Magic Blocks\n\n'
    'Histórico de tudo o que entrou em cada versão do mod (Forge 1.20.1), da mais nova para a mais antiga.\n'
    'Algumas versões seguidas foram agrupadas quando eram ajustes da mesma novidade.\n\n'
    '| Versão | O que mudou |\n|---|---|\n' + '\n'.join(index) + '\n')
print(len(index), 'versoes em', OUT)
