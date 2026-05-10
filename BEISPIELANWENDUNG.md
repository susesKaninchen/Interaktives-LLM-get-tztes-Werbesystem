# 🚀 Beispielanwendung: Interaktives LLM-Werbesystem

Dieses Dokument zeigt dir, wie du das System in der Praxis benutzen kannst - von der Installation bis zu realen Business-Anwendungsfällen.

## 📋 Inhalt

1. [System Start & Installation](#system-start--installation)
2. [Erste Schritte](#erste-schritte)
3. [Real-Geschäftsszenarien](#real-geschäftsszenarien)
4. [API-Integration](#api-integration)
5. [Web-Benutzeroberfläche](#web-benutzeroberfläche)
6. [Testing & Validierung](#testing--validierung)
7. [Erweiterte Nutzung](#erweiterte-nutzung)

---

## 🏗️ System Start & Installation

### **Voraussetzungen:**
- Python 3.8+ installiert
- Node.js 18+ installiert
- Git Repository geklont

### **Installation:**
```bash
# 1. Repository klonen
git clone https://github.com/susesKaninchen/Interaktives-LLM-get-tztes-Werbesystem.git
cd Interaktives-LLM-get-tztes-Werbesystem

# 2. Backend Dependencies installieren
cd backend
pip install -r requirements.txt

# 3. Frontend Dependencies installieren
cd ../frontend  
npm install
```

### **System starten:**
```bash
# Backend starten (Terminal 1)
cd backend
uvicorn app.main:app --reload

# Frontend starten (Terminal 2)
cd frontend
npm run dev
```

**Zugriff:**
- Backend: http://localhost:8000
- Frontend: http://localhost:5173
- API Docs: http://localhost:8000/docs

---

## 🎯 Erste Schritte

### **1. Backend API testen:**

```bash
# Health Check
curl http://localhost:8000/health

# Qwen Modelle testen
curl -X POST http://localhost:8000/api/test-llm \
  -H "Content-Type: application/json" \
  -d '{"message": "Test message"}'
```

### **2. Frontend öffnen:**
- Öffne http://localhost:5173 im Browser
- Du solltest die Chat-Oberfläche sehen
- Beginne mit einer einfachen Nachricht

### **3. Erste Chat-Sitzung:**

```bash
# Im Frontend Chat-Feld:
"Suche nach Holzplatten Lieferanten für CNC-Bearbeitung"
```

**Das System wird:**  
✅ Den Intent erkennen (Suche)  
✅ Web-Suche durchführen  
✅ Ergebnisse in der Chat-Anzeige präsentieren  

---

## 💼 Real-Geschäftsszenarien

### **Szenario 1: Automobilzulieferer sucht Materialien**

**User-Profil:** Automobilzulieferer, 50 Mitarbeiter, München  
**Gesuch:** CNC-freundliche Holzplatten für Laserschneiden  

**Schritt-für-Schritt:**

#### **Schritt 1: Erste Suchanfrage**
```
User: "Ich bin ein Automobilzulieferer aus München. Suche nach 
      Lieferanten für CNC-freundliche Holzplatten, geeignet für
      Laserschneiden, im DACH-Raum."

System: 
- ➤ Intent: search
- ➤ Parameter: CNC-Materialien, Holzplatten, Laserschneiden, DACH
- ➤ Web-Suche: 8 relevante Lieferanten gefunden
```

#### **Schritt 2: Fortgeschrittene Details**
```
User: "Spezifikationen: 18mm Dicke, Buche oder Eiche, 
      Präzisionsqualität für Teile ≤ 2mm tolerance"

System:
- ➤ Intent: search
- ➤ Verfeinerte Suche nach Spezifikationen
- ➤ Filterung: Premium-Lieferanten mit hoher Präzision
```

#### **Schritt 3: Lieferanten-Analyse**
```
User: "Analysiere CNC Materials GmbH von den Ergebnissen"

System:
- ➤ Intent: crawl_url
- ➤ Website analysieren: cnc-materials.de
- ➤ Profil erstellt: 
   - Anbieter: CNC Materials GmbH
   - Expertise: Präzisionstechnik, 20+ Jahre
   - Produkte: Buche/Eiche Holzplatten, 16-18mm
   - Qualität: ISO 9001 zertifiziert
   - Standort: Berlin
```

#### **Schritt 4: Profil-Matching**
```
User: "Erstelle ein Profil und teste Match mit CNC Materials"

System:
- ➤ Intent: matching
- ➤ User-Profil erstellt:
   - Firma: AutoParts München
   - Branche: Automobilzulieferung
   - Anforderungen: Präzision ≤2mm, Massenproduktion
- ➤ Matching-Score: 0.85 (hoch)
- ➤ Gemeinsamkeiten: Präzisionstechnik, DACH-Region
```

#### **Schritt 5: Outreach-Generierung**
```
User: "Schreibe eine professionelle Email an CNC Materials"

System:
- ➤ Intent: outreach
- ➤ Email generiert:
   Betreff: Anfrage für CNC-freundliche Holzplatten - AutoParts München
   
   Sie sind auf der Suche nach einem zuverlässigen Partner
   für CNC-freundliche Holzplatten mit hoher Präzision...
   
   Uns interessieren besonders Ihre 18mm Buche/Eiche Holzplatten
   mit Laserschneiden-Kompatibilität für unsere Teile ≤2mm Toleranz...
   
   Wir würden gerne erste Musterrequesten für unsere
   Massenproduktion diskutieren...
```

### **Szenario 2: Start-up sucht Erstausrüstung**

**User-Profil:** Tech-Start-up, 5 Mitarbeiter, Berlin  
**Gesuch:** Erstausrüstung für Prototypen-Fertigung  

**Ablauf:**
```
User: "Wir sind ein Tech-Start-up aus Berlin, 5 Mitarbeiter. 
      Suchen Erstausrüstung für Prototypen-Fertigung: 
      3D-Drucker und CNC-Fräse zu vernünftigen Preisen."

System:
✅ Intent erkannt: search
✅ Spezifizierung: Start-up, Erstausstattung, kleine Mengen
✅ Web-Suche: 12 Anbieter für Kleinserien-Fertigung
✅ Budget-fokus: Anbieter mit Start-up-Paketen
✅ Ergebnisse: Anbieter mit speziellen Start-up-Programmen
```

### **Szenario 3: Expansion in neuen Markt**

**User-Profil:** Bestehendes Unternehmen, Expansion  
**Gesuch:** Niederländischer Markt  

**Ablauf:**
```
User: "Wir sind ein deutsches CNC-Unternehmen und wollen nach
      Niederlande expandieren. Finde potenzielle Partner
      für Zusammenarbeit."

System:
✅ Intent erkannt: search
✅ Geo-Targeting: Niederlande
✅ B2B-Fokus: Zusammenarbeit, Joint-Ventures
✅ Synergie-Suche: Deutsche Unternehmen in NL
✅ Ergebnisse: 6 potenzielle Partner identifiziert
```

---

## 🔌 API-Integration

### **Python Backend API-Nutzung:**

```python
import requests
import json

# Base URL
BASE_URL = "http://localhost:8000/api"

# 1. Neue Konversation erstellen
conversation = requests.post(f"{BASE_URL}/conversations", json={
    "title": "Materialsuche für AutoParts",
    "phase": "search"
}).json()

conversation_id = conversation["id"]
print(f"Konversation erstellt: {conversation_id}")

# 2. Nachricht senden
message = requests.post(f"{BASE_URL}/conversations/{conversation_id}/messages", json={
    "role": "user",
    "content": "Suche nach CNC-freundlichen Holzplatten"
}).json()

print(f"Nachricht gesendet: {message['id']}")

# 3. Nachrichten auflisten
messages = requests.get(f"{BASE_URL}/conversations/{conversation_id}/messages").json()
print(f"Nachrichten in Konversation: {len(messages)}")

# 4. Konversationen auflisten
all_conversations = requests.get(f"{BASE_URL}/conversations").json()
print(f"Alle Konversationen: {len(all_conversations)}")
```

### **Erweiterte API-Nutzung:**

```python
# Wissenbasis abfragen
knowledge = requests.get(f"{BASE_URL}/knowledge").json()
print(f"Knowledge Base Einträge: {len(knowledge)}")

# Template erstellen
template = requests.post(f"{BASE_URL}/templates", json={
    "name": "Email Template - Anfrage",
    "content": "Hallo {{company}}, wir interessieren uns für...",
    "description": "Standard Email für Lieferantenanfragen"
}).json()

# Matching durchführen
matching = requests.post(f"{BASE_URL}/matching", json={
    "user_profile": {
        "company": "AutoParts München",
        "requirements": ["Präzision", "DACH", "Massenproduktion"]
    },
    "company_profile": {
        "company": "CNC Materials GmbH", 
        "expertise": ["Holzplatten", "Präzision"],
        "location": "Berlin"
    }
}).json()

print(f"Matching Score: {matching['score']}")
```

---

## 🌐 Web-Benutzeroberfläche

### **Frontend-Nutzung in der Praxis:**

#### **1. Chat-Interface aufrufen:**
- Öffne http://localhost:5173
- Ladezeit: <3 Sekunden
- Oberfläche: Modernes React + Vite Design

#### **2. Chat-Anwendung:**

**Einfache Suchanfrage:**
```
Suchnachricht: "Find me premium suppliers for CNC materials"
→ Ergebnis: 8 relevante Lieferanten mit Details
→ Interaktive Karte: Klickbare Ergebnisse
→ Filter: Nach Spezifikationen filtern
```

**Komplexe Anfrage:**
```
Suchnachricht: "Ich bin ein Automobilzulieferer aus Süddeutschland.
              Suche Lieferanten für Präzisions-CNC-Teile mit
              Toleranz ≤ 0.5mm, für Massenproduktion 10k+ Stk/Monat.
              Zielmarkt: Premium-Automobilhersteller."
              
→ System-Antwort: Detaillierte Analyse
→ Priorisierte Ergebnisse: Nach Relevanz sortiert
→ Matching-Diagramm: Visualisierte Kompatibilität
```

#### **3. Feature-Interaktion:**

**A. Suchergebnis klicken:**
- Anklicken eines Lieferanten öffnet Detail-View
- Zeigt: Produkte, Spezifikationen, Kontaktinfo
- Buttons: "Profil lesen", "Outreach erstellen", "Match prüfen"

**B. Profil erstellen:**
- Klick auf "Neues Profil" in der Sidebar
- Formular: Company Details, Branchen, Spezifikationen
- Speichert für zukünftige Matching-Vorgänge

**C. Matching-Dashboard:**
- Visualisiert Kompatibilitäten zwischen Profilen
- Score-Range: 0.0 - 1.0 (Grün bei >0.7)
- Interaktive Filter: Und Strings, Steinkohlen, Or

---

## 🧪 Testing & Validierung

### **Systemtests durchführen:**

```bash
# Quick Sanity Check (2 Sekunden)
cd backend && python run_tests.py

# Spezifische Tests
python run_tests.py --e2e           # Komplette Systemtests
python run_tests.py --ui            # Selenium UI Tests
python run_tests.py --workflow      # Agent Workflows
python run_tests.py --model         # Modell-Konfiguration
python run_tests.py --llm           # LLM Integration

# Coverage Reports generieren
python run_tests.py --coverage
# Öffne htmlcov/index.html für Visualisierung
```

### **Integrative Tests:**

```bash
# API Tests
python -m pytest backend/tests/integration_tests/test_api.py -v

# E2E Selenium Tests  
python -m pytest e2e_tests/test_selenium_ui.py -v

# LLM Tests
python -m pytest e2e_tests/test_llm_integration.py -v
```

---

## ⚙️ Erweiterte Nutzung

### **1. Custom Templates erstellen:**

```python
# API Call
template = requests.post("http://localhost:8000/api/templates", json={
    "name": "Outreach - Premium Partner",
    "content": """
    Dear {{company_name}},
    
    Following our previous discussions, we would like to propose
    a premium partnership agreement for {{year}}.
    
    Highlights:
    - Joint R&D initiatives
    - Priority supply chain integration
    - Marketing collaboration
    - Revenue sharing: {{revenue_share}}%
    
    Please let us know your thoughts on this opportunity.
    
    Best regards,
    {{user_company}}
    """,
    "variables": ["company_name", "year", "revenue_share", "user_company"],
    "description": "High-value partnership proposal template"
}).json()
```

### **2. Knowledge Base erweitern:**

```python
# Neue Fachwissen hinzufügen
knowledge = requests.post("http://localhost:8000/api/knowledge", json={
    "title": "CNC-Toleranzen für Automobilindustrie",
    "content": """
    Toleranzanforderungen je nach Anwendungsfall:
    
    Strukturteile: ±0.5mm
    Präzisionsteile: ±0.1mm  
    Sicherheitsteile: ±0.02mm
    Motorenteile: ±0.005mm
    
    Diese Toleranzen gelten für Maserienproduktion
    bei Raumtemperatur 20°C ±2°C.
    """,
    "category": "technical_specifications",
    "tags": ["CNC", "Toleranzen", "Automobil", "Qualität"]
}).json()
```

### **3. Webhook-Integration:**

```python
# Webhook für externe Integration
webhook = requests.post("http://localhost:8000/api/webhooks", json={
    "url": "https://your-crm-system.com/webhook",
    "events": ["conversation_created", "match_complete", "outreach_generated"],
    "headers": {
        "Authorization": "Bearer YOUR_CRM_TOKEN"
    }
}).json()

# Automatische Updates in CRM
# ⚠️
```

### **4. Batch-Verarbeitung:**

```python
# Mehrere Suchläufe parallel
search_queries = [
    "CNC Materials Berlin",
    "Precision Parts Stuttgart", 
    "Laser Thüringen",
    "Automotive Bayern",
    "Prototyping Hamburg"
]

results = []
for query in search_queries:
    result = requests.post("http://localhost:8000/api/search", json={
        "query": query,
        "max_results": 10
    }).json()
    results.append(result)

print(f"Insgesamt {len(results)} Suchläufe abgeschlossen")
```

---

## 📈 Performance & Best Practices

### **Performance-Tipps:**

### **Frontend:**
- Lazy Loading für große Datenmengen
- Debounce Chat-Input (300ms)
- Komprimierte API-Caching
- CDN für statische Assets

### **Backend:**
- Async Processing für LLM-Anfragen
- Connection Pooling für Datenbanken
- Caching für häufige Queries
- Rate Limiting für API-Calls

### **Cache-Strategie:**

```python
# Frontend Caching
const CACHE_DURATION = 5 * 60 * 1000; // 5 Minute

async function searchWithCache(query) {
    const cacheKey = `search_${query}`;
    const cached = localStorage.getItem(cacheKey);
    
    if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
        return cached.data;
    }
    
    const result = await fetch(`/api/search?q=${query}`);
    const data = await result.json();
    
    localStorage.setItem(cacheKey, {
        data,
        timestamp: Date.now()
    });
    
    return data;
}
```

---

## 🎯 Anwendungsbeispiele

### **1. E-Mail-Marketing Automation:**

```python
# Mailing-Kampagne automatisieren
import requests
import schedule
import time

def generate_campaign_emails():
    # collects leads from system
    leads = requests.get("http://localhost:8000/api/leads").json()
    
    for lead in leads:
        # Generate personalized email
        email = requests.post("http://localhost:8000/api/outreach", json={
            "template": "email_campaign_intro",
            "recipient": lead["email"],
            "company": lead["company"],
            "personalization": lead["interests"]
        }).json()
        
        # Send via email service
        send_email_service(email["content"], lead["email"])
        print(f"Email gesendet an {lead['company']}")

# Daily at 9:00 AM
schedule.every().day.at("09:00").do(generate_campaign_emails)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### **2. Dashboard für Business Intelligence:**

```javascript
// Frontend Dashboard Component
import React, { useEffect, useState } from 'react';

const Dashboard = () => {
    const [stats, setStats] = useState(null);
    const [matches, setMatches] = useState([]);
    
    useEffect(() => {
        // Lade Dashboard-Statistiken
        fetch('/api/dashboard/stats')
            .then(res => res.json())
            .then(setStats);
        
        // Lade letzte Matching-Vorgänge
        fetch('/api/matching/recent')
            .then(res => res.json())
            .then(setMatches);
    }, []);
    
    return (
        <div className="dashboard">
            <h1>Business Intelligence Dashboard</h1>
            
            {/* Key Metrics */}
            <div className="metrics">
                <div className="metric-card">
                    <h3>Suchanfragen</h3>
                    <p className="value">{stats?.search_queries || 0}</p>
                </div>
                <div className="metric-card">
                    <h3>Matching Score</h3>
                    <p className="value">{stats?.avg_match_score || 0}</p>
                </div>
                <div className="metric-card">
                    <h3>Conversions</h3>
                    <p className="value">{stats?.conversions || 0}</p>
                </div>
            </div>
            
            {/* Recent Matching Activities */}
            <div className="recent-matches">
                <h2>Aktuelle Matchings</h2>
                {matches.map(match => (
                    <div key={match.id} className="match-item">
                        <p><strong>{match.user_company}</strong></p>
                        <p>matched with <strong>{match.supplier_company}</strong></p>
                        <p>Score: {match.score}</p>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default Dashboard;
```

---

## 🚀 System-Integration Beispiele

### **1. CRM-Integration:**

```python
class CRMIntegration:
    def __init__(self, crm_api_key):
        self.crm_api_key = crm_api_key
        self.our_system_url = "http://localhost:8000/api"
        self.crm_url = "https://api.crm-system.com"
    
    def sync_leads(self):
        # Download leads from CRM
        leads = self._get_crm_leads()
        
        # Upload to our system for matching
        for lead in leads:
            self._create_lead_in_system(lead)
    
    def sync_matches_to_crm(self, match_results):
        # Upload match results back to CRM
        for match in match_results:
            self._update_crm_lead(match)
    
    def schedule_sync(self):
        # Automated sync every hour
        while True:
            self.sync_leads()
            time.sleep(3600)
```

### **2. WhatsApp Business Integration:**

```python
import requests

def send_whatsapp_message(phone_number, supplier_name, message):
    """
    Send WhatsApp message with match results
    """
    whatsapp_api = "https://api.whatsapp.com/v1/messages"
    
    payload = {
        "to": phone_number,
        "type": "text",
        "text": {
            "body": f"""
            Neu: Potential Match für {supplier_name} gefunden!
            
            {message}
            
            Details in Dashboard verfügbar.
            """
        }
    }
    
    response = requests.post(
        whatsapp_api,
        json=payload,
        headers={"Authorization": "Bearer YOUR_WHATSAPP_TOKEN"}
    )
    
    return response.json()
```

### **3. Google Sheets Automatisierung:**

```python
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def sync_to_google_sheet(matching_results):
    """
    Sync match results to Google Sheet for Business Team
    """
    # Authorize
    scope = ['https://spreadsheets.google.com/feeds']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        'service-account.json', scope)
    )
    
    gc = gspread.authorize(credentials)
    sheet = gc.open('Matching Dashboard').sheet1
    
    # Clear old data
    sheet.clear()
    
    # Add headers
    sheet.append_row([
        'Match ID', 'User Company', 'Supplier Company',
        'Score', 'Date', 'Status'
    ])
    
    # Add matching results
    for match in matching_results:
        sheet.append_row([
            match['id'],
            match['user_company'],
            match['supplier_company'],
            match['score'],
            match['date'],
            match['status']
        ])
```

---

## 📊 Reporting & Analytics

### **Business Intelligence Dashboard:**

```python
import matplotlib.pyplot as plt
import pandas as pd

def generate_match_report():
    # Fetch match data from API
    matches = requests.get("http://localhost:8000/api/matching/all").json()
    
    # Convert to DataFrame
    df = pd.DataFrame(matches)
    
    # Create visualizations
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    
    # Score Distribution
    df['score'].hist(bins=20, ax=axes[0,0])
    axes[0,0].set_title('Match Score Distribution')
    
    # Companies per Category
    df['supplier_category'].value_counts().plot(kind='bar', ax=axes[0,1])
    axes[0,1].set_title('Companies per Category')
    
    # Timeline
    df['date'] = pd.to_datetime(df['date'])
    df.groupby('date').size().plot(ax=axes[1,0])
    axes[1,0].set_title('Matches over Time')
    
    # Status Pie Chart
    df['status'].value_counts().plot(kind='pie', ax=axes[1,1])
    axes[1,1].set_title('Match Status Distribution')
    
    plt.tight_layout()
    plt.savefig('matching_report.png')
    return 'matching_report.png'
```

---

## 🎓 Best Practices

### **1. Query-Strategien:**

**Schlecht:**
```
"Suche Lieferanten"  # zu vage
```

**Gut:**
```
"Suche nach CNC-Materialien Lieferanten in Bayern,
spezialisiert auf Präzisionsteile ≤ 0.5mm Toleranz,
für Massenproduktion >10k Stk/Monat"
```

### **2. Profil-Erstellung:**

**Schlecht:**
```
{
    "company": "AutoParts",
    "needs": "CNC"
}
```

**Gut:**
```
{
    "company_name": "AutoParts München",
    "industry": "Automotive Industry",
    "location": "München, Deutschland",
    "company_size": "50-100 Mitarbeiter",
    "products": ["Precision Components", "Laser Parts", "Safety Systems"],
    "requirements": {
        "tolerance": "≤ 0.5mm",
        "production_volume": "> 10k Stk/Monat",
        "target_market": "Premium Automotive Manufacturers"
    },
    "contact_email": "procurement@autoparts-muenchen.de"
}
```

### **3. API-Nutzung:**

**Rate Limiting:**
```python
import time
import requests

def get_matches_with_rate_limit(company_ids):
    results = []
    for company_id in company_ids:
        result = requests.get(f"/api/match/{company_id}")
        results.append(result.json())
        time.sleep(0.1)  # 10 requests per second
    return results
```

**Error Handling:**
```python
def safe_api_call(endpoint, payload, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.post(f"{BASE_URL}{endpoint}", json=payload)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)  # Exponential backoff
```

---

## 🎯 Zusammenfassung

### **Wann das System nutzen:**

✅ **Sourcing Phase:** Neue Lieferanten finden  
✅ **Qualitätssicherung:** Profil-Matching und -Validierung  
✅ **Business Development:** Gründungsphase & Expansion  
✅ **Strategic Partnerships:** Langzeitige Kooperationen  
✅ **Market Research:** Marktanalyse und Konkurrenz-Scouting  

### **Wie maximales Ergebnis erzielen:**

1. **Detaillierte Anfragen:** Präzise Spezifikationen angeben
2. **Profiling:** Genaue Unternehmensprofile erstellen
3. **Phase-Systematik:** System nach Phase nutzen (Finden → Analysieren → Matchen → Outreachen)
4. **Integration:** Mit CRM und anderen Systemen verknüpfen
5. **Optimierung:** Regelmäßige Analyse und Anpassung

### **Nächste Schritte:**

1. **System starten** → Backend & Frontend laufen
2. **Validierung** → `python run_tests.py` 
3. **Erste Anfrage** → Test-Query eingeben
4. **Profile erstellen** → Eigene Daten eintragen
5. **Matching testen** → Kompatibilität prüfen
6. **Outreach starten** → Erstkontakt generieren
7. **Integration erweitern** → CRM, WhatsApp, etc.

**DEIN INTERAKTIVES LLM-WERBESYSTEM IST BEREIT! 🚀**

**Von der ersten Suchanfrage bis zu vollautomatisierten Geschäftsprozessen - alles möglich mit diesem System!**