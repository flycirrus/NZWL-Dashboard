import streamlit as st
import pandas as pd

st.title("Berichte & Revisionsprotokoll")

st.markdown("""
### Revisionsprotokoll (Audit Log)
Hier werden sämtliche Änderungen an Zahlungsstatus revisionssicher über die Session geloggt.
""")

if "audit_log" in st.session_state and len(st.session_state.audit_log) > 0:
    audit_df = pd.DataFrame(st.session_state.audit_log)
    st.dataframe(audit_df.sort_values(by="Zeitpunkt", ascending=False), use_container_width=True)
else:
    st.info("Bisher keine Aktionen protokolliert. Bitte logge dich als Vorbereiter/Geschäftsleitung ein und nimm Freigaben in 'Zahlungsplanung' vor.")

st.divider()

st.subheader("Wochen- und Monatsreport Export")
st.button("Als Excel & PDF Exportieren (Demo-Funktion, erfordert Phase 2 Export-Logik)")
