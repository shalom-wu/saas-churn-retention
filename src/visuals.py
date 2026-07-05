"""Shared plotting style so every figure in the repo looks like one family."""

import matplotlib as mpl
import matplotlib.pyplot as plt

from src.config import FIGURES_DIR, PALETTE


def apply_style() -> None:
    """Apply the project-wide matplotlib style. Call once per session."""
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Segoe UI", "Arial", "DejaVu Sans"],
        "font.size": 11,
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.titlelocation": "left",
        "axes.labelsize": 11,
        "axes.labelcolor": PALETTE["dark"],
        "axes.edgecolor": PALETTE["neutral"],
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "axes.grid.axis": "y",
        "grid.color": "#E3E7EB",
        "grid.linewidth": 0.8,
        "xtick.color": PALETTE["dark"],
        "ytick.color": PALETTE["dark"],
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
        "savefig.dpi": 200,
        "savefig.bbox": "tight",
        "legend.frameon": False,
    })


def save_fig(fig: plt.Figure, name: str) -> str:
    """Save a figure into reports/figures as a standalone PNG."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    path = FIGURES_DIR / f"{name}.png"
    fig.savefig(path)
    plt.close(fig)
    return str(path)


def annotate_bars(ax: plt.Axes, fmt: str = "{:.0%}", fontsize: int = 10,
                  padding: int = 3) -> None:
    """Write the value of each bar above/beside it (direct labelling beats
    forcing the reader to eyeball gridlines)."""
    for container in ax.containers:
        ax.bar_label(container, fmt=fmt, fontsize=fontsize,
                     padding=padding, color=PALETTE["dark"])


def add_source_note(ax: plt.Axes, text: str = "Source: Telco Customer Churn dataset (Kaggle / IBM), n=7,043") -> None:
    """Small source annotation under the plot, deck-style."""
    ax.annotate(text, xy=(0, -0.18), xycoords="axes fraction",
                fontsize=8, color=PALETTE["neutral"], ha="left")
