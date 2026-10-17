This project is intended to build practice questions based on the lecture slides

## Layout

```
asset/                 lecture slides (source material)
src/common/            reusable pieces: transfer-function analysis (tf.py), Bode plots (bode.py),
                       LaTeX scaffolding + pdflatex (texdoc.py), unit formatting (units.py), MNA checker (mna.py)
src/lecture1/          Lecture 1 generator (linear network analysis)
    ladder.py          circuit model + divider-chain / Thevenin-march analysis
    draw.py            schemdraw schematics (problem, DC equivalent, AC equivalent)
    narrative.py       writes the 7-step worked solution in LaTeX (sets 1A-1C)
    narrative_1d.py    writes the 6-step reverse solution (set 1D: Bode plot -> H(s))
    problems_1a/b/c/d.py  the 18 problems of each set (6 easy, 6 medium, 6 hard)
    build.py           builds everything
    tex/               generated LaTeX + compiled PDF (one document per question type)
src/lecture2/          Lecture 2 generator (operational amplifiers)
    netlist.py         named-node netlist, exact (sympy) and numeric (MNA) solvers, ideal/finite-gain op-amps
    blocks.py          standard blocks: inverting, non-inverting, difference, summing (DC), T-network
    topo.py            circuits needing nodal analysis: ladder-inverting, ladder+buffer, Sallen-Key, MFB, loop
    kcl.py             writes the virtual-short + KCL + step-by-step elimination for any ideal op-amp netlist
    chain.py           cascades of blocks/topologies
    design.py          Bode-ready H(s) -> cascade of inverting stages with component values
    narrative2.py      Lecture-2 pipeline card and the solution writers for every set
    problems_2a..2e.py the 18 problems of each set
    build.py           builds everything
    tex/               generated LaTeX + compiled PDF
output/lecture<N>/<set>/  generated figures (.pdf for LaTeX, .png preview)
```

Sets:
- Lecture 1: 1A AC transfer functions, 1B DC+AC superposition, 1C dependent-source stages, 1D Bode plot -> H(s).
- Lecture 2: 2A ideal op-amp blocks and cascades, 2B nodal analysis (Sallen-Key, MFB, loops),
  2C filter design from a Bode plot, 2D finite gain-bandwidth, 2E slew rate.

## Build

```
pip install schemdraw sympy numpy matplotlib
cd src
python -m lecture1.build              # all sets, or e.g. python -m lecture1.build 1B 1D
python -m lecture2.build              # all sets, or e.g. python -m lecture2.build 2B
python -m lecture2.build --no-pdf     # skip the pdflatex step
```

Every answer is cross-checked during the build against an independent solve (numeric MNA with ideal or
finite-gain op-amp models; designed circuits are re-solved and must reproduce the target H(s)); a mismatch
stops the build. Each `.tex` is then compiled with `pdflatex` (MiKTeX) and the PDF is saved next to it.

## Adding a problem

Lecture 1: append a `Prob(level, items, Sine(...))` to a `problems_1*.py` file. `items` reads the circuit left
to right: `Src()`, `Series(z)`, `Shunt(z, rail=None|±V)`, `Tap('x')`, `Out()`, `VCVS(k,'x')`,
`VCCS(g,'x','down'|'up')`, with `z` = `R/C/L(name, value)` or `Ser(...)` / `Par(...)`.

Lecture 2: append a `ChainProb(level, [block, block, ...], Sine(...), nonideal=(A0, f_b))` (2A/2B/2D),
a `SlewProb(level, blocks, SR_V_per_us, f_in)` (2E) or a `BodeProb(level, m, poles_Hz, zeros_Hz, (f_ref, dB), Sine(...))`
(2C). Blocks: `Inv(zin, zf, zm=None)`, `NonInv(zg, zf, za, zb)`, `Diff(zin, zf, za, zb)`, `Sum(zin, zd, zf, Vdc)`,
`InvT(zin, za, zb, zc)`; topologies: `LadderInv`, `PiBuf`, `SallenKey`, `MFB`, `Loop` (see `topo.py`).
Values must give real poles (the build stops otherwise).
