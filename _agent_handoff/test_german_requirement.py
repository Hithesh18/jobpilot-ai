r"""Regression tests for the German-requirement detector (German-WRITTEN JDs are fine unless German B1+ / good/fluent is REQUIRED).
Run: python _agent_handoff/test_german_requirement.py
1 = German required (skip), 0 = OK to apply."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ats_poll as a  # noqa: E402
import auto_tailor as t  # noqa: E402

CASES = {
    "Berührungspunkte mit Test-Frameworks wie Jest und Cypress sind von Vorteil Gute Deutsch- und Englischkenntnisse in Wort und Schrift (Mindestens B2)": 1,
    "Verständnis für betriebswirtschaftliche Softwareprozesse von Vorteil Sehr gute Deutschkenntnisse und gute Englischkenntnisse": 1,
    "Deutschkenntnisse sind von Vorteil": 0,
    "Von Vorteil: gute Deutschkenntnisse": 0,
    "German is a plus": 0,
    "Ein Plus sind gute Deutschkenntnisse": 0,
    "Kommunikation Sehr gute Deutsch- und Englischkenntnisse Nice to have Erfahrung": 1,
    "Dein Profil: React. Nice to have: Kotlin, gute Deutschkenntnisse": 0,
    'Sprachen: Englisch, Deutsch Ein "Plus", aber keinesfalls ein "Muss"': 0,
    "Sehr gute Deutschkenntnisse (B2+), Englischkenntnisse von Vorteil": 1,
    "C1-Deutschkenntnisse sind von Vorteil, B2-Niveau ist ausreichend (mit": 1,
    "Fluency in English is required; German is an advantage": 0,
    "Good spoken and written communication skills in German": 1,
    "Arbeitsweise Sehr gute Deutschkenntnisse Zusätzliche Pluspunkte: Erfahrung mit SAP": 1,
    "Du verfügst über Deutschkenntnisse auf mindestens B2-Niveau.": 1,
    "Gute Englischkenntnisse in Wort und Schrift runden Dein Profil ab; Deutschkenntnisse sind von Vorteil.": 0,
    "Deutsch-Kenntnisse gerne gesehen": 0,
    "Fluent in English and German": 1,
    "Excellent command of English. Knowledge of German will be considered a plus.": 0,
    "Du kommunizierst sicher auf Deutsch (mind. B2 Niveau) und Englisch": 1,
    "Aufgeschlossene Persönlichkeit und gute Kommunikationsfähigkeiten in Deutsch und Englisch Wir bieten": 1,
    "Du bewegst Dich sicher in Deutsch und Englisch": 1,
    "Wir bieten dir ein tolles Team. Deine Aufgaben: React": 0,
    "2+ years experience in web application development Full-Stack Good communication skills in both English and German": 1,
    "Good communication skills in English; German is a plus": 0,
    "vermitteln und verfügst über mindestens Deutschkenntnisse auf B2-Niveau": 1,
    "Teamorientierung Deutsch und Englisch sehr gut in Wort und Schrift Deine Chance": 1,
    "Fertigungsprozessen Gute Kenntnisse in Deutsch und Englisch Analytisches und konzeptionelles Denken": 1,
    "Du bringst fließende mündliche und schriftliche Kommunikationsfähigkeiten in Englisch und Deutsch mit und bist zu einer gelegentlichen Reisetätigkeit bereit": 1,
    "Ausgezeichnete Kommunikationsfähigkeiten in Englisch und Deutsch Zusatzleistungen": 1,
    "Ausgezeichnete Kommunikationsfähigkeiten in Englisch; Deutsch ist ein Plus": 0,
    "- Deutsch mind. auf C1-Niveau (ein sehr flüssiger, fachlicher Austausch ist notwendig)": 1,
    "* Deutschkenntnisse auf verhandlungssicherem Niveau sowie Englischkenntnisse wünschenswert": 1,
    "Du sprichst Deutsch auf muttersprachlichem Niveau und kannst dich auch auf Englisch sicher verständigen.": 1,
    "Du sprichst Deutsch fließend und Englisch gut.": 1,
    "implementiert Du beherrschst die deutsche Sprache fließend in Wort und Schrift": 1,
    "Deutsch oder Englisch Du sprichst Deutsch oder Englisch, am besten beides": 0,
    "pragmatische Software-Lösungen. Deutsch (sehr gut) und Englisch (gut) sowie ein abgeschlossenes Studium": 1,
    "im industriellen Kontext (HMI) Deutsch und Englisch in Wort und Schrift Was wir bieten": 1,
    "systematisch. - Deutsch beherrschen Sie fließend in Wort und Schrift, gute Englischkenntnisse sind von Vorteil.": 1,
    "Kommunikationsstärke und eine selbstständige Arbeitsweise Gute Deutsch- und Englischkenntnisse Wünschenswert Erfahrung mit Docker": 1,
    "Flüssige Englischkenntnisse in Wort und Schrift sind erforderlich, Deutsch ist von Vorteil.": 0,
    "teamorientierte Persönlichkeit mit strukturierter Arbeitsweise und guten Deutschkenntnissen Apply": 1,
    "Zielorientierung zeichnen Ihre Arbeitsweise aus Sie beherrschen Deutsch fließend (C2-Niveau) Folgende Kenntnisse sind ein Plus, jedoch kein Muss": 1,
    "Strukturierte, eigenständige Arbeitsweise - Gutes Deutsch, technisches Englisch ***Nice-to-have***": 1,
    "Umgang mit internen Kunden - Sehr gut Deutschkenntnisse und Grundkenntnisse in englischer Sprache": 1,
    "lernst Du gerne dazu. Deutsch und Englisch nutzt Du fließend in Projekten und Dokumentation": 1,
    "Erfahrung mit REST-APIs - Verhandlungssichere Deutschkenntnisse (C1 oder höher) **Darüber hinaus von Vorteil:** - Erfahrung": 1,
}
bad = 0
for text, exp in CASES.items():
    g = 1 if a.german_requirement(text) else 0
    g2 = 1 if any("German" in r for r in t.check_jd_dealbreakers({"title": "Frontend Developer"}, text)) else 0
    if g != exp or g2 != exp:
        bad += 1
        print(f"FAIL exp={exp} ats_poll={g} auto_tailor={g2} :: {text}")
print(f"{len(CASES) - bad}/{len(CASES)} passed")
sys.exit(1 if bad else 0)
