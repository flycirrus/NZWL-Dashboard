"""
Data Models Module.

Defines the structure for various entities in the dashboard according to the spec:
- User
- KreditorPosition
- Zahlung
- Kreditor
- Liquiditaet
- AuditLog

These can be implemented as Pydantic models or Python dataclasses 
(to be connected to a SQLite database in phase 2).
"""

from typing import Optional, Literal
from dataclasses import dataclass
from datetime import datetime

# Placeholders for future Phase 2 Data Classes
@dataclass
class User:
    id: str
    name: str
    email: str
    role: Literal["vorbereiter", "geschaeftsleitung", "fibu", "viewer", "admin"]
    gesellschaft: Literal["nzwl", "zwl_sk", "beide"]
    avatar: Optional[str]
    monthlyPaymentLimit: float
    createdAt: datetime

@dataclass
class KreditorPosition:
    id: str
    kreditorId: str
    kreditorName: str
    dokumentenNr: str
    gesellschaft: Literal["nzwl", "zwl_sk"]
    betrag: float
    waehrung: str = "EUR"
    faelligkeit: datetime = None
    zahlungsziel: str = ""
    skontoziel: Optional[datetime] = None
    skontobetrag: Optional[float] = None
    kategorie: str = ""
    status: Literal["ausstehend", "freigegeben", "abgelehnt", "ueberfaellig", "bezahlt"] = "ausstehend"
    materialId: Optional[str] = None
    endkundeId: Optional[str] = None
    createdAt: datetime = None

@dataclass
class Zahlung:
    id: str
    kreditorPositionId: str
    betrag: float
    typ: Literal["einzelzahlung", "sammelzahlung"]
    status: Literal["vorbereitet", "freigegeben", "ausgefuehrt", "storniert"]
    vorbereiterId: str
    geschaeftsleitungId: Optional[str] = None
    fibuConfirmedId: Optional[str] = None
    freigegebenAm: Optional[datetime] = None
    ausgefuehrtAm: Optional[datetime] = None
    kommentar: Optional[str] = None
    createdAt: datetime = None
