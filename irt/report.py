"""Relatorio comparativo em texto (o mesmo impresso no terminal)."""

import numpy as np

from .config import CONFIG_ORDER, TOPO_DEFS


def _fmt(x, width=8):
    return f"{x:>{width}.4f}" if not np.isnan(x) else f"{'N/A':>{width}}"


def build_report(df, topo_defs=TOPO_DEFS, order=CONFIG_ORDER):
    """Monta o comparativo Baseline -> Baseline+Ataque -> Ataque+Protecao."""
    out = []
    p = out.append
    p("=" * 100)
    p("  COMPARATIVO FINAL: Baseline -> Baseline+Ataque -> Ataque+Protecao (modelo IRT)")
    p("=" * 100)

    for topo, _ in topo_defs:
        p(f"\n  {topo}")

        # Qualidade de rede ------------------------------------------------
        p("\n  [Qualidade de Rede]")
        p(f"  {'Config':<20} {'QI':>8} {'IC95':>8} {'Cfrac':>8} {'Eprop':>8} {'Eprop_g':>8} {'Delivery':>10} {'ARF':>8} {'TII':>8}")
        p(f"  {'-'*99}")
        for lbl in order:
            sub = df[(df.config == lbl) & (df.topology == topo)]
            if sub.empty:
                continue
            qi = sub["qi_mean"].mean()
            ic95 = 1.96 * sub["qi_mean"].std() / np.sqrt(len(sub))
            cfrac = sub["connectivity_mean"].mean()
            eprop = sub["prop_eff_mean"].mean()          # Eq. (16), restrito a Cmax
            eprop_g = sub["eprop_global_mean"].mean()    # Eq. (16) sobre todo V
            dv = sub["delivery_mean"].mean()
            # ARF (Eq. 6) e TII (Eq. 5) so' fazem sentido no cenario com defesa
            if lbl == "Ataque+Protecao":
                arf_val = sub["arf_mean"].mean()
                tii_val = sub["tii_mean"].mean()
            else:
                arf_val = tii_val = np.nan
            p(f"  {lbl:<20} {qi:>8.4f} {ic95:>8.4f} {cfrac:>8.4f} {eprop:>8.4f} {_fmt(eprop_g)} {dv:>10.4f} {_fmt(arf_val)} {_fmt(tii_val)}")

        # Deteccao ---------------------------------------------------------
        p("\n  [Deteccao de Anomalias]")
        p(f"  {'Config':<20} {'Prec':>8} {'Rec':>8} {'F1':>8} {'Acc':>8} {'ROC-AUC':>8}")
        p(f"  {'-'*55}")
        for lbl in order:
            sub = df[(df.config == lbl) & (df.topology == topo)]
            if sub.empty:
                continue
            if lbl == "Baseline":
                p(f"  {lbl:<20} {'N/A':>8} {'N/A':>8} {'N/A':>8} {'N/A':>8} {'N/A':>8}")
                continue
            vals = [sub[k].mean() for k in ("precision_mean", "recall_mean", "f1_mean", "accuracy_mean", "roc_auc_mean")]
            p(f"  {lbl:<20} " + " ".join(_fmt(v) for v in vals))

        # Mecanismo dual ---------------------------------------------------
        protect_sub = df[(df.config == "Ataque+Protecao") & (df.topology == topo)]
        if not protect_sub.empty:
            p("\n  [Mecanismo Dual - Ataque+Protecao]")
            n_s1 = protect_sub["n_s1"].sum()
            n_s2 = protect_sub["n_s2"].sum()
            total = n_s1 + n_s2
            pct_s1 = 100 * n_s1 / total if total > 0 else 0
            pct_s2 = 100 * n_s2 / total if total > 0 else 0
            r1 = protect_sub["reward_s1_mean"].mean()
            r2 = protect_sub["reward_s2_mean"].mean()
            p(f"  System 1 (intuitivo):     {pct_s1:>5.1f}% dos ciclos | recompensa media {_fmt(r1)}")
            p(f"  System 2 (deliberativo):  {pct_s2:>5.1f}% dos ciclos | recompensa media {_fmt(r2)}")

    return "\n".join(out)
