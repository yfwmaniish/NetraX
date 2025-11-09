import sqlite3
import os
from uuid import uuid4

# ✅ Define database path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'decimal_scraped_data.db')


def initialize_database():
    """Create the database and scraped_data table if not exists."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # ✅ Create table (if doesn't exist) with AI workflow columns
    c.execute('''
        CREATE TABLE IF NOT EXISTS scraped_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT,
            title TEXT,
            matched_keywords TEXT,
            run_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            named_entities TEXT DEFAULT '',
            ai_classification TEXT DEFAULT NULL,
            leak_severity TEXT DEFAULT NULL,
            ai_confidence REAL DEFAULT 0.0,
            threat_score REAL DEFAULT 0.0,
            ai_summary TEXT DEFAULT NULL,
            processed_at TIMESTAMP DEFAULT NULL,
            detection_method TEXT DEFAULT 'regex',
            local_detection_results TEXT DEFAULT NULL,
            gemini_detection_results TEXT DEFAULT NULL
        )
    ''')

    # 🛠 Ensure all required columns are present (backward compatibility)
    c.execute("PRAGMA table_info(scraped_data)")
    columns = [col[1] for col in c.fetchall()]

    # Legacy columns
    if 'named_entities' not in columns:
        print("🔧 Adding missing 'named_entities' column...")
        c.execute("ALTER TABLE scraped_data ADD COLUMN named_entities TEXT DEFAULT ''")

    # New AI workflow columns
    if 'ai_classification' not in columns:
        print("🔧 Adding missing 'ai_classification' column...")
        c.execute("ALTER TABLE scraped_data ADD COLUMN ai_classification TEXT DEFAULT NULL")
    
    if 'leak_severity' not in columns:
        print("🔧 Adding missing 'leak_severity' column...")
        c.execute("ALTER TABLE scraped_data ADD COLUMN leak_severity TEXT DEFAULT NULL")
    
    if 'ai_confidence' not in columns:
        print("🔧 Adding missing 'ai_confidence' column...")
        c.execute("ALTER TABLE scraped_data ADD COLUMN ai_confidence REAL DEFAULT 0.0")

    if 'threat_score' not in columns:
        print("🔧 Adding missing 'threat_score' column...")
        c.execute("ALTER TABLE scraped_data ADD COLUMN threat_score REAL DEFAULT 0.0")
    
    if 'ai_summary' not in columns:
        print("🔧 Adding missing 'ai_summary' column...")
        c.execute("ALTER TABLE scraped_data ADD COLUMN ai_summary TEXT DEFAULT NULL")
    
    if 'processed_at' not in columns:
        print("🔧 Adding missing 'processed_at' column...")
        c.execute("ALTER TABLE scraped_data ADD COLUMN processed_at TIMESTAMP DEFAULT NULL")
    
    if 'detection_method' not in columns:
        print("🔧 Adding missing 'detection_method' column...")
        c.execute("ALTER TABLE scraped_data ADD COLUMN detection_method TEXT DEFAULT 'regex'")
    
    if 'local_detection_results' not in columns:
        print("🔧 Adding missing 'local_detection_results' column...")
        c.execute("ALTER TABLE scraped_data ADD COLUMN local_detection_results TEXT DEFAULT NULL")
    
    if 'gemini_detection_results' not in columns:
        print("🔧 Adding missing 'gemini_detection_results' column...")
        c.execute("ALTER TABLE scraped_data ADD COLUMN gemini_detection_results TEXT DEFAULT NULL")

    # Index to speed up duplicate checks by URL
    c.execute("CREATE INDEX IF NOT EXISTS idx_scraped_url ON scraped_data(url)")

    conn.commit()
    conn.close()
    print("✅ Database initialized with AI workflow columns.")


def insert_data(url, title, matched_keywords, run_id, named_entities="", 
                ai_classification=None, leak_severity=None, ai_confidence=0.0,
                detection_method="regex", local_detection_results=None, 
                gemini_detection_results=None):
    """Insert a single row of scraped data with AI workflow support.
    Skips insert if a row with the same URL already exists.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Skip duplicates by URL
    c.execute("SELECT 1 FROM scraped_data WHERE url = ? LIMIT 1", (url,))
    if c.fetchone():
        conn.close()
        print(f"↩️  Skipping duplicate URL: {url}")
        return
    
    # Convert JSON objects to strings if needed
    if isinstance(local_detection_results, dict):
        local_detection_results = str(local_detection_results)
    if isinstance(gemini_detection_results, dict):
        gemini_detection_results = str(gemini_detection_results)
    
    c.execute('''
        INSERT INTO scraped_data (
            url, title, matched_keywords, run_id, named_entities,
            ai_classification, leak_severity, ai_confidence, detection_method,
            local_detection_results, gemini_detection_results, processed_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
    ''', (url, title, matched_keywords, run_id, named_entities,
          ai_classification, leak_severity, ai_confidence, detection_method,
          local_detection_results, gemini_detection_results))
    conn.commit()
    conn.close()
    print(f"✅ Data inserted with AI classification: {url} - {ai_classification}")


def fetch_all_data(run_id=None, limit=None, offset=None, search=None):
    """Fetch all data with optional pagination and search filtering."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    query = """
        SELECT id, url, title, matched_keywords, run_id, created_at, named_entities, threat_score
        FROM scraped_data
    """
    params = []

    conditions = []
    if run_id:
        conditions.append("run_id = ?")
        params.append(run_id)

    if search:
        conditions.append("(LOWER(url) LIKE ? OR LOWER(matched_keywords) LIKE ? OR LOWER(named_entities) LIKE ?)")
        search_term = f"%{search.lower()}%"
        params.extend([search_term, search_term, search_term])

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY created_at DESC"

    if limit is not None:
        query += " LIMIT ?"
        params.append(limit)

    if offset is not None:
        query += " OFFSET ?"
        params.append(offset)

    c.execute(query, params)
    data = c.fetchall()
    conn.close()
    return data


def count_total_sites(run_id=None):
    """Return the count of unique sites (URLs) crawled, filtered by run_id if given."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if run_id:
        c.execute("SELECT COUNT(DISTINCT url) FROM scraped_data WHERE run_id = ?", (run_id,))
    else:
        c.execute("SELECT COUNT(DISTINCT url) FROM scraped_data")
    count = c.fetchone()[0]
    conn.close()
    print(f"✅ Total unique sites crawled: {count}")
    return count


def count_total_alerts(run_id=None, search=None):
    """Return total number of alerts (rows with matched keywords), optionally filtered by run_id and search."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    query = """
        SELECT COUNT(*) FROM scraped_data
        WHERE matched_keywords IS NOT NULL AND matched_keywords != ''
    """
    params = []

    if run_id:
        query += " AND run_id = ?"
        params.append(run_id)

    if search:
        query += " AND (LOWER(url) LIKE ? OR LOWER(matched_keywords) LIKE ? OR LOWER(named_entities) LIKE ?)"
        search_term = f"%{search.lower()}%"
        params.extend([search_term, search_term, search_term])

    c.execute(query, params)
    count = c.fetchone()[0]
    conn.close()
    print(f"✅ Total alerts found: {count}")
    return count


def fetch_all_run_ids():
    """Return list of distinct run_id values sorted by most recent."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT DISTINCT run_id FROM scraped_data ORDER BY created_at DESC")
    run_ids = [row[0] for row in c.fetchall()]
    conn.close()
    return run_ids


def clear_all_data():
    """Delete all rows from scraped_data table."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM scraped_data")
    conn.commit()
    conn.close()
    print("🧹 All data cleared from the database.")


def update_threat_score(row_id, score):
    """Update the threat score for a specific row."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE scraped_data SET threat_score = ? WHERE id = ?", (score, row_id))
    conn.commit()
    conn.close()
    print(f"⚡ Threat score updated for ID {row_id}: {score}")


# New AI Workflow Functions
def fetch_all_data_ai(run_id=None, limit=None, offset=None, search=None):
    """Fetch all data with AI workflow columns included."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    query = """
        SELECT id, url, title, matched_keywords, run_id, created_at, named_entities,
               ai_classification, leak_severity, ai_confidence, ai_summary,
               processed_at, detection_method, local_detection_results,
               gemini_detection_results
        FROM scraped_data
    """
    params = []

    conditions = []
    if run_id:
        conditions.append("run_id = ?")
        params.append(run_id)

    if search:
        conditions.append("(LOWER(url) LIKE ? OR LOWER(matched_keywords) LIKE ? OR LOWER(named_entities) LIKE ? OR LOWER(ai_classification) LIKE ?)")
        search_term = f"%{search.lower()}%"
        params.extend([search_term, search_term, search_term, search_term])

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY created_at DESC"

    if limit is not None:
        query += " LIMIT ?"
        params.append(limit)

    if offset is not None:
        query += " OFFSET ?"
        params.append(offset)

    c.execute(query, params)
    data = c.fetchall()
    conn.close()
    return data


def update_ai_analysis(row_id, ai_classification=None, leak_severity=None, 
                      ai_confidence=None, ai_summary=None):
    """Update AI analysis results for a specific row."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    updates = []
    params = []
    
    if ai_classification is not None:
        updates.append("ai_classification = ?")
        params.append(ai_classification)
    
    if leak_severity is not None:
        updates.append("leak_severity = ?")
        params.append(leak_severity)
    
    if ai_confidence is not None:
        updates.append("ai_confidence = ?")
        params.append(ai_confidence)
    
    if ai_summary is not None:
        updates.append("ai_summary = ?")
        params.append(ai_summary)
    
    updates.append("processed_at = datetime('now')")
    params.append(row_id)
    
    query = f"UPDATE scraped_data SET {', '.join(updates)} WHERE id = ?"
    c.execute(query, params)
    conn.commit()
    conn.close()
    print(f"🧠 AI analysis updated for ID {row_id}: {ai_classification} - {leak_severity}")


def search_by_identifier_db(identifier, limit=100):
    """Search database records by identifier (name, email, phone, Aadhaar, PAN)."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    query = """
        SELECT id, url, title, matched_keywords, run_id, created_at, named_entities,
               ai_classification, leak_severity, ai_confidence
        FROM scraped_data
        WHERE LOWER(named_entities) LIKE ? 
           OR LOWER(title) LIKE ?
           OR LOWER(matched_keywords) LIKE ?
        ORDER BY ai_confidence DESC, created_at DESC
        LIMIT ?
    """
    
    search_term = f"%{identifier.lower()}%"
    c.execute(query, (search_term, search_term, search_term, limit))
    data = c.fetchall()
    conn.close()
    
    return data


def search_indian_data(search_type="all", identifier=None, limit=100):
    """Specialized search for Indian leaked data (Aadhaar, PAN, KYC, Banking, Telecom)."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    base_query = """
        SELECT id, url, title, matched_keywords, run_id, created_at, named_entities,
               ai_classification, leak_severity, ai_confidence, ai_summary
        FROM scraped_data
    """
    
    conditions = []
    params = []
    
    if search_type == "aadhaar":
        conditions.append("(LOWER(named_entities) LIKE '%aadhaar%' OR LOWER(ai_classification) LIKE '%aadhaar%')")
    elif search_type == "pan":
        conditions.append("(LOWER(named_entities) LIKE '%pan%' OR LOWER(ai_classification) LIKE '%pan%')")
    elif search_type == "kyc":
        conditions.append("(LOWER(named_entities) LIKE '%kyc%' OR LOWER(ai_classification) LIKE '%kyc%' OR LOWER(matched_keywords) LIKE '%kyc%')")
    elif search_type == "banking":
        conditions.append("(LOWER(named_entities) LIKE '%bank%' OR LOWER(ai_classification) LIKE '%bank%' OR LOWER(named_entities) LIKE '%ifsc%' OR LOWER(named_entities) LIKE '%account%')")
    elif search_type == "telecom":
        conditions.append("(LOWER(named_entities) LIKE '%phone%' OR LOWER(named_entities) LIKE '%imei%' OR LOWER(ai_classification) LIKE '%telecom%')")
    elif search_type == "indian_ids":
        conditions.append("(LOWER(ai_classification) IN ('aadhaar', 'pan', 'banking/financial', 'telecom', 'government_id'))")
    
    if identifier:
        identifier_condition = "(LOWER(named_entities) LIKE ? OR LOWER(title) LIKE ? OR LOWER(matched_keywords) LIKE ?)"
        if conditions:
            conditions.append(identifier_condition)
        else:
            conditions = [identifier_condition]
        search_term = f"%{identifier.lower()}%"
        params.extend([search_term, search_term, search_term])
    
    if conditions:
        base_query += " WHERE " + " AND ".join(conditions)
    
    base_query += " ORDER BY ai_confidence DESC, created_at DESC LIMIT ?"
    params.append(limit)
    
    c.execute(base_query, params)
    data = c.fetchall()
    conn.close()
    
    return data


def get_indian_leak_statistics():
    """Get statistics specifically for Indian data leaks."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    stats = {}
    
    # Aadhaar leak statistics
    c.execute("""
        SELECT COUNT(*) FROM scraped_data 
        WHERE LOWER(named_entities) LIKE '%aadhaar%' OR LOWER(ai_classification) LIKE '%aadhaar%'
    """)
    stats['aadhaar_leaks'] = c.fetchone()[0]
    
    # PAN leak statistics  
    c.execute("""
        SELECT COUNT(*) FROM scraped_data 
        WHERE LOWER(named_entities) LIKE '%pan%' OR LOWER(ai_classification) LIKE '%pan%'
    """)
    stats['pan_leaks'] = c.fetchone()[0]
    
    # Banking leak statistics
    c.execute("""
        SELECT COUNT(*) FROM scraped_data 
        WHERE LOWER(named_entities) LIKE '%bank%' OR LOWER(ai_classification) LIKE '%bank%' 
           OR LOWER(named_entities) LIKE '%ifsc%' OR LOWER(named_entities) LIKE '%account%'
    """)
    stats['banking_leaks'] = c.fetchone()[0]
    
    # Telecom leak statistics
    c.execute("""
        SELECT COUNT(*) FROM scraped_data 
        WHERE LOWER(named_entities) LIKE '%phone%' OR LOWER(named_entities) LIKE '%imei%' 
           OR LOWER(ai_classification) LIKE '%telecom%'
    """)
    stats['telecom_leaks'] = c.fetchone()[0]
    
    # KYC document statistics
    c.execute("""
        SELECT COUNT(*) FROM scraped_data 
        WHERE LOWER(named_entities) LIKE '%kyc%' OR LOWER(ai_classification) LIKE '%kyc%' 
           OR LOWER(matched_keywords) LIKE '%kyc%'
    """)
    stats['kyc_leaks'] = c.fetchone()[0]
    
    # High severity Indian leaks
    c.execute("""
        SELECT COUNT(*) FROM scraped_data 
        WHERE leak_severity IN ('HIGH', 'CRITICAL') 
           AND (LOWER(ai_classification) IN ('aadhaar', 'pan', 'banking/financial', 'telecom', 'government_id')
                OR LOWER(named_entities) LIKE '%aadhaar%' OR LOWER(named_entities) LIKE '%pan%')
    """)
    stats['high_severity_indian'] = c.fetchone()[0]
    
    # Recent Indian leaks (last 30 days)
    c.execute("""
        SELECT COUNT(*) FROM scraped_data 
        WHERE created_at >= datetime('now', '-30 days')
           AND (LOWER(ai_classification) IN ('aadhaar', 'pan', 'banking/financial', 'telecom', 'government_id')
                OR LOWER(named_entities) LIKE '%aadhaar%' OR LOWER(named_entities) LIKE '%pan%')
    """)
    stats['recent_indian_leaks'] = c.fetchone()[0]
    
    conn.close()
    return stats


def search_by_entity_type(entity_type, entity_value=None, limit=100):
    """Search by specific entity types extracted from text."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    query = """
        SELECT id, url, title, matched_keywords, run_id, created_at, named_entities,
               ai_classification, leak_severity, ai_confidence
        FROM scraped_data
        WHERE LOWER(named_entities) LIKE ?
    """
    
    params = [f"%{entity_type.lower()}%"]
    
    if entity_value:
        query += " AND (LOWER(named_entities) LIKE ? OR LOWER(title) LIKE ? OR LOWER(matched_keywords) LIKE ?)"
        search_term = f"%{entity_value.lower()}%"
        params.extend([search_term, search_term, search_term])
    
    query += " ORDER BY ai_confidence DESC, created_at DESC LIMIT ?"
    params.append(limit)
    
    c.execute(query, params)
    data = c.fetchall()
    conn.close()
    
    return data


def get_leak_statistics():
    """Get comprehensive leak detection statistics."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Total records
    c.execute("SELECT COUNT(*) FROM scraped_data")
    total_records = c.fetchone()[0]
    
    # Records with AI classification
    c.execute("SELECT COUNT(*) FROM scraped_data WHERE ai_classification IS NOT NULL")
    ai_analyzed = c.fetchone()[0]
    
    # Records by severity
    c.execute("""
        SELECT leak_severity, COUNT(*) 
        FROM scraped_data 
        WHERE leak_severity IS NOT NULL 
        GROUP BY leak_severity
    """)
    severity_stats = dict(c.fetchall())
    
    # Records by classification
    c.execute("""
        SELECT ai_classification, COUNT(*) 
        FROM scraped_data 
        WHERE ai_classification IS NOT NULL 
        GROUP BY ai_classification
    """)
    classification_stats = dict(c.fetchall())
    
    # Average confidence score
    c.execute("SELECT AVG(ai_confidence) FROM scraped_data WHERE ai_confidence > 0")
    avg_confidence = c.fetchone()[0] or 0
    
    conn.close()
    
    return {
        "total_records": total_records,
        "ai_analyzed": ai_analyzed,
        "severity_distribution": severity_stats,
        "classification_distribution": classification_stats,
        "average_confidence": round(avg_confidence, 2)
    }


def export_leaks_json(run_id=None, classification=None, severity=None, limit=None):
    """Export leak data as structured JSON."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    query = """
        SELECT id, url, title, matched_keywords, run_id, created_at, named_entities,
               ai_classification, leak_severity, ai_confidence, ai_summary,
               processed_at, detection_method
        FROM scraped_data
    """
    
    conditions = []
    params = []
    
    if run_id:
        conditions.append("run_id = ?")
        params.append(run_id)
    
    if classification:
        conditions.append("ai_classification = ?")
        params.append(classification)
    
    if severity:
        conditions.append("leak_severity = ?")
        params.append(severity)
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += " ORDER BY ai_confidence DESC, created_at DESC"
    
    if limit:
        query += " LIMIT ?"
        params.append(limit)
    
    c.execute(query, params)
    rows = c.fetchall()
    
    # Convert to structured JSON
    leaks = []
    for row in rows:
        leak = {
            "id": row[0],
            "url": row[1],
            "title": row[2],
            "matched_keywords": row[3].split(',') if row[3] else [],
            "run_id": row[4],
            "discovered_at": row[5],
            "entities": row[6].split(',') if row[6] else [],
            "ai_analysis": {
                "classification": row[7],
                "severity": row[8],
                "confidence": row[9],
                "summary": row[10],
                "processed_at": row[11],
                "detection_method": row[12]
            }
        }
        leaks.append(leak)
    
    conn.close()
    return leaks
