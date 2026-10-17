"""Shared LaTeX document scaffolding: preamble, problem/solution blocks, small helpers."""

PREAMBLE = r"""\documentclass[11pt]{article}
\usepackage[margin=2cm]{geometry}
\usepackage{amsmath,amssymb}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{array}
\usepackage{xcolor}
\usepackage[breakable]{tcolorbox}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\allowdisplaybreaks
\setlength{\parindent}{0pt}
\setlength{\parskip}{4pt}
\definecolor{stepc}{HTML}{1F4E9E}
\definecolor{ansc}{HTML}{0B6E4F}
\newcommand{\solstep}[2]{\par\medskip{\color{stepc}\textbf{Step #1 --- #2}}\par\nopagebreak}
\newtcolorbox{probbox}[1]{colback=white,colframe=black!55,fonttitle=\bfseries,title={#1}}
\newtcolorbox{ansbox}{breakable,colback=ansc!6,colframe=ansc,fonttitle=\bfseries,title={Answer}}
\newtcolorbox{cardbox}[1]{breakable,colback=stepc!4,colframe=stepc,fonttitle=\bfseries,title={#1}}
"""


def document(title, subtitle, graphicspath, body):
    return (PREAMBLE
            + '\\graphicspath{{' + graphicspath + '}}\n'
            + '\\title{' + title + '}\n\\author{' + subtitle + '}\n\\date{}\n'
            + '\\begin{document}\n\\maketitle\n' + body + '\n\\end{document}\n')


def figure(fname, width=r'0.75\linewidth', height='6cm'):
    return ('\\begin{center}\\includegraphics[width=' + width + ',height=' + height
            + ',keepaspectratio]{' + fname + '}\\end{center}\n')


def eq(body):
    return '\\[\n' + body + '\n\\]\n'


def align(lines):
    return '\\begin{align*}\n' + ' \\\\\n'.join(lines) + '\n\\end{align*}\n'


def table(header, rows, spec=None):
    spec = spec or ('c' * len(header))
    out = '\\begin{center}\\renewcommand{\\arraystretch}{1.35}\n\\begin{tabular}{' + spec + '}\n\\toprule\n'
    out += ' & '.join(header) + ' \\\\\n\\midrule\n'
    for r in rows:
        out += ' & '.join(r) + ' \\\\\n'
    out += '\\bottomrule\n\\end{tabular}\\end{center}\n'
    return out


def find_pdflatex():
    import os
    import shutil
    exe = shutil.which('pdflatex')
    if exe:
        return exe
    guess = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Programs', 'MiKTeX', 'miktex', 'bin', 'x64',
                         'pdflatex.exe')
    return guess if os.path.exists(guess) else None


def compile_pdf(tex_path):
    """Compile tex_path with pdflatex; the PDF lands next to the .tex. Aux files are removed."""
    import os
    import subprocess
    exe = find_pdflatex()
    if not exe:
        raise RuntimeError('pdflatex not found (install MiKTeX or TeX Live)')
    folder, name = os.path.split(os.path.abspath(tex_path))
    stem = os.path.splitext(name)[0]
    r = subprocess.run([exe, '-interaction=nonstopmode', '-halt-on-error', name], cwd=folder,
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    log = os.path.join(folder, stem + '.log')
    if r.returncode != 0:
        tail = open(log, encoding='utf-8', errors='replace').read()[-3000:] if os.path.exists(log) else r.stdout[-3000:]
        raise RuntimeError(f'pdflatex failed on {name}:\n{tail}')
    for ext in ('.aux', '.log', '.out'):
        p = os.path.join(folder, stem + ext)
        if os.path.exists(p):
            os.remove(p)
    return os.path.join(folder, stem + '.pdf')


def check_balanced(tex, where=''):
    """Cheap sanity checks on generated LaTeX (no compiler available here)."""
    bad = [c for c in tex if ord(c) < 32 and c not in '\n']
    if bad:  # e.g. '\f' or '\a' produced by a non-raw Python string
        raise ValueError(f'control characters {set(map(ord, bad))} {where}')
    depth = 0
    i = 0
    while i < len(tex):
        ch = tex[i]
        if ch == '\\':
            i += 2
            continue
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth < 0:
                raise ValueError(f'unbalanced }} near {tex[max(0, i - 80):i + 20]!r} {where}')
        i += 1
    if depth:
        raise ValueError(f'unbalanced braces ({depth}) {where}')
    for a, b in (('\\left', '\\right'), ('\\begin{', '\\end{')):
        if tex.count(a) != tex.count(b):
            raise ValueError(f'{a} / {b} mismatch {where}')
    import re
    if len(re.findall(r'(?<!\\)\\\[', tex)) != len(re.findall(r'(?<!\\)\\\]', tex)):
        raise ValueError(f'display math mismatch {where}')
    for para in tex.split('\n\n'):
        if len(re.findall(r'(?<!\\)\$', para)) % 2:
            raise ValueError(f'odd number of $ in paragraph {para[:120]!r} {where}')
