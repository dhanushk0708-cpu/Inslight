import io
from typing import List, Dict, Any, Optional
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np


class ReportVisualizer:
    """
    High-resolution Matplotlib Visualization Engine for Corporate PDF Reports.
    Generates publication-quality charts rendered into memory buffers.
    """

    # Corporate Executive Palette
    PRIMARY_NAVY = "#0F172A"
    ACCENT_BLUE = "#2563EB"
    EMERALD_GREEN = "#10B981"
    AMBER_ORANGE = "#F59E0B"
    PURPLE_INDIGO = "#6366F1"
    ROSE_RED = "#EF4444"
    TEAL = "#0D9488"
    BG_LIGHT = "#F8FAFC"
    GRID_COLOR = "#E2E8F0"
    PALETTE = ["#2563EB", "#10B981", "#6366F1", "#F59E0B", "#0D9488", "#EC4899", "#8B5CF6"]

    @classmethod
    def _apply_corporate_style(cls, ax: plt.Axes, title: str, xlabel: str = "", ylabel: str = ""):
        """Apply uniform corporate styling to axes."""
        ax.set_facecolor(cls.BG_LIGHT)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color(cls.GRID_COLOR)
        ax.spines["bottom"].set_color(cls.GRID_COLOR)
        ax.yaxis.grid(True, linestyle="--", linewidth=0.6, color=cls.GRID_COLOR, alpha=0.9)
        ax.xaxis.grid(False)
        ax.set_axisbelow(True)

        ax.set_title(title, fontsize=12, fontweight="bold", color=cls.PRIMARY_NAVY, pad=12, loc="left")
        if xlabel:
            ax.set_xlabel(xlabel, fontsize=9.5, fontweight="bold", color="#475569", labelpad=6)
        if ylabel:
            ax.set_ylabel(ylabel, fontsize=9.5, fontweight="bold", color="#475569", labelpad=6)
        ax.tick_params(colors="#64748B", labelsize=8.5)

    @classmethod
    def generate_revenue_trend_chart(cls, trends: List[Dict[str, Any]]) -> Optional[bytes]:
        """Generate high-res monthly revenue and profit trend line chart."""
        if not trends or len(trends) < 2:
            return None

        months = [t["month"] for t in trends]
        revenues = [t["revenue"] for t in trends]
        profits = [t["profit"] for t in trends]

        fig, ax = plt.subplots(figsize=(7.2, 2.8), dpi=220)
        fig.patch.set_facecolor("white")

        x = np.arange(len(months))
        ax.plot(x, revenues, color=cls.ACCENT_BLUE, linewidth=2.4, marker="o", markersize=4.5, label="Gross Revenue", zorder=4)
        ax.fill_between(x, revenues, color=cls.ACCENT_BLUE, alpha=0.12, zorder=2)

        has_profit = any(p > 0 for p in profits)
        if has_profit:
            ax.plot(x, profits, color=cls.EMERALD_GREEN, linewidth=2.0, linestyle="--", marker="s", markersize=4, label="Gross Profit", zorder=4)

        cls._apply_corporate_style(ax, "Monthly Revenue & Profitability Trajectory", xlabel="Reporting Period", ylabel="Turnover")

        ax.set_xticks(x)
        ax.set_xticklabels(months, rotation=35, ha="right", fontsize=8)

        # Formatter for Indian Rupees
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(cls._inr_tick_formatter))

        ax.legend(frameon=True, facecolor="white", edgecolor=cls.GRID_COLOR, fontsize=8.5, loc="upper left")
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight", dpi=220)
        plt.close(fig)
        buf.seek(0)
        return buf.getvalue()

    @classmethod
    def generate_regional_bar_chart(cls, regional: List[Dict[str, Any]]) -> Optional[bytes]:
        """Generate horizontal bar chart comparing regional revenue contribution."""
        if not regional:
            return None

        # Sort ascending for clean bottom-to-top horizontal bar chart
        sorted_reg = sorted(regional, key=lambda x: x["revenue"], reverse=False)
        names = [r["name"] for r in sorted_reg]
        revenues = [r["revenue"] for r in sorted_reg]
        shares = [r["revenue_share_pct"] for r in sorted_reg]

        fig, ax = plt.subplots(figsize=(7.2, 2.6), dpi=220)
        fig.patch.set_facecolor("white")

        y = np.arange(len(names))
        bars = ax.barh(y, revenues, color=cls.ACCENT_BLUE, height=0.55, edgecolor="none", alpha=0.92, zorder=3)

        cls._apply_corporate_style(ax, "Regional Revenue Performance & Share", xlabel="Total Revenue", ylabel="Region")
        ax.set_yticks(y)
        ax.set_yticklabels(names, fontsize=8.5, fontweight="normal")
        ax.xaxis.set_major_formatter(ticker.FuncFormatter(cls._inr_tick_formatter))
        ax.xaxis.grid(True, linestyle="--", linewidth=0.6, color=cls.GRID_COLOR, alpha=0.9)
        ax.yaxis.grid(False)

        # Direct data labels at bar ends
        max_rev = max(revenues) if revenues else 1
        for bar, share in zip(bars, shares):
            w = bar.get_width()
            ax.text(w + (max_rev * 0.02), bar.get_y() + bar.get_height() / 2, f"{share}%",
                    va="center", ha="left", fontsize=8, fontweight="bold", color=cls.PRIMARY_NAVY)

        ax.set_xlim(0, max_rev * 1.15)
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight", dpi=220)
        plt.close(fig)
        buf.seek(0)
        return buf.getvalue()

    @classmethod
    def generate_product_ranking_chart(cls, products: List[Dict[str, Any]]) -> Optional[bytes]:
        """Generate horizontal ranking of top revenue-driving products."""
        if not products:
            return None

        top = products[:8]
        sorted_prod = sorted(top, key=lambda x: x["revenue"], reverse=False)
        names = [p["name"][:18] for p in sorted_prod]
        revenues = [p["revenue"] for p in sorted_prod]

        fig, ax = plt.subplots(figsize=(7.2, 3.0), dpi=220)
        fig.patch.set_facecolor("white")

        y = np.arange(len(names))
        bars = ax.barh(y, revenues, color=cls.PURPLE_INDIGO, height=0.58, alpha=0.9, zorder=3)

        cls._apply_corporate_style(ax, "Top 8 Products by Revenue Generation", xlabel="Gross Revenue", ylabel="Product SKU")
        ax.set_yticks(y)
        ax.set_yticklabels(names, fontsize=8)
        ax.xaxis.set_major_formatter(ticker.FuncFormatter(cls._inr_tick_formatter))
        ax.xaxis.grid(True, linestyle="--", linewidth=0.6, color=cls.GRID_COLOR, alpha=0.9)
        ax.yaxis.grid(False)

        max_rev = max(revenues) if revenues else 1
        for bar, p in zip(bars, sorted_prod):
            w = bar.get_width()
            ax.text(w + (max_rev * 0.015), bar.get_y() + bar.get_height() / 2,
                    f"{cls._format_inr_short(w)} ({p['revenue_share_pct']}%)",
                    va="center", ha="left", fontsize=7.5, fontweight="bold", color=cls.PRIMARY_NAVY)

        ax.set_xlim(0, max_rev * 1.25)
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight", dpi=220)
        plt.close(fig)
        buf.seek(0)
        return buf.getvalue()

    @classmethod
    def generate_category_breakdown_chart(cls, categories: List[Dict[str, Any]]) -> Optional[bytes]:
        """Generate high-contrast donut chart for category market share."""
        if not categories:
            return None

        names = [c["name"] for c in categories]
        revenues = [c["revenue"] for c in categories]
        colors = cls.PALETTE[:len(names)]

        fig, ax = plt.subplots(figsize=(6.8, 2.6), dpi=220)
        fig.patch.set_facecolor("white")

        wedges, texts, autotexts = ax.pie(
            revenues,
            labels=None,
            autopct="%1.1f%%",
            startangle=140,
            pctdistance=0.75,
            colors=colors,
            wedgeprops=dict(width=0.45, edgecolor="white", linewidth=2.0)
        )

        for at in autotexts:
            at.set_color("white")
            at.set_fontsize(8.5)
            at.set_fontweight("bold")

        ax.legend(
            wedges,
            [f"{n} ({cls._format_inr_short(r)})" for n, r in zip(names, revenues)],
            title="Category Turnover",
            title_fontsize=8.5,
            loc="center left",
            bbox_to_anchor=(0.95, 0.5),
            fontsize=8,
            frameon=False
        )

        ax.set_title("Category Revenue Contribution", fontsize=11, fontweight="bold", color=cls.PRIMARY_NAVY, pad=10, loc="left")
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight", dpi=220)
        plt.close(fig)
        buf.seek(0)
        return buf.getvalue()

    @classmethod
    def generate_profit_margin_comparison_chart(cls, categories: List[Dict[str, Any]]) -> Optional[bytes]:
        """Generate dual-bar chart showing Revenue vs Gross Profit by Category."""
        if not categories:
            return None

        names = [c["name"] for c in categories]
        revenues = [c["revenue"] for c in categories]
        profits = [c["profit"] for c in categories]

        fig, ax = plt.subplots(figsize=(7.2, 2.7), dpi=220)
        fig.patch.set_facecolor("white")

        x = np.arange(len(names))
        width = 0.35

        ax.bar(x - width/2, revenues, width, label="Revenue", color=cls.ACCENT_BLUE, alpha=0.9, zorder=3)
        ax.bar(x + width/2, profits, width, label="Gross Profit", color=cls.EMERALD_GREEN, alpha=0.9, zorder=3)

        cls._apply_corporate_style(ax, "Category Revenue vs Profit Comparison", xlabel="Category", ylabel="Monetary Value")
        ax.set_xticks(x)
        ax.set_xticklabels(names, fontsize=8.5)
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(cls._inr_tick_formatter))
        ax.legend(frameon=True, facecolor="white", edgecolor=cls.GRID_COLOR, fontsize=8.5, loc="upper right")

        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight", dpi=220)
        plt.close(fig)
        buf.seek(0)
        return buf.getvalue()

    # ━━━━━━━━ NUMBER FORMATTING UTILS ━━━━━━━━

    @staticmethod
    def _inr_tick_formatter(val, pos=None):
        if abs(val) >= 1e7:
            return f"₹{val/1e7:.1f}Cr"
        elif abs(val) >= 1e5:
            return f"₹{val/1e5:.1f}L"
        elif abs(val) >= 1e3:
            return f"₹{val/1e3:.0f}K"
        return f"₹{val:.0f}"

    @staticmethod
    def _format_inr_short(val: float) -> str:
        if abs(val) >= 1e7:
            return f"₹{val/1e7:.2f} Cr"
        elif abs(val) >= 1e5:
            return f"₹{val/1e5:.1f} L"
        elif abs(val) >= 1e3:
            return f"₹{val/1e3:.0f} K"
        return f"₹{val:.0f}"
