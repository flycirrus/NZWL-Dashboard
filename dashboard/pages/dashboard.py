import streamlit as st
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from core.data_import import lade_ergebnis_daten

st.title("Dashboard")

# ── Kernlogik ausfuehren + Daten aktualisieren ───────────────────────────────
import os
import subprocess

col_kern, col_refresh, col_ts = st.columns([1, 1, 2])
ausgabe_container = st.empty() # Container in voller Breite für Terminal-Output

with col_kern:
    if os.name == "nt":
        if st.button("Kernlogik ausfuehren"):
            skript = r"C:\nzwl-cashflow-core\src\kreditor_debitor\kreditor_debitor_logik.py"
            
            if not os.path.exists(skript):
                st.error(f"Fehler: Das Skript wurde nicht gefunden!\nPfad: `{skript}`\nBitte den Pfad auf dem Server prüfen.")
            else:
                st.info("Starte Kernlogik...")
                log_text = ""
                
                with st.spinner("Kernlogik läuft — bitte warten (Live-Ausgabe unten)..."):
                    try:
                        # Popen statt run(), um Output live zu lesen
                        process = subprocess.Popen(
                            [sys.executable, skript],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, # stderr in stdout umleiten
                            text=True,
                            bufsize=1, # Zeilenweise puffern
                            universal_newlines=True
                        )
                        
                        # Output live mitlesen und anzeigen
                        for line in process.stdout:
                            log_text += line
                            ausgabe_container.code(log_text, language="shell")
                            
                        process.wait()
                        
                        if process.returncode == 0:
                            st.success("Kernlogik erfolgreich ausgeführt!")
                            st.cache_data.clear()
                            # Optionaler kurzer Rerun nach Erfolg, oder Benutzer Button klicken lassen
                            # st.rerun() 
                        else:
                            st.error(f"Kernlogik abgebrochen mit Fehlercode {process.returncode}!")
                            
                    except Exception as e:
                        st.error(f"Systemfehler beim Ausführen: {e}")
    else:
        st.caption("Kernlogik nur auf dem Windows-Server verfügbar")

with col_refresh:
    if st.button("Daten neu laden"):
        st.cache_data.clear()
        st.rerun()

daten = lade_ergebnis_daten()
detail = daten["detail"]
nv_raw = daten.get("nicht_verknuepft", pd.DataFrame())
uebersicht = daten["uebersicht"]
statistik = daten["statistik"]

# Zeitstempel aus den Daten
zeitstempel = "unbekannt"
if not detail.empty and "aktualisiert_am" in detail.columns:
    try:
        ts = pd.to_datetime(detail["aktualisiert_am"]).max()
        zeitstempel = ts.strftime("%d.%m.%Y %H:%M")
    except Exception:
        pass

with col_ts:
    st.caption(f"Datenstand: {zeitstempel}")

if detail.empty and uebersicht.empty:
    st.warning("Keine Daten geladen. Bitte JSON-Dateien in data/input/ ablegen.")
    st.stop()

# ── Statistik-Dict ────────────────────────────────────────────────────────────
stat = {}
if not statistik.empty:
    for _, row in statistik.iterrows():
        stat[row["kennzahl"]] = row["wert"]


# ── Hilfsfunktionen ──────────────────────────────────────────────────────────
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


# ── KPI-Karten ────────────────────────────────────────────────────────────────
# Gesamtverbindlichkeiten: verknuepft + nicht verknuepft = kompletter OPOS-Master
if not detail.empty and "buchhaltungsbeleg" in detail.columns and "offener_betrag" in detail.columns:
    gesamt_betrag = (
        detail.drop_duplicates(subset=["buchhaltungsbeleg"])["offener_betrag"].sum()
    )
    if not nv_raw.empty and "offener_betrag" in nv_raw.columns:
        gesamt_betrag += nv_raw["offener_betrag"].sum()
else:
    gesamt_betrag = (
        uebersicht["offener_betrag_summe"].sum()
        if not uebersicht.empty and "offener_betrag_summe" in uebersicht.columns
        else 0.0
    )

st.markdown("### Kennzahlen")
col1, col2, col3, col4 = st.columns(4)

col1.metric(
    label="Gesamtverbindlichkeiten",
    value=fmt_mio(gesamt_betrag),
)
col1.caption("💡 Summe aller offenen Belege (OPOS), je Beleg einmalig gezählt")
col2.metric(
    label="Kreditoren (verknüpft / gesamt)",
    value=f"{stat.get('Kreditoren bis Debitor (Schritt 4)', '?')} / {stat.get('Kreditoren gesamt (OPOS)', '?')}",
)
col3.metric(
    label="Buchungsbelege (OPOS)",
    value=stat.get("Buchhaltungsbelege gesamt (OPOS)", "?"),
)
col4.metric(
    label="Match-Quote",
    value=stat.get("Gesamte Match-Quote", "?"),
)
# Beträge: verknüpft vs. nicht verknüpft
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
col4.caption(
    f"🟢 Verknüpft: **{fmt_mio(_betrag_verknuepft)}**  \n"
    f"🔴 Nicht verknüpft: **{fmt_mio(_betrag_nicht_verknuepft)}**"
)

st.markdown("---")

# ── Nicht verknüpft — Aufschlüsselung ────────────────────────────────────────
if not nv_raw.empty:
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

        nv_col_left, nv_col_right = st.columns(2)

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

            with nv_col_left:
                st.markdown("##### Anteil nach Grund")

                _farben_grund = ["#C0392B", "#E67E22", "#2980B9", "#7F8C8D", "#8E44AD"]
                donut = alt.Chart(grund_agg).mark_arc(innerRadius=60, outerRadius=120).encode(
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

                # Detail-Tabelle mit Anzahl UND Betrag
                grund_tabelle = grund_agg[["Grund", "Anzahl", "Anteil", "Betrag_fmt", "Anteil_betrag"]].copy()
                grund_tabelle.columns = ["Grund", "Belege", "Anteil Belege %", "Betrag", "Anteil Betrag %"]
                st.dataframe(grund_tabelle, use_container_width=True, hide_index=True)

        # ── 3) Branchen: Doppeltes Balkendiagramm (Anzahl + Betrag) ──────────
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

            with nv_col_right:
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
                    (bar_branche + text_betrag).properties(height=280),
                    use_container_width=True,
                )

                # Detail-Tabelle mit Anzahl UND Betrag
                branche_tabelle = branche_agg[["Branche", "Anzahl", "Anteil", "Betrag_fmt", "Anteil_betrag"]].copy()
                branche_tabelle.columns = ["Branche", "Belege", "Anteil Belege %", "Betrag", "Anteil Betrag %"]
                st.dataframe(branche_tabelle, use_container_width=True, hide_index=True)

        # ── 4) Kreuz-Tabelle: Branche × Grund ────────────────────────────────
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

        # ── 5) Top Kreditoren (nicht verknüpft) mit Betrag ────────────────────
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


# ── Faelligkeiten (Wochenansicht) ─────────────────────────────────────────────────────
# Gleiche Datenbasis wie Fälligkeiten-Seite: detail (dedupliziert) + nv_raw
df_faellig_week = pd.DataFrame()  # used later for chart filtering

if not detail.empty and "nettofaelligkeit" in detail.columns:
    st.subheader("Faelligkeiten nach Woche")
    st.caption("Klicken zum Filtern der Diagramme unten.")

    # ── Datenbasis: identisch zur Fälligkeiten-Seite ──────────────────────────
    _df = detail.copy()
    _df["nettofaelligkeit"] = pd.to_datetime(_df["nettofaelligkeit"], errors="coerce")
    _df = _df.dropna(subset=["nettofaelligkeit"])

    # Pro Buchhaltungsbeleg eine Zeile (wie in faelligkeiten.py)
    _agg_cols = {"kreditor_name": "first", "kreditor": "first",
                 "offener_betrag": "first", "nettofaelligkeit": "first"}
    _agg_cols = {k: v for k, v in _agg_cols.items() if k in _df.columns}
    belege_dash = _df.groupby("buchhaltungsbeleg", as_index=False).agg(_agg_cols)

    # Nicht-verknüpfte Positionen hinzufügen (nv_raw)
    if not nv_raw.empty and "nettofaelligkeit" in nv_raw.columns:
        _nv = nv_raw.copy()
        _nv["nettofaelligkeit"] = pd.to_datetime(_nv["nettofaelligkeit"], errors="coerce")
        _nv = _nv.dropna(subset=["nettofaelligkeit"])
        if not _nv.empty:
            for c in belege_dash.columns:
                if c not in _nv.columns:
                    _nv[c] = "" if belege_dash[c].dtype == object else 0
            belege_dash = pd.concat([belege_dash, _nv[belege_dash.columns]], ignore_index=True)

    df_faellig_week = belege_dash.copy()
    df_faellig_week_unique = belege_dash.copy()

    heute = pd.Timestamp.now().normalize()
    # ISO-Kalenderwochen-Grenzen: Montag dieser KW als Ankerpunkt
    heute_montag   = heute - pd.Timedelta(days=heute.weekday())  # Montag der aktuellen KW
    naechste_kw    = heute_montag + pd.Timedelta(weeks=1)
    in_2_wochen    = heute_montag + pd.Timedelta(weeks=2)
    in_3_wochen    = heute_montag + pd.Timedelta(weeks=3)

    df_faellig_week_unique["woche"] = df_faellig_week_unique["nettofaelligkeit"].apply(
        lambda d: "Ueberfaellig"   if d < heute_montag
        else "Diese Woche"         if d < naechste_kw
        else "Naechste Woche"      if d < in_2_wochen
        else "In 2 Wochen"         if d < in_3_wochen
        else "Spaeter"
    )

    wochen_order = ["Ueberfaellig", "Diese Woche", "Naechste Woche", "In 2 Wochen", "Spaeter"]
    wochen_summe = df_faellig_week_unique.groupby("woche")["offener_betrag"].sum().reindex(wochen_order, fill_value=0)

    if "selected_woche" not in st.session_state:
        st.session_state["selected_woche"] = "Alle"

    # 5 Wochen-Spalten + 1 schmalere Spalte rechts für "Alle"
    wk_cols = st.columns([1, 1, 1, 1, 1, 0.7])
    for i, woche in enumerate(wochen_order):
        betrag = wochen_summe.get(woche, 0)
        is_active = st.session_state["selected_woche"] == woche
        wk_cols[i].metric(woche, fmt_mio(betrag))
        btn_label = "Aktiv" if is_active else "Filtern"
        if wk_cols[i].button(btn_label, key=f"btn_{woche}", use_container_width=True):
            st.session_state["selected_woche"] = "Alle" if is_active else woche
            st.rerun()

    # "Alle" Knopf rechts — Dummy-Metric zum perfekten vertikalen Ausrichten
    wk_cols[5].metric(" ", " ")
    if wk_cols[5].button("Alle", key="btn_alle", use_container_width=True):
        st.session_state["selected_woche"] = "Alle"
        st.rerun()

    selected_woche = st.session_state["selected_woche"]

    st.markdown("---")
else:
    st.info("Faelligkeitsdaten werden nach dem naechsten Kernlogik-Lauf verfuegbar sein.")
    selected_woche = "Alle"
    st.markdown("---")



# ── Charts (gefiltert nach Wochenauswahl) ─────────────────────────────────────
if not detail.empty:
    try:
        import altair as alt

        # Basis-Datensatz je nach Wochen-Filter aufbauen
        if not df_faellig_week.empty and selected_woche != "Alle":
            belege_im_zeitraum = set(
                df_faellig_week_unique[df_faellig_week_unique["woche"] == selected_woche]["buchhaltungsbeleg"]
            )
            chart_base = detail[detail["buchhaltungsbeleg"].isin(belege_im_zeitraum)].copy()
        else:
            chart_base = detail.copy()

        # Aggregation pro Kreditor mit Endkunden-Namen für Tooltip
        grp_cols = [c for c in ["kreditor", "kreditor_name"] if c in chart_base.columns]
        if grp_cols and not chart_base.empty:
            hat_debitor = "debitor" in chart_base.columns
            hat_debitor_name = "debitor_name" in chart_base.columns

            def _namen_set(series):
                namen = set()
                for v in series.dropna():
                    for teil in str(v).split(","):
                        teil = teil.strip()
                        if teil and teil not in ("nan", "NaT", ""):
                            namen.add(teil)
                return namen

            # Betrag: pro Beleg nur einmal zaehlen (BOM-Join vervielfacht Zeilen)
            chart_belege = chart_base.drop_duplicates(subset=["buchhaltungsbeleg"])
            kred_agg = chart_belege.groupby(grp_cols, as_index=False).agg(
                offener_betrag_summe=("offener_betrag", "sum")
            )

            # Debitoren: aus allen Detail-Zeilen (verschiedene Debitoren pro Zeile)
            if hat_debitor_name:
                deb_agg = chart_base.groupby(grp_cols, as_index=False).agg(
                    anzahl_debitoren=("debitor_name", lambda x: len(_namen_set(x))),
                    endkunden_namen=("debitor_name", lambda x: ", ".join(sorted(_namen_set(x))) or "—"),
                )
                kred_agg = kred_agg.merge(deb_agg, on=grp_cols, how="left")
            elif hat_debitor:
                deb_agg = chart_base.groupby(grp_cols, as_index=False).agg(
                    anzahl_debitoren=("debitor", "nunique")
                )
                kred_agg = kred_agg.merge(deb_agg, on=grp_cols, how="left")

            kred_agg["betrag_fmt"] = kred_agg["offener_betrag_summe"].apply(fmt_mio)
        else:
            kred_agg = pd.DataFrame()

        chart_titel_suffix = f" — {selected_woche}" if selected_woche != "Alle" else ""
        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader(f"Top 10 Kreditoren nach Betrag{chart_titel_suffix}")
            if not kred_agg.empty:
                top10 = kred_agg.nlargest(10, "offener_betrag_summe").copy()
                chart = alt.Chart(top10).mark_bar(color="#1F4E79").encode(
                    x=alt.X("offener_betrag_summe:Q", title="Offener Betrag",
                             axis=alt.Axis(format=",.0f")),
                    y=alt.Y("kreditor_name:N", title="", sort="-x"),
                    tooltip=[
                        alt.Tooltip("kreditor_name:N", title="Kreditor"),
                        alt.Tooltip("betrag_fmt:N", title="Offener Betrag"),
                        alt.Tooltip("anzahl_debitoren:Q", title="Anzahl Endkunden"),
                        alt.Tooltip("endkunden_namen:N", title="Endkunden"),
                    ],
                ).properties(height=400)
                st.altair_chart(chart, use_container_width=True)
            else:
                st.info("Keine Daten für diesen Zeitraum.")

        with col_right:
            st.subheader(f"Top 10 Kreditoren nach Endkunden{chart_titel_suffix}")
            if not kred_agg.empty and "anzahl_debitoren" in kred_agg.columns:
                deb_data = kred_agg.sort_values("anzahl_debitoren", ascending=False).head(10).copy()
                chart2 = alt.Chart(deb_data).mark_bar(color="#2E75B6").encode(
                    x=alt.X("anzahl_debitoren:Q", title="Anzahl Endkunden"),
                    y=alt.Y("kreditor_name:N", title="", sort="-x"),
                    tooltip=[
                        alt.Tooltip("kreditor_name:N", title="Kreditor"),
                        alt.Tooltip("anzahl_debitoren:Q", title="Anzahl Endkunden"),
                        alt.Tooltip("endkunden_namen:N", title="Endkunden"),
                        alt.Tooltip("betrag_fmt:N", title="Offener Betrag"),
                    ],
                ).properties(height=400)
                st.altair_chart(chart2, use_container_width=True)

    except ImportError:
        st.info("Altair nicht verfuegbar — Charts uebersprungen.")

st.markdown("---")


# ── Verknuepfungsstatistik ────────────────────────────────────────────────────
st.subheader("Verknuepfungsstatistik (4-Schritt-Kette)")
if not statistik.empty:
    anzeige = statistik[["kennzahl", "wert"]].copy()
    anzeige.columns = ["Kennzahl", "Wert"]
    st.dataframe(anzeige, use_container_width=True, hide_index=True)

st.markdown("---")

# ── Kreditor-Uebersicht mit Download ─────────────────────────────────────────
st.subheader("Kreditor-Uebersicht")

if not uebersicht.empty:
    anzeige_spalten = [c for c in [
        "kreditor", "kreditor_name", "offener_betrag_summe",
        "anzahl_rohteile", "anzahl_fertigteile", "anzahl_debitoren",
        "aktualisiert_am"
    ] if c in uebersicht.columns]

    anz = uebersicht[anzeige_spalten].copy().sort_values(
        "offener_betrag_summe", ascending=False
    )

    if "aktualisiert_am" in anz.columns:
        anz["aktualisiert_am"] = pd.to_datetime(anz["aktualisiert_am"], errors="coerce").dt.strftime("%d.%m.%Y %H:%M")

    if "offener_betrag_summe" in anz.columns:
        anz["offener_betrag_summe"] = anz["offener_betrag_summe"].apply(fmt_mio)

    anz = anz.rename(columns={
        "kreditor": "Kreditor-Nr.",
        "kreditor_name": "Kreditor",
        "offener_betrag_summe": "Offener Betrag",
        "anzahl_rohteile": "Rohteile",
        "anzahl_fertigteile": "Fertigteile",
        "anzahl_debitoren": "Endkunden",
        "aktualisiert_am": "Stand",
    })
    st.dataframe(anz, use_container_width=True, hide_index=True)

    st.download_button(
        "Kreditor-Uebersicht als CSV",
        data=uebersicht.to_csv(index=False, sep=";", decimal=",").encode("utf-8"),
        file_name="kreditor_uebersicht.csv",
        mime="text/csv",
    )
