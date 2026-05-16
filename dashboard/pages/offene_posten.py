import streamlit as st
import sys
import pandas as pd
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from core.data_import import lade_ergebnis_daten
from core.calculations import (
    klassifiziere_faelligkeit, ampel_zusammenfassung,
    AMPEL_ROT, AMPEL_GELB, AMPEL_GRUEN,
    FARBE_ROT, FARBE_GELB, FARBE_GRUEN,
    FARBE_ROT_BG, FARBE_GELB_BG, FARBE_GRUEN_BG,
)


def _fmt_num(value: float, decimals: int = 2) -> str:
    fmt = f"{value:,.{decimals}f}"
    return fmt.replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_eur(betrag: float) -> str:
    return f"{_fmt_num(betrag, 2)} EUR"


def fmt_mio(betrag: float) -> str:
    abs_b = abs(betrag)
    if abs_b >= 1_000_000_000:
        return f"{_fmt_num(betrag / 1_000_000_000, 2)} Mrd. EUR"
    if abs_b >= 1_000_000:
        return f"{_fmt_num(betrag / 1_000_000, 2)} M EUR"
    if abs_b >= 1_000:
        return f"{_fmt_num(betrag / 1_000, 1)} T EUR"
    return fmt_eur(betrag)


st.title("Kreditor-Debitor Detail")

daten = lade_ergebnis_daten()
detail = daten["detail"]

if detail.empty:
    st.warning("Keine Detail-Daten geladen.")
    st.stop()

# ── Ampel-KPI-Karten oben ───────────────────────────────────────────────────
if "nettofaelligkeit" in detail.columns:
    ampel = ampel_zusammenfassung(detail)

    a1, a2, a3 = st.columns(3)
    for ampel_key, farbe, farbe_bg, label, col in [
        (AMPEL_ROT, FARBE_ROT, FARBE_ROT_BG, "Ueberfaellig", a1),
        (AMPEL_GELB, FARBE_GELB, FARBE_GELB_BG, "Faellig bald", a2),
        (AMPEL_GRUEN, FARBE_GRUEN, FARBE_GRUEN_BG, "OK", a3),
    ]:
        werte = ampel[ampel_key]
        col.markdown(f"""
        <div style="
            background: {farbe_bg};
            border-left: 5px solid {farbe};
            border-radius: 8px;
            padding: 12px 16px;
            margin-bottom: 12px;
        ">
            <div style="color: #555555; font-size: 12px; font-weight: 600;">{label}</div>
            <div style="color: {farbe}; font-size: 22px; font-weight: 700;">{werte['anzahl']} Belege</div>
            <div style="color: #1A1A1A; font-size: 14px;">{fmt_mio(werte['betrag'])}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

# ── Filter ────────────────────────────────────────────────────────────────────
st.subheader("Filter")
col1, col2, col3 = st.columns(3)

with col1:
    kred_optionen = ["Alle"] + sorted(detail["kreditor_name"].dropna().unique().tolist()) if "kreditor_name" in detail.columns else ["Alle"]
    kred_filter = st.selectbox("Kreditor", kred_optionen, key="op_kred_filter")

with col2:
    deb_optionen = ["Alle"] + sorted(detail["debitor_name"].dropna().unique().tolist()) if "debitor_name" in detail.columns else ["Alle"]
    deb_filter = st.selectbox("Debitor (Endkunde)", deb_optionen, key="op_deb_filter")

with col3:
    quelle_optionen = ["Alle"] + sorted(detail["quelle"].dropna().unique().tolist()) if "quelle" in detail.columns else ["Alle"]
    quelle_filter = st.selectbox("Quelle", quelle_optionen, key="op_quelle_filter")

# Ampel-Filter
if "nettofaelligkeit" in detail.columns:
    ampel_optionen = ["Alle", AMPEL_ROT, AMPEL_GELB, AMPEL_GRUEN]
    ampel_filter = st.selectbox("Ampel-Status", ampel_optionen, key="op_ampel_filter")
else:
    ampel_filter = "Alle"

gefiltert = detail.copy()
if kred_filter != "Alle":
    gefiltert = gefiltert[gefiltert["kreditor_name"] == kred_filter]
if deb_filter != "Alle":
    gefiltert = gefiltert[gefiltert["debitor_name"] == deb_filter]
if quelle_filter != "Alle":
    gefiltert = gefiltert[gefiltert["quelle"] == quelle_filter]
if ampel_filter != "Alle" and "nettofaelligkeit" in gefiltert.columns:
    gefiltert = gefiltert.copy()
    gefiltert["_ampel"] = klassifiziere_faelligkeit(gefiltert["nettofaelligkeit"])
    gefiltert = gefiltert[gefiltert["_ampel"] == ampel_filter]
    gefiltert = gefiltert.drop(columns=["_ampel"])

# ── KPIs ──────────────────────────────────────────────────────────────────────
st.markdown("---")
c1, c2, c3, c4 = st.columns(4)

betrag = gefiltert["offener_betrag"].sum() if "offener_betrag" in gefiltert.columns else 0
belege = gefiltert["buchhaltungsbeleg"].nunique() if "buchhaltungsbeleg" in gefiltert.columns else 0

c1.metric("Buchungsbelege", f"{belege:,}")
c2.metric("Kreditoren", gefiltert["kreditor"].nunique() if "kreditor" in gefiltert.columns else 0)
c3.metric("Endkunden", gefiltert["debitor"].nunique() if "debitor" in gefiltert.columns else 0)
c4.metric("Offener Betrag", fmt_mio(betrag))

# ── Clusterauswahl ───────────────────────────────────────────────────────────
st.markdown("---")
cluster_modus = st.radio(
    "Ansicht",
    ["Alle Positionen offen", "Zusammenfassung nach Kreditor", "Pro Buchungsbeleg (gruppiert)", "Alle Detail-Zeilen"],
    horizontal=True,
    key="op_cluster_modus",
)

if cluster_modus == "Zusammenfassung nach Kreditor":
    # Collapsible Sektionen pro Kreditor
    if "kreditor_name" not in gefiltert.columns:
        st.warning("Spalte 'kreditor_name' nicht vorhanden.")
    else:
        kred_gruppen = gefiltert.groupby("kreditor_name", as_index=False).agg(
            Betrag=("offener_betrag", "sum"),
            Belege=("buchhaltungsbeleg", "nunique"),
            Endkunden=("debitor_name", lambda x: ", ".join(sorted(set(
                k.strip() for v in x.dropna() for k in str(v).split(",") if k.strip() and k.strip() != "nan"
            ))) or "—"),
        ).sort_values("Betrag", ascending=False)

        st.caption(f"{len(kred_gruppen)} Kreditoren gefunden")

        for _, kred_row in kred_gruppen.iterrows():
            kred_name = kred_row["kreditor_name"]
            kred_betrag = kred_row["Betrag"]
            kred_belege = kred_row["Belege"]

            with st.expander(f"{kred_name} — {fmt_mio(kred_betrag)} ({kred_belege} Belege)"):
                kred_detail = gefiltert[gefiltert["kreditor_name"] == kred_name].copy()

                if "buchhaltungsbeleg" in kred_detail.columns:
                    beleg_agg = kred_detail.groupby("buchhaltungsbeleg", as_index=False).agg({
                        "offener_betrag": "first",
                        "rohteil": lambda x: ", ".join(sorted(set(str(v) for v in x.dropna() if str(v) != "nan"))),
                        "bom_parent": lambda x: ", ".join(sorted(set(str(v) for v in x.dropna() if str(v) != "nan"))),
                        "debitor_name": lambda x: ", ".join(sorted(set(str(v) for v in x.dropna() if str(v) != "nan"))),
                    })

                    if "nettofaelligkeit" in kred_detail.columns:
                        faellig_first = kred_detail.groupby("buchhaltungsbeleg", as_index=False)["nettofaelligkeit"].first()
                        beleg_agg = beleg_agg.merge(faellig_first, on="buchhaltungsbeleg", how="left")
                        beleg_agg["nettofaelligkeit"] = pd.to_datetime(beleg_agg["nettofaelligkeit"], errors="coerce")
                        beleg_agg = beleg_agg.sort_values("nettofaelligkeit")
                        beleg_agg["nettofaelligkeit"] = beleg_agg["nettofaelligkeit"].dt.strftime("%d.%m.%Y")

                    beleg_agg["offener_betrag"] = beleg_agg["offener_betrag"].apply(fmt_eur)

                    display_cols = [c for c in ["buchhaltungsbeleg", "offener_betrag", "nettofaelligkeit",
                                                 "rohteil", "bom_parent", "debitor_name"] if c in beleg_agg.columns]
                    anzeige = beleg_agg[display_cols].copy()
                    col_map = {
                        "buchhaltungsbeleg": "Beleg",
                        "offener_betrag": "Betrag",
                        "nettofaelligkeit": "Faellig am",
                        "rohteil": "Rohteile",
                        "bom_parent": "Fertigteile",
                        "debitor_name": "Endkunden",
                    }
                    anzeige = anzeige.rename(columns=col_map)
                    st.dataframe(anzeige, use_container_width=True, hide_index=True)

                st.caption(f"Endkunden: {kred_row['Endkunden']}")

elif cluster_modus == "Alle Positionen offen":
    # Alle Belege flach mit Ampel-Indikator
    if "buchhaltungsbeleg" in gefiltert.columns:
        beleg_flat = gefiltert.groupby("buchhaltungsbeleg", as_index=False).agg({
            "kreditor_name": "first",
            "offener_betrag": "first",
            "rohteil": lambda x: ", ".join(sorted(set(str(v) for v in x.dropna() if str(v) != "nan"))),
            "bom_parent": lambda x: ", ".join(sorted(set(str(v) for v in x.dropna() if str(v) != "nan"))),
            "debitor_name": lambda x: ", ".join(sorted(set(str(v) for v in x.dropna() if str(v) != "nan"))),
        })

        if "nettofaelligkeit" in gefiltert.columns:
            faellig_first = gefiltert.groupby("buchhaltungsbeleg", as_index=False)["nettofaelligkeit"].first()
            beleg_flat = beleg_flat.merge(faellig_first, on="buchhaltungsbeleg", how="left")
            beleg_flat["nettofaelligkeit"] = pd.to_datetime(beleg_flat["nettofaelligkeit"], errors="coerce")
            beleg_flat["ampel_status"] = klassifiziere_faelligkeit(beleg_flat["nettofaelligkeit"])
            beleg_flat = beleg_flat.sort_values("nettofaelligkeit")
            beleg_flat["nettofaelligkeit"] = beleg_flat["nettofaelligkeit"].dt.strftime("%d.%m.%Y")
        else:
            beleg_flat["ampel_status"] = "—"

        beleg_flat["offener_betrag_fmt"] = beleg_flat["offener_betrag"].apply(fmt_eur)
        beleg_flat = beleg_flat.sort_values("offener_betrag", ascending=False)

        display_cols = ["ampel_status"] + [c for c in ["buchhaltungsbeleg", "kreditor_name", "offener_betrag_fmt",
                                                         "nettofaelligkeit", "rohteil", "bom_parent", "debitor_name"]
                                            if c in beleg_flat.columns]
        anzeige = beleg_flat[display_cols].copy()
        col_map = {
            "ampel_status": "Status",
            "buchhaltungsbeleg": "Beleg",
            "kreditor_name": "Kreditor",
            "offener_betrag_fmt": "Offener Betrag",
            "nettofaelligkeit": "Faellig am",
            "rohteil": "Rohteile",
            "bom_parent": "Fertigteile",
            "debitor_name": "Endkunden",
        }
        anzeige = anzeige.rename(columns=col_map)
        st.dataframe(anzeige, use_container_width=True, hide_index=True)
    else:
        st.warning("Spalte 'buchhaltungsbeleg' nicht vorhanden.")

elif cluster_modus == "Pro Buchungsbeleg (gruppiert)":
    if "buchhaltungsbeleg" in gefiltert.columns:
        gruppiert = gefiltert.groupby("buchhaltungsbeleg", as_index=False).agg({
            "kreditor_name": "first",
            "offener_betrag": "first",
            "rohteil": lambda x: ", ".join(sorted(set(str(v) for v in x.dropna() if str(v) != "nan"))),
            "bom_parent": lambda x: ", ".join(sorted(set(str(v) for v in x.dropna() if str(v) != "nan"))),
            "debitor_name": lambda x: ", ".join(sorted(set(str(v) for v in x.dropna() if str(v) != "nan"))),
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
    # Alle Detail-Zeilen
    anzeige_spalten = [c for c in ["buchhaltungsbeleg", "kreditor_name", "offener_betrag",
                                    "rohteil", "bom_parent", "debitor_name", "quelle"] if c in gefiltert.columns]
    anzeige = gefiltert[anzeige_spalten].copy().sort_values("offener_betrag", ascending=False)
    if "offener_betrag" in anzeige.columns:
        anzeige["offener_betrag"] = anzeige["offener_betrag"].apply(fmt_mio)
    anzeige.columns = [c.replace("_", " ").title() for c in anzeige.columns]
    st.dataframe(anzeige, use_container_width=True, hide_index=True)

# ── Download ─────────────────────────────────────────────────────────────────
st.markdown("---")
st.download_button(
    "Als CSV herunterladen",
    data=gefiltert.to_csv(index=False, sep=";", decimal=",").encode("utf-8"),
    file_name="kreditor_debitor_detail.csv",
    mime="text/csv",
)
