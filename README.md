This project is intended to generate extra practice questions based on the lecture slides for TAMU ECEN 325 and potentially ECEN 326. The code is generated entirely by Claude Code, but is monitored, reviewed, and validated by a human.

## Output and Docs
All the schematics are generated and stored in the output/ folder. All the final PDF files are copied and stored in the pdf_copies/ folder for practice.


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
src/lecture3/          Lecture 3 generator (diodes)
    pwl.py             piecewise-linear engine: every ON/OFF state solved exactly (diodes: ideal or CVD; op-amps
                       closed- or open-loop), validity intervals, coverage/continuity checks, state narrative
    circuits.py        Lecture-1 ladders / Lecture-2 chains -> diode netlists; diode-after-op-amp and precision-
                       rectifier topologies; V_o(V_i) and V_o(t) plots
    rect.py            rectifiers + AC-adapter design (formulas, narrative, schematic, waveform simulation)
    smallsig.py        small-signal analysis: DC point (CVD / exponential with iteration), r_d, AC via L1/L2
    narrative3.py      Lecture-3 pipeline card and the transfer-characteristic solution writer
    problems_3a..3d.py the 18 problems of each set
    build.py           builds everything
    tex/               generated LaTeX + compiled PDF
src/lecture4/          Lecture 4 generator (bipolar junction transistors)
    bjtnet.py          column-stack circuit model (one description -> DC netlist, AC netlist, schematic)
    dc.py              DC analysis the slides' way (I_B ~ 0, V_BE, mirrors, node-by-node KCL) + exact finite-beta solve
    ac.py              small-signal analysis with the node-impedance method + exact hybrid-pi solve
    design.py          bias design: design rules + targets -> every resistor (R = dV / I), V_BE-sensitivity check
    ampdesign.py       amplifier design (one-/two-/three-stage procedures of the slides, Sample Problem 11)
    narrative4.py, narrative_design.py, narrative_amp.py   pipeline card and solution writers
    problems_4a..4e.py the 18 problems of each set
    build.py           builds everything
    tex/               generated LaTeX + compiled PDF
output/lecture<N>/<set>/  generated figures (.pdf for LaTeX, .png preview)
```

Sets:
- Lecture 1: 1A AC transfer functions, 1B DC+AC superposition, 1C dependent-source stages, 1D Bode plot -> H(s).
- Lecture 2: 2A ideal op-amp blocks and cascades, 2B nodal analysis (Sallen-Key, MFB, loops),
  2C filter design from a Bode plot, 2D finite gain-bandwidth, 2E slew rate.
- Lecture 3: 3A diode transfer characteristics, 3B op-amp circuits with diodes, 3C rectifiers and AC-adapter
  design, 3D diode small-signal analysis.
- Lecture 4: 4A BJT DC bias analysis, 4B current-mirror biasing, 4C DC bias design, 4D small-signal transfer
  functions of BJT amplifiers, 4E amplifier design (specification table -> all resistors).

## Build

```
pip install schemdraw sympy numpy matplotlib
cd src
python -m lecture1.build              # all sets, or e.g. python -m lecture1.build 1B 1D
python -m lecture2.build              # all sets, or e.g. python -m lecture2.build 2B
python -m lecture3.build              # all sets, or e.g. python -m lecture3.build 3C
python -m lecture4.build              # all sets, or e.g. python -m lecture4.build 4C 4E
python -m lecture2.build --no-pdf     # skip the pdflatex step (any lecture)
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

Lecture 4: a circuit is a list of columns, e.g.
`BJTCircuit([Col([R('R1','6k'), 'b1', R('R2','2k')], top=12, bottom=0), Col([R('R3','2.2k'), 'c1', Q('Q1','npn', base='b1'), 'e1', R('R4','1k')], top=12, bottom=0)])`
(strings name the nodes, a node used in two columns joins them, `Q(..., diode=True)` is diode-connected).
4A/4B: `DCProb(level, lambda: circuit)`. 4D: `ACProb(level, build, Sine(...))` with `build()` returning the circuit
(plus `Src`/`Load`) and its `Stage(q, 'CE'|'CB'|'CC')` list. 4C: `DCDesign(level, build(values), {Q: I_C}, {node: V},
[vre('R4'), idiv('R2', I, ...)], vce_min, idc_max)`. 4E: `AmpSpec(level, ('pnp', 'npn', 'F'), V_CC, V_o, |A_v|, R_i,
rl=..., thd=..., vo_d=..., n=..., vre=(...), av_mid=(...))`. Every design is re-analysed exactly (finite beta) during
the build and must meet its specifications.
