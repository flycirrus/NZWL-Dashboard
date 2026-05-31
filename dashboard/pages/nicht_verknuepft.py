import streamlit as st
import sys
import pandas as pd
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from core.data_import import lade_ergebnis_daten

# Helper formatting functions
def _fmt_num(value: float, decimals: int = 2) -> str:
    """Zahl auf Deutsch formatieren (Punkt = Tausender, Komma = Dezimal)."""
    fmt = f"{value:,.{decimals}f}"
    return fmt.replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_eur(betrag: float) -> str:
    return f"{_fmt_num(betrag, 2)} €"


def fmt_mio(betrag: float) -> str:
    """Kompakte EUR-Darstellung: Mrd.€ / M€ / T€."""
    abs_b = abs(betrag)
    if abs_b >= 1_000_000_000:
        return f"{_fmt_num(betrag / 1_000_000_000, 2)} Mrd. €"
    if abs_b >= 1_000_000:
        return f"{_fmt_num(betrag / 1_000_000, 2)} M€"
    if abs_b >= 1_000:
        return f"{_fmt_num(betrag / 1_000, 1)} T€"
    return fmt_eur(betrag)


st.title("Nicht verknüpfte Belege")

daten = lade_ergebnis_daten()
detail = daten["detail"]
nv_raw = daten.get("nicht_verknuepft", pd.DataFrame())
statistik = daten["statistik"]

if nv_raw.empty:
    st.warning("Keine Daten geladen. Bitte JSON-Dateien in data/input/ ablegen.")
    st.stop()

# ── Statistik-Dict ────────────────────────────────────────────────────────────
stat = {}
if not statistik.empty:
    for _, row in statistik.iterrows():
        stat[row["kennzahl"]] = row["wert"]

# calculate verknüpft / nicht verknüpft betrag:
_betrag_verknuepft = (
    detail.drop_duplicates(subset=["buchhaltungsbeleg"])["offener_betrag"].sum()
    if not detail.empty and "buchhaltungsbeleg" in detail.columns and "offener_betrag" in detail.columns
    else 0.0
)
_betrag_nicht_verknuepft = (
    nv_raw["offener_betrag"].sum()
    if not nv_raw.empty and "offener_betrag" in nv_raw.columns
    else 0.0
)

match_quote = stat.get("Gesamte Match-Quote", "?")

# Highlight summary banner as requested by the user
st.info(f"**Matchquote {match_quote}** · davon verknüpft: **{fmt_mio(_betrag_verknuepft)}** und nicht verknüpft: **{fmt_mio(_betrag_nicht_verknuepft)}**")

# ── Nicht verknüpft — Aufschlüsselung ────────────────────────────────────────
st.subheader("Nicht verknüpft — Aufschlüsselung")
st.caption(
    f"Von {stat.get('Buchhaltungsbelege gesamt (OPOS)', '?')} Belegen konnten "
    f"**{len(nv_raw)}** nicht bis zum Endkunden verknüpft werden. "
    f"Hier die Gründe und Branchen-Verteilung."
)

try:
    import altair as alt

    _nv = nv_raw.copy()
    _grund_col = "grund" if "grund" in _nv.columns else None
    _branche_col = "branche" if "branche" in _nv.columns else None
    _betrag_col = "offener_betrag" if "offener_betrag" in _nv.columns else None

    col_chart_left, col_chart_right = st.columns(2)
    col_tbl_left, col_tbl_right = st.columns(2)

    # ── 1) Donut-Chart nach Grund (Anzahl + Betrag als Label) ────────────
    if _grund_col and _betrag_col:
        grund_agg = _nv.groupby(_grund_col).agg(
            Anzahl=(_grund_col, "count"),
            Betrag=(_betrag_col, "sum"),
        ).reset_index()
        grund_agg.columns = ["Grund", "Anzahl", "Betrag"]
        grund_agg = grund_agg.sort_values("Anzahl", ascending=False)
        grund_agg["Anteil"] = (grund_agg["Anzahl"] / grund_agg["Anzahl"].sum() * 100).round(1)
        grund_agg["Betrag_fmt"] = grund_agg["Betrag"].apply(fmt_mio)
        grund_agg["Anteil_betrag"] = (
            grund_agg["Betrag"].abs() / grund_agg["Betrag"].abs().sum() * 100
        ).round(1)
        grund_agg["Donut_Label"] = grund_agg.apply(
            lambda r: f"{int(r['Anzahl'])} Belege\n{r['Betrag_fmt']}", axis=1
        )

        with col_chart_left:
            st.markdown("##### Anteil nach Grund")

            _farben_grund = ["#C0392B", "#E67E22", "#2980B9", "#7F8C8D", "#8E44AD"]
            donut = alt.Chart(grund_agg).mark_arc(innerRadius=55, outerRadius=95).encode(
                theta=alt.Theta("Anzahl:Q"),
                color=alt.Color(
                    "Grund:N",
                    scale=alt.Scale(range=_farben_grund[:len(grund_agg)]),
                    legend=alt.Legend(title="Grund", orient="bottom"),
                ),
                tooltip=[
                    alt.Tooltip("Grund:N", title="Grund"),
                    alt.Tooltip("Anzahl:Q", title="Anzahl Belege"),
                    alt.Tooltip("Anteil:Q", title="Anteil Belege %", format=".1f"),
                    alt.Tooltip("Betrag_fmt:N", title="Betrag EUR"),
                    alt.Tooltip("Anteil_betrag:Q", title="Anteil Betrag %", format=".1f"),
                ],
            ).properties(height=280)

            text_center = alt.Chart(pd.DataFrame([{"text": f"{len(_nv)} Belege"}])).mark_text(
                fontSize=16, fontWeight="bold", color="#555"
            ).encode(text="text:N")

            st.altair_chart(donut + text_center, use_container_width=True)

        with col_tbl_left:
            # Detail-Tabelle mit Anzahl UND Betrag
            grund_tabelle = grund_agg[["Grund", "Anzahl", "Anteil", "Betrag_fmt", "Anteil_betrag"]].copy()
            grund_tabelle.columns = ["Grund", "Belege", "Anteil Belege %", "Betrag", "Anteil Betrag %"]
            st.dataframe(grund_tabelle, use_container_width=True, hide_index=True)

    # ── 2) Branchen: Doppeltes Balkendiagramm (Anzahl + Betrag) ──────────
    if _branche_col and _betrag_col:
        branche_agg = _nv.groupby(_branche_col).agg(
            Anzahl=(_branche_col, "count"),
            Betrag=(_betrag_col, "sum"),
        ).reset_index()
        branche_agg.columns = ["Branche", "Anzahl", "Betrag"]
        branche_agg["Branche"] = branche_agg["Branche"].fillna("Unbekannt")
        branche_agg.loc[branche_agg["Branche"].isin(["nan", ""]), "Branche"] = "Unbekannt"
        branche_agg = branche_agg.sort_values("Anzahl", ascending=False)
        branche_agg["Anteil"] = (branche_agg["Anzahl"] / branche_agg["Anzahl"].sum() * 100).round(1)
        branche_agg["Betrag_fmt"] = branche_agg["Betrag"].apply(fmt_mio)
        branche_agg["Anteil_betrag"] = (
            branche_agg["Betrag"].abs() / branche_agg["Betrag"].abs().sum() * 100
        ).round(1)

        with col_chart_right:
            st.markdown("##### Verteilung nach Branche")

            # Anzahl-Balken (dunkelblau) + Betrag als Text rechts am Balken
            _farben_branche = ["#1F4E79", "#2E75B6", "#4BACC6", "#F4B183", "#C55A11", "#A5A5A5", "#7030A0", "#548235"]
            _sort_order = branche_agg["Branche"].tolist()

            bar_branche = alt.Chart(branche_agg).mark_bar(cornerRadiusEnd=4).encode(
                x=alt.X("Anzahl:Q", title="Anzahl Belege"),
                y=alt.Y("Branche:N", title="", sort=_sort_order),
                color=alt.Color(
                    "Branche:N",
                    scale=alt.Scale(range=_farben_branche[:len(branche_agg)]),
                    legend=None,
                ),
                tooltip=[
                    alt.Tooltip("Branche:N", title="Branche"),
                    alt.Tooltip("Anzahl:Q", title="Anzahl Belege"),
                    alt.Tooltip("Anteil:Q", title="Anteil Belege %", format=".1f"),
                    alt.Tooltip("Betrag_fmt:N", title="Betrag EUR"),
                    alt.Tooltip("Anteil_betrag:Q", title="Anteil Betrag %", format=".1f"),
                ],
            )

            # Betrag als Text rechts neben dem Balken
            text_betrag = alt.Chart(branche_agg).mark_text(
                align="left", dx=4, fontSize=11, color="#666"
            ).encode(
                x=alt.X("Anzahl:Q"),
                y=alt.Y("Branche:N", sort=_sort_order),
                text=alt.Text("Betrag_fmt:N"),
            )

            st.altair_chart(
                (bar_branche + text_betrag).properties(
                    height=280,
                    padding={"top": 25, "bottom": 10, "left": 10, "right": 50}
                ),
                use_container_width=True,
            )

        with col_tbl_right:
            # Detail-Tabelle mit Anzahl UND Betrag
            branche_tabelle = branche_agg[["Branche", "Anzahl", "Anteil", "Betrag_fmt", "Anteil_betrag"]].copy()
            branche_tabelle.columns = ["Branche", "Belege", "Anteil Belege %", "Betrag", "Anteil Betrag %"]
            st.dataframe(branche_tabelle, use_container_width=True, hide_index=True)

    # ── 3) Kreuz-Tabelle: Branche × Grund ────────────────────────────────
    if _grund_col and _branche_col and _betrag_col:
        st.markdown("##### Kreuz-Aufschlüsselung: Branche × Grund")
        st.caption("Zeigt pro Branche, welche Gründe wie oft vorkommen und welcher Betrag betroffen ist.")

        # Anzahl-Pivot
        kreuz_anz = _nv.groupby([_branche_col, _grund_col]).size().reset_index(name="Anzahl")
        kreuz_betrag = _nv.groupby([_branche_col, _grund_col])[_betrag_col].sum().reset_index(name="Betrag")
        kreuz = kreuz_anz.merge(kreuz_betrag, on=[_branche_col, _grund_col])

        # Formatierung: "Anzahl (Betrag)"
        kreuz["Wert"] = kreuz.apply(
            lambda r: f"{int(r['Anzahl'])}× | {fmt_mio(r['Betrag'])}", axis=1
        )

        kreuz_pivot = kreuz.pivot_table(
            index=_branche_col, columns=_grund_col, values="Wert", aggfunc="first", fill_value="—"
        ).reset_index()
        kreuz_pivot.columns.name = None

        # Bereinigung
        kreuz_pivot[_branche_col] = kreuz_pivot[_branche_col].replace({"nan": "Unbekannt", "": "Unbekannt"})
        kreuz_pivot = kreuz_pivot.rename(columns={_branche_col: "Branche"})

        # Gesamtsumme pro Branche
        branche_total = _nv.groupby(_branche_col).agg(
            Gesamt_Belege=(_branche_col, "count"),
            Gesamt_Betrag=(_betrag_col, "sum"),
        ).reset_index()
        branche_total[_branche_col] = branche_total[_branche_col].replace({"nan": "Unbekannt", "": "Unbekannt"})
        branche_total["Gesamt"] = branche_total.apply(
            lambda r: f"{int(r['Gesamt_Belege'])}× | {fmt_mio(r['Gesamt_Betrag'])}", axis=1
        )
        kreuz_pivot = kreuz_pivot.merge(
            branche_total[[_branche_col, "Gesamt"]],
            left_on="Branche", right_on=_branche_col, how="left"
        )
        if _branche_col in kreuz_pivot.columns and _branche_col != "Branche":
            kreuz_pivot = kreuz_pivot.drop(columns=[_branche_col])

        st.dataframe(kreuz_pivot, use_container_width=True, hide_index=True)

    # ── 4) Top Kreditoren (nicht verknüpft) mit Betrag ────────────────────
    _kred_name_col = "kreditor_name" if "kreditor_name" in _nv.columns else None
    if _kred_name_col and _betrag_col:
        st.markdown("##### Top 15 Kreditoren — nicht verknüpft")
        st.caption("Sortiert nach Betrag. Zeigt pro Kreditor die Gründe und Branchen.")

        kred_nv_agg = _nv.groupby(_kred_name_col).agg(
            Belege=(_kred_name_col, "count"),
            Betrag=(_betrag_col, "sum"),
        ).reset_index()
        kred_nv_agg.columns = ["Kreditor", "Belege", "Betrag"]
        kred_nv_agg = kred_nv_agg.sort_values("Betrag", ascending=False).head(15)

        # Grund-Aufschlüsselung pro Kreditor: zeigt Anzahl + Betrag
        if _grund_col:
            # Anzahl pro Kreditor × Grund
            kred_gruende_anz = _nv.groupby([_kred_name_col, _grund_col]).size().reset_index(name="Anz")
            kred_gruende_betrag = _nv.groupby([_kred_name_col, _grund_col])[_betrag_col].sum().reset_index(name="Betr")
            kred_gruende = kred_gruende_anz.merge(kred_gruende_betrag, on=[_kred_name_col, _grund_col])
            kred_gruende["Wert"] = kred_gruende.apply(
                lambda r: f"{int(r['Anz'])}× ({fmt_mio(r['Betr'])})", axis=1
            )
            kred_gruende_pivot = kred_gruende.pivot_table(
                index=_kred_name_col, columns=_grund_col, values="Wert", aggfunc="first", fill_value="—"
            ).reset_index()
            kred_gruende_pivot.columns.name = None
            kred_nv_agg = kred_nv_agg.merge(
                kred_gruende_pivot, left_on="Kreditor", right_on=_kred_name_col, how="left"
            )
            if _kred_name_col in kred_nv_agg.columns and _kred_name_col != "Kreditor":
                kred_nv_agg = kred_nv_agg.drop(columns=[_kred_name_col])

        # Branche hinzufügen
        if _branche_col:
            kred_branchen = _nv.groupby(_kred_name_col)[_branche_col].agg(
                lambda x: ", ".join(sorted(set(str(v) for v in x.dropna() if str(v) not in ("nan", ""))))
            ).reset_index()
            kred_branchen.columns = [_kred_name_col, "Branchen"]
            kred_nv_agg = kred_nv_agg.merge(
                kred_branchen, left_on="Kreditor", right_on=_kred_name_col, how="left"
            )
            if _kred_name_col in kred_nv_agg.columns and _kred_name_col != "Kreditor":
                kred_nv_agg = kred_nv_agg.drop(columns=[_kred_name_col])

        kred_nv_agg["Betrag"] = kred_nv_agg["Betrag"].apply(fmt_mio)
        st.dataframe(kred_nv_agg, use_container_width=True, hide_index=True)

except ImportError:
    st.info("Altair nicht verfügbar — Charts übersprungen.")

st.markdown("---")
