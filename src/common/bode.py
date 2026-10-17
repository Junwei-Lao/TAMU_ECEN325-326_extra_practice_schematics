"""Magnitude Bode plot: straight-line asymptote (what you sketch) + exact curve (for reference)."""
import math

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from .tf import f_of, f_txt
from .units import sig


def _range(tf):
    corners = [w for w, _ in tf.corners()]
    return min(corners) / 12, max(corners) * 12


def _slope_labels(ax, tf, lo, hi, all_segments=True, fontsize=9):
    flip = False
    for seg in tf.segments():
        wl = seg['w_lo'] or lo
        wh = seg['w_hi'] or hi
        wm = math.sqrt(wl * wh)
        short = seg['w_lo'] and seg['w_hi'] and wh / wl < 2.5
        if short and not all_segments:
            continue
        flip = not flip if short else False
        txt = f"{seg['slope']:+d} dB/dec" if seg['slope'] else '0 dB/dec'
        ax.annotate(txt, (f_of(wm), tf.asym_db(wm)), textcoords='offset points',
                    xytext=(0, -14 if flip else 8), ha='center', fontsize=fontsize, color='tab:blue')


def plot_bode_problem(tf, path_base, f_ref):
    """Problem figure for 'Bode plot -> H(s)': the straight-line plot only, with corner frequencies,
    slopes and ONE marked level (the asymptote value at f_ref)."""
    lo, hi = _range(tf)
    w = np.logspace(math.log10(lo), math.log10(hi), 600)
    asym = np.array([tf.asym_db(x) for x in w])
    fig, ax = plt.subplots(figsize=(6.6, 3.4))
    ax.semilogx(w / (2 * math.pi), asym, color='tab:blue', lw=2.4)
    span = max(asym.max() - asym.min(), 20)
    ax.set_ylim(asym.min() - 0.25 * span, asym.max() + 0.25 * span)
    for wc, _ in tf.corners():
        ax.axvline(f_of(wc), color='0.6', lw=0.8, ls='--')
    ticks = sorted({f_of(wc) for wc, _ in tf.corners()})
    ax.set_xticks(ticks)
    ax.set_xticklabels([f_txt(2 * math.pi * t) for t in ticks], fontsize=8, rotation=0)
    ax.minorticks_off()
    _slope_labels(ax, tf, lo, hi)
    wr = 2 * math.pi * f_ref
    L = round(tf.asym_db(wr), 9) + 0.0
    ax.plot([lo / (2 * math.pi), f_ref], [L, L], color='tab:red', lw=0.9, ls=':')
    ax.plot([f_ref], [L], 'o', color='tab:red', ms=5)
    ax.set_yticks([L])
    ax.set_yticklabels([f'{sig(L, 3)} dB'], color='tab:red')
    if not any(abs(f_ref - t) / t < 1e-6 for t in ticks):
        ax.annotate(f'{f_txt(wr)}', (f_ref, L), textcoords='offset points', xytext=(0, -14),
                    ha='center', fontsize=8, color='tab:red')
    ax.set_xlabel('f (log scale)')
    ax.set_ylabel('$|H(j\\omega)|$ (dB)')
    for sp_ in ('top', 'right'):
        ax.spines[sp_].set_visible(False)
    fig.tight_layout()
    fig.savefig(path_base + '.pdf')
    fig.savefig(path_base + '.png', dpi=130)
    plt.close(fig)


def plot_bode_factors(tf, path_base):
    """Solution figure: the asymptote of every factor, stacked, and their sum at the bottom."""
    lo, hi = _range(tf)
    w = np.logspace(math.log10(lo), math.log10(hi), 500)
    f = w / (2 * math.pi)
    facs = tf.factors
    n = len(facs) + 1
    fig, axs = plt.subplots(n, 1, figsize=(6.6, 0.95 * n + 0.6), sharex=True)
    for ax, fac in zip(axs, facs):
        y = np.array([fac.asym_db(x) for x in w])
        ax.semilogx(f, y, color='tab:green', lw=1.8)
        ax.axhline(0, color='0.8', lw=0.6)
        ax.set_yticks([])
        ax.text(1.01, 0.5, fac.mathtext(), transform=ax.transAxes, va='center', fontsize=13)
        if fac.kind == 'K':
            ax.text(0.01, 0.6, f'{sig(y[0], 3)} dB', transform=ax.transAxes, fontsize=8, color='tab:green')
        pad = max(abs(y).max(), 6) * 0.25
        ax.set_ylim(min(y.min(), 0) - pad, max(y.max(), 0) + pad)
    y = np.array([tf.asym_db(x) for x in w])
    axs[-1].semilogx(f, y, color='tab:blue', lw=2.2)
    axs[-1].set_yticks([])
    axs[-1].text(1.01, 0.5, 'sum = $|H|$', transform=axs[-1].transAxes, va='center', fontsize=10)
    for ax in axs:
        for wc, _ in tf.corners():
            ax.axvline(f_of(wc), color='0.75', lw=0.6, ls=':')
        for sp_ in ('top', 'right'):
            ax.spines[sp_].set_visible(False)
    ticks = sorted({f_of(wc) for wc, _ in tf.corners()})
    axs[-1].set_xticks(ticks)
    axs[-1].set_xticklabels([f_txt(2 * math.pi * t) for t in ticks], fontsize=7)
    axs[-1].minorticks_off()
    fig.tight_layout()
    fig.subplots_adjust(right=0.74)
    fig.savefig(path_base + '.pdf')
    fig.savefig(path_base + '.png', dpi=130)
    plt.close(fig)


def plot_bode(tf, path_base, f_in=None):
    corners = [w for w, _ in tf.corners()]
    ws = corners + ([2 * math.pi * f_in] if f_in else [])
    lo = min(ws) / 20 if ws else 1
    hi = max(ws) * 20 if ws else 1e6
    w = np.logspace(math.log10(lo), math.log10(hi), 600)
    exact = np.array([20 * math.log10(abs(tf.at(x))) for x in w])
    asym = np.array([tf.asym_db(x) for x in w])
    f = w / (2 * math.pi)

    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    ax.semilogx(f, exact, color='0.6', lw=1.2, ls='--', label='exact $|H(j\\omega)|$')
    ax.semilogx(f, asym, color='tab:blue', lw=2.2, label='asymptotic sketch')
    ymin = min(asym.min(), exact.min())
    ymax = max(asym.max(), exact.max())
    span = max(ymax - ymin, 20)
    ax.set_ylim(ymin - 0.12 * span, ymax + 0.42 * span)

    level = 0
    for k, wc in enumerate(corners):
        ax.axvline(f_of(wc), color='0.75', lw=0.8, ls=':')
        # stagger labels of corners that are close together so they do not overlap
        level = (level + 1) % 2 if k and wc / corners[k - 1] < 4 else 0
        ax.annotate(f_txt(wc), (f_of(wc), ymax + (0.33 - 0.12 * level) * span), ha='center', fontsize=8,
                    bbox=dict(boxstyle='round,pad=0.15', fc='white', ec='0.8'))
    # slope labels in the middle of each segment
    for seg in tf.segments():
        wl = seg['w_lo'] if seg['w_lo'] else lo
        wh = seg['w_hi'] if seg['w_hi'] else hi
        wm = math.sqrt(wl * wh)
        if seg['w_lo'] is None:
            wm = math.sqrt(lo * wh) if wh / lo > 4 else wh / 2
        if seg['w_hi'] is None:
            wm = math.sqrt(wl * hi) if hi / wl > 4 else wl * 2
        if seg['w_lo'] and seg['w_hi'] and wh / wl < 2.5:
            continue  # too short to label legibly; the solution's table lists it
        ax.annotate(f"{seg['slope']:+d} dB/dec" if seg['slope'] else '0 dB/dec',
                    (f_of(wm), tf.asym_db(wm)), textcoords='offset points', xytext=(0, 7),
                    ha='center', fontsize=8, color='tab:blue')
    # flat-band level(s)
    for seg in tf.segments():
        if seg['slope'] == 0:
            wl = seg['w_lo'] or lo
            wh = seg['w_hi'] or hi
            lvl = tf.asym_db(wl * 1.0001)
            ax.axhline(lvl, color='tab:blue', lw=0.6, ls=':')
            ax.annotate(f'{sig(lvl, 3)} dB', (f_of(math.sqrt(wl * wh)), lvl), textcoords='offset points',
                        xytext=(0, -12), ha='center', fontsize=8, color='tab:blue', fontweight='bold')
    if f_in:
        g = 20 * math.log10(abs(tf.at(2 * math.pi * f_in)))
        ax.plot([f_in], [g], 'o', color='tab:red', ms=5, label=f'input frequency {f_txt(2 * math.pi * f_in)}')
    ax.set_xlabel('f (Hz, log scale)')
    ax.set_ylabel('$|H(j\\omega)|$ (dB)')
    ax.grid(True, which='major', color='0.9')
    ax.legend(fontsize=7, loc='best', framealpha=0.9)
    fig.tight_layout()
    fig.savefig(path_base + '.pdf')
    fig.savefig(path_base + '.png', dpi=130)
    plt.close(fig)
