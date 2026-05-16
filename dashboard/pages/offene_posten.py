import streamlit as st
import sys
import pandas as pd
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from core.data_import import lade_ergebnis_daten


def _fmt_num(value: float, decimals: int = 2) -> str:
    fmt = f"{value:,.{decimals}f}"
    return fmt.replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_eur(betrag: float) -> str:
    return f"{_fmt_num(betrag, 2)} €"


def fmt_mio(betrag: float) -> str:
    abs_b = abs(betrag)
    if abs_b >= 1_000_000_000:
        return f"{_fmt_num(betrag / 1_000_000_000, 2)} Mrd. €"
    if abs_b >= 1_000_000:
        return f"{_fmt_num(betrag / 1_000_000, 2)} M€"
    if abs_b >= 1_000:
        return f"{_fmt_num(betrag / 1_000, 1)} T€"
    return fmt_eur(betrag)


st.title("Kreditor-Debitor Detail")

daten = lade_ergebnis_daten()
detail = daten["detail"]

if detail.empty:
    st.warning("Keine Detail-Daten geladen.")
    st.stop()

# ── Filter ────────────────────────────────────────────────────────────────────
st.subheader("Filter")
col1, col2, col3 = st.columns(3)

with col1:
    kred_optionen = ["Alle"] + sorted(detail["kreditor_name"].dropna().unique().tolist()) if "kreditor_name" in detail.columns else ["Alle"]
    kred_filter = st.selectbox("Kreditor", kred_optionen)

with col2:
    deb_optionen = ["Alle"] + sorted(detail["debitor_name"].dropna().unique().tolist()) if "debitor_name" in detail.columns else ["Alle"]
    deb_filter = st.selectbox("Debitor (Endkunde)", deb_optionen)

with col3:
    quelle_optionen = ["Alle"] + sorted(detail["quelle"].dropna().unique().tolist()) if "quelle" in detail.columns else ["Alle"]
    quelle_filter = st.selectbox("Quelle", quelle_optionen)

gefiltert = detail.copy()
if kred_filter != "Alle":
    gefiltert = gefiltert[gefiltert["kreditor_name"] == kred_filter]
if deb_filter != "Alle":
    gefiltert = gefiltert[gefiltert["debitor_name"] == deb_filter]
if quelle_filter != "Alle":
    gefiltert = gefiltert[gefiltert["quelle"] == quelle_filter]

# ── KPIs ──────────────────────────────────────────────────────────────────────
st.markdown("---")
c1, c2, c3, c4 = st.columns(4)

betrag = gefiltert["offener_betrag"].sum() if "offener_betrag" in gefiltert.columns else 0
belege = gefiltert["buchhaltungsbeleg"].nunique() if "buchhaltungsbeleg" in gefiltert.columns else 0

c1.metric("Buchungsbelege", f"{belege:,}")
c2.metric("Kreditoren", gefiltert["kreditor"].nunique() if "kreditor" in gefiltert.columns else 0)
c3.metric("Endkunden", gefiltert["debitor"].nunique() if "debitor" in gefiltert.columns else 0)
c4.metric("Offener Betrag", fmt_mio(betrag))

# ── Ansicht waehlen ───────────────────────────────────────────────────────────
st.markdown("---")
ansicht = st.radio("Ansicht", ["Pro Buchungsbeleg (gruppiert)", "Alle Detail-Zeilen"], horizontal=True)

if ansicht == "Pro Buchungsbeleg (gruppiert)":
    # Gruppiert: ein Eintrag pro Beleg mit zusammengefassten Infos
    if "buchhaltungsbeleg" in gefiltert.columns:
        gruppiert = gefiltert.groupby("buchhaltungsbeleg", as_index=False).agg({
            "kreditor_name": "first",
            "offener_betrag": "first",
            "rohteil": lambda x: ", ".join(sorted(set(str(v) for v in x.dropna()))),
            "bom_parent": lambda x: ", ".join(sorted(set(str(v) for v in x.dropna()))),
            "debitor_name": lambda x: ", ".join(sorted(set(str(v) for v in x.dropna()))),
        })
        gruppiert = gruppiert.sort_values("offener_betrag", ascending=False)
        gruppiert["offener_betrag_fmt"] = gruppiert["offener_betrag"].apply(fmt_mio)

        anzeige = gruppiert[["buchhaltungsbeleg", "kreditor_name", "offener_betrag_fmt",
                              "rohteil", "bom_parent", "debitor_name"]].copy()
        anzeige.columns = ["Beleg", "Kreditor", "Offener Betrag", "Rohteile", "Fertigteile", "Endkunden"]
        st.dataframe(anzeige, use_container_width=True, hide_index=True)
    else:
        st.warning("Spalte 'buchhaltungsbeleg' nicht vorhanden.")
else:
    # Alle Zeilen
    anzeige_spalten = [c for c in ["buchhaltungsbeleg", "kreditor_name", "offener_betrag",
                                    "rohteil", "bom_parent", "debitor_name", "quelle"] if c in gefiltert.columns]
    anzeige = gefiltert[anzeige_spalten].copy().sort_values("offener_betrag", ascending=False)
    if "offener_betrag" in anzeige.columns:
        anzeige["offener_betrag"] = anzeige["offener_betrag"].apply(fmt_mio)
    anzeige.columns = [c.replace("_", " ").title() for c in anzeige.columns]
    st.dataframe(anzeige, use_container_width=True, hide_index=True)

# ── Download ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.download_button(
    "Als CSV herunterladen",
    data=gefiltert.to_csv(index=False, sep=";", decimal=",").encode("utf-8"),
    file_name="kreditor_debitor_detail.csv",
    mime="text/csv",
)
