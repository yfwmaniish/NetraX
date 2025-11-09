import sys
import os
import csv
import io
import json
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, session, Response, jsonify
from dotenv import load_dotenv

# Fix paths
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(BASE_DIR, '..', 'database'))
sys.path.append(os.path.join(BASE_DIR, '..'))

from models import (fetch_all_run_ids, fetch_all_data, count_total_sites, 
                    count_total_alerts, clear_all_data, fetch_all_data_ai, 
                    search_by_identifier_db, get_leak_statistics, export_leaks_json,
                    search_indian_data, get_indian_leak_statistics, search_by_entity_type)
try:
    from threat_score import calculate_threat_score
except ImportError:
    calculate_threat_score = None
# Try to import AI utilities, but continue without them if not available
try:
    from ai_utils import search_by_identifier, GeminiAIProcessor
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    print("⚠️ AI utilities not available - running without Gemini integration")
    def search_by_identifier(*args, **kwargs):
        return []
    class GeminiAIProcessor:
        def __init__(self, *args, **kwargs):
            pass

# Load env
load_dotenv()
USERNAME = os.getenv("DASHBOARD_USERNAME")
PASSWORD = os.getenv("DASHBOARD_PASSWORD")

# Flask app setup
app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = b'super_secret_h4_key'

DB_PATH = os.path.join(BASE_DIR, '..', 'decimal_scraped_data.db')

@app.route('/')
def index():
    """Redirect directly to dashboard - no login required."""
    return redirect('/dashboard')

@app.route('/dashboard')
def dashboard():
    # Remove login check - direct access to dashboard

    selected_run_id = request.args.get('run_id', None)
    search_query = request.args.get('search', '').strip()

    try:
        page = int(request.args.get('page', 1))
        if page < 1:
            page = 1
    except ValueError:
        page = 1

    per_page = 150
    offset = (page - 1) * per_page

    total_sites = count_total_sites(selected_run_id)
    total_alerts = count_total_alerts(selected_run_id, search=search_query)
    run_ids = fetch_all_run_ids()

    data = fetch_all_data(selected_run_id, limit=per_page, offset=offset, search=search_query)
    total_pages = max(1, (total_alerts + per_page - 1) // per_page)

    highlighted_data = []
    for row in data:
        if len(row) == 8:
            id, url, title, keywords, run_id, created_at, entities, db_threat_score = row
        elif len(row) == 7:
            id, url, title, keywords, run_id, created_at, entities = row
            db_threat_score = None
        elif len(row) == 6:
            id, url, title, keywords, run_id, created_at = row
            entities = ""
            db_threat_score = None
        else:
            continue

        import ast

        # Robustly parse keywords: accept JSON-like lists or CSV strings
        keyword_tags = []
        if keywords:
            parsed = None
            try:
                parsed = ast.literal_eval(keywords)
            except Exception:
                parsed = None
            if isinstance(parsed, list):
                keyword_tags = [str(x).strip() for x in parsed if str(x).strip()]
            elif isinstance(parsed, str):
                keyword_tags = [parsed.strip()] if parsed.strip() else []
            else:
                # Fallback: treat as CSV string
                keyword_tags = [kw.strip() for kw in str(keywords).split(',') if kw.strip()]

        entity_tags = [ent.strip() for ent in str(entities).split(',') if ent.strip()] if entities else []

        try:
            formatted_time = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S').strftime('%b %d, %Y %H:%M')
        except Exception:
            formatted_time = created_at

        threat_score = db_threat_score if db_threat_score else "0.0"

        highlighted_data.append({
            'id': id,
            'url': url,
            'title': highlight_keywords(title),
            'keywords': keyword_tags,
            'entities': entity_tags,
            'run_id': run_id,
            'timestamp': formatted_time,
            'threat_score': threat_score
        })

    return render_template('index.html',
                           data=highlighted_data,
                           total_sites=total_sites,
                           total_alerts=total_alerts,
                           run_ids=run_ids,
                           selected_run_id=selected_run_id,
                           page=page,
                           total_pages=total_pages,
                           search_query=search_query)

@app.route('/score/<int:item_id>', methods=['POST'])
def score_item(item_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT title, matched_keywords FROM scraped_data WHERE id = ?", (item_id,))
    row = cursor.fetchone()

    if not row:
        return jsonify({'error': 'Item not found'}), 404

    title, keywords = row
    text = (title or '') + ' ' + (keywords or '')
    score, reasons = calculate_threat_score(text)

    cursor.execute("UPDATE scraped_data SET threat_score = ? WHERE id = ?", (score, item_id))
    conn.commit()
    conn.close()

    print(f"\u2705 Threat score updated for ID {item_id}: {score}")
    return jsonify({'score': score, 'reasons': reasons})

@app.route('/download_csv')
def download_csv():
    # Remove login check - direct access

    data = fetch_all_data()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'URL', 'Title', 'Matched Keywords', 'Entities', 'Run ID', 'Timestamp', 'Threat Score'])

    for row in data:
        if len(row) == 8:
            id, url, title, keywords, run_id, created_at, entities, db_threat_score = row
        elif len(row) == 7:
            id, url, title, keywords, run_id, created_at, entities = row
            db_threat_score = "N/A"
        elif len(row) == 6:
            id, url, title, keywords, run_id, created_at = row
            entities = ""
            db_threat_score = "N/A"
        else:
            continue

        try:
            formatted_time = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S').strftime('%b %d, %Y %H:%M')
        except Exception:
            formatted_time = created_at

        threat_score = db_threat_score if db_threat_score else "N/A"

        writer.writerow([id, url, title, keywords, entities, run_id, formatted_time, threat_score])

    output.seek(0)
    return Response(output, mimetype="text/csv",
                    headers={"Content-Disposition": "attachment;filename=darkweb_data.csv"})

@app.route('/clear_history', methods=['POST'])
def clear_history():
    # Remove login check - direct access
    clear_all_data()
    return redirect('/dashboard')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# Enhanced search function for various types of leaked data
def comprehensive_search(query, search_filters=None):
    """Perform comprehensive search across all leaked data with advanced filtering."""
    if not search_filters:
        search_filters = {}
    
    # Determine search type based on query pattern
    search_type = "general"
    
    # Check if query matches specific patterns
    import re
    
    # Aadhaar pattern
    if re.match(r'^\d{4}[\s\-]?\d{4}[\s\-]?\d{4}$', query.replace(' ', '').replace('-', '')):
        search_type = "aadhaar"
    # PAN pattern
    elif re.match(r'^[A-Z]{5}\d{4}[A-Z]$', query.upper()):
        search_type = "pan"
    # Email pattern
    elif re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', query):
        search_type = "email"
    # Phone pattern
    elif re.match(r'^[\+]?[0-9]{10,13}$', query.replace(' ', '').replace('-', '')):
        search_type = "phone"
    
    results = []
    
    try:
        # First try Indian data search if applicable
        if search_type in ["aadhaar", "pan"] or search_filters.get("indian_only"):
            indian_results = search_indian_data(
                search_type=search_type if search_type in ["aadhaar", "pan"] else "all",
                identifier=query,
                limit=search_filters.get("limit", 100)
            )
            
            for row in indian_results:
                result = {
                    'id': row[0],
                    'url': row[1],
                    'title': row[2],
                    'keywords': row[3].split(',') if row[3] else [],
                    'run_id': row[4],
                    'timestamp': row[5],
                    'entities': row[6].split(',') if row[6] else [],
                    'ai_classification': row[7] if len(row) > 7 else None,
                    'leak_severity': row[8] if len(row) > 8 else None,
                    'ai_confidence': row[9] if len(row) > 9 else 0,
                    'search_match_type': 'indian_data',
                    'relevance_score': calculate_relevance_score(query, row)
                }
                results.append(result)
        
        # General database search
        if search_type == "general" or len(results) < 10:
            db_results = search_by_identifier_db(query, search_filters.get("limit", 100))
            
            for row in db_results:
                # Avoid duplicates
                if not any(r['id'] == row[0] for r in results):
                    result = {
                        'id': row[0],
                        'url': row[1],
                        'title': row[2],
                        'keywords': row[3].split(',') if row[3] else [],
                        'run_id': row[4],
                        'timestamp': row[5],
                        'entities': row[6].split(',') if row[6] else [],
                        'ai_classification': row[7] if len(row) > 7 else None,
                        'leak_severity': row[8] if len(row) > 8 else None,
                        'ai_confidence': row[9] if len(row) > 9 else 0,
                        'search_match_type': 'general_db',
                        'relevance_score': calculate_relevance_score(query, row)
                    }
                    results.append(result)
        
        # Sort by relevance score and confidence
        results.sort(key=lambda x: (x['relevance_score'], x['ai_confidence']), reverse=True)
        
        # Apply additional filters
        if search_filters.get('severity'):
            results = [r for r in results if r.get('leak_severity') == search_filters['severity']]
        
        if search_filters.get('classification'):
            results = [r for r in results if r.get('ai_classification') == search_filters['classification']]
        
        return {
            'success': True,
            'query': query,
            'search_type': search_type,
            'total_results': len(results),
            'filters_applied': search_filters,
            'results': results[:search_filters.get('limit', 100)]
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'query': query,
            'search_type': search_type
        }

def calculate_relevance_score(query, db_row):
    """Calculate relevance score for search results."""
    score = 0
    query_lower = query.lower()
    
    # Check title match
    if db_row[2] and query_lower in db_row[2].lower():
        score += 3
    
    # Check entities match
    if db_row[6] and query_lower in db_row[6].lower():
        score += 4
    
    # Check keywords match
    if db_row[3] and query_lower in db_row[3].lower():
        score += 2
    
    # Check URL match
    if db_row[1] and query_lower in db_row[1].lower():
        score += 1
    
    # Boost score for AI-classified results
    if len(db_row) > 7 and db_row[7]:
        score += 1
    
    # Boost score for high-severity leaks
    if len(db_row) > 8 and db_row[8] in ['HIGH', 'CRITICAL']:
        score += 2
    
    return score

# New AI-powered search endpoints
@app.route('/api/search_identifier', methods=['POST'])
def api_search_identifier():
    """Search for leaks by identifier (name, email, phone, Aadhaar, PAN)."""
    # Remove authentication check - direct API access
    
    data = request.get_json()
    if not data or 'identifier' not in data:
        return jsonify({'error': 'Identifier is required'}), 400
    
    identifier = data['identifier'].strip()
    use_ai = data.get('use_ai', True)
    limit = min(int(data.get('limit', 100)), 500)  # Max 500 results
    
    try:
        # First search local database
        db_results = search_by_identifier_db(identifier, limit)
        
        # Convert to structured format
        formatted_results = []
        for row in db_results:
            result = {
                'id': row[0],
                'url': row[1],
                'title': row[2],
                'keywords': row[3].split(',') if row[3] else [],
                'run_id': row[4],
                'timestamp': row[5],
                'entities': row[6].split(',') if row[6] else [],
                'ai_classification': row[7] if len(row) > 7 else None,
                'leak_severity': row[8] if len(row) > 8 else None,
                'ai_confidence': row[9] if len(row) > 9 else 0,
                'match_type': 'database'
            }
            formatted_results.append(result)
        
        # If AI is enabled and we have ambiguous results, use Gemini for fuzzy matching
        ai_results = []
        if use_ai and (len(formatted_results) == 0 or len(formatted_results) > 10):
            try:
                ai_processor = GeminiAIProcessor()
                ai_matches = search_by_identifier(identifier, formatted_results, ai_processor)
                for match in ai_matches:
                    if match.get('match_type') == 'ai_fuzzy':
                        ai_results.append(match)
            except Exception as e:
                print(f"AI search failed: {str(e)}")
        
        return jsonify({
            'success': True,
            'identifier': identifier,
            'database_results': len(formatted_results),
            'ai_results': len(ai_results),
            'total_results': len(formatted_results) + len(ai_results),
            'results': formatted_results + ai_results
        })
    
    except Exception as e:
        return jsonify({'error': f'Search failed: {str(e)}'}), 500

@app.route('/api/statistics')
def api_statistics():
    """Get comprehensive leak detection statistics."""
    # Remove authentication check - direct API access
    
    try:
        stats = get_leak_statistics()
        return jsonify({
            'success': True,
            'statistics': stats
        })
    except Exception as e:
        return jsonify({'error': f'Failed to get statistics: {str(e)}'}), 500

@app.route('/api/export_json')
def api_export_json():
    """Export leak data as structured JSON."""
    # Remove authentication check - direct API access
    
    # Get query parameters
    run_id = request.args.get('run_id')
    classification = request.args.get('classification')
    severity = request.args.get('severity')
    limit = int(request.args.get('limit', 1000))
    
    try:
        leaks = export_leaks_json(run_id, classification, severity, limit)
        
        # Generate summary
        summary = {
            'total_leaks': len(leaks),
            'export_timestamp': datetime.now().isoformat(),
            'filters_applied': {
                'run_id': run_id,
                'classification': classification,
                'severity': severity,
                'limit': limit
            },
            'classifications': {},
            'severities': {}
        }
        
        # Count classifications and severities
        for leak in leaks:
            ai_analysis = leak.get('ai_analysis', {})
            if ai_analysis.get('classification'):
                summary['classifications'][ai_analysis['classification']] = summary['classifications'].get(ai_analysis['classification'], 0) + 1
            if ai_analysis.get('severity'):
                summary['severities'][ai_analysis['severity']] = summary['severities'].get(ai_analysis['severity'], 0) + 1
        
        response_data = {
            'summary': summary,
            'leaks': leaks
        }
        
        # Return as downloadable JSON file
        response = Response(
            json.dumps(response_data, indent=2),
            mimetype='application/json',
            headers={'Content-Disposition': f'attachment; filename=leak_data_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'}
        )
        return response
    
    except Exception as e:
        return jsonify({'error': f'Export failed: {str(e)}'}), 500

@app.route('/search')
def search_page():
    """Search page for identifier-based searches."""
    return render_template('search.html')

@app.route('/indian_search')
def indian_search_page():
    """Indian data leak search page."""
    return render_template('indian_search.html')

@app.route('/all_leaks')
def all_leaks_page():
    """Show all detected leaks with direct source links."""
    try:
        # Get all data with AI classification and entities
        data = fetch_all_data_ai(limit=1000)  # Get more results
        
        formatted_data = []
        for row in data:
            if len(row) >= 15:  # Ensure we have all fields
                leak_info = {
                    'id': row[0],
                    'url': row[1],
                    'title': row[2],
                    'keywords': row[3].split(',') if row[3] else [],
                    'run_id': row[4],
                    'timestamp': row[5],
                    'entities': row[6].split(',') if row[6] else [],
                    'ai_classification': row[7],
                    'leak_severity': row[8], 
                    'ai_confidence': row[9],
                    'ai_summary': row[10],
                    'processed_at': row[11],
                    'detection_method': row[12],
                    'local_detection': row[13],
                    'gemini_detection': row[14]
                }
                
                # Only include if it has entities or AI classification
                if leak_info['entities'] or leak_info['ai_classification']:
                    formatted_data.append(leak_info)
        
        # Sort by confidence and timestamp
        formatted_data.sort(key=lambda x: (x['ai_confidence'] or 0, x['timestamp']), reverse=True)
        
        return render_template('all_leaks.html', leaks=formatted_data[:100])  # Show top 100
        
    except Exception as e:
        print(f"Error in all_leaks_page: {str(e)}")
        return render_template('all_leaks.html', leaks=[], error=str(e))

@app.route('/api/indian_statistics')
def api_indian_statistics():
    """Get statistics specifically for Indian data leaks."""
    # Remove authentication check - direct API access
    
    try:
        stats = get_indian_leak_statistics()
        return jsonify({
            'success': True,
            'statistics': stats
        })
    except Exception as e:
        return jsonify({'error': f'Failed to get Indian statistics: {str(e)}'}), 500

@app.route('/api/search_indian_identifier', methods=['POST'])
def api_search_indian_identifier():
    """Search for Indian data leaks by specific identifier."""
    # Remove authentication check - direct API access
    
    data = request.get_json()
    if not data or 'identifier' not in data:
        return jsonify({'error': 'Identifier is required'}), 400
    
    identifier = data['identifier'].strip()
    search_type = data.get('search_type', 'all')
    limit = min(int(data.get('limit', 200)), 500)  # Max 500 results
    
    try:
        # Search Indian data with specific type filter
        results = search_indian_data(search_type=search_type, identifier=identifier, limit=limit)
        
        # Convert to structured format
        formatted_results = []
        for row in results:
            result = {
                'id': row[0],
                'url': row[1],
                'title': row[2],
                'keywords': row[3].split(',') if row[3] else [],
                'run_id': row[4],
                'timestamp': row[5],
                'entities': row[6].split(',') if row[6] else [],
                'ai_classification': row[7] if len(row) > 7 else None,
                'leak_severity': row[8] if len(row) > 8 else None,
                'ai_confidence': row[9] if len(row) > 9 else 0,
                'ai_summary': row[10] if len(row) > 10 else None,
                'match_type': 'indian_data'
            }
            formatted_results.append(result)
        
        return jsonify({
            'success': True,
            'identifier': identifier,
            'search_type': search_type,
            'total_results': len(formatted_results),
            'results': formatted_results
        })
    
    except Exception as e:
        return jsonify({'error': f'Indian data search failed: {str(e)}'}), 500

@app.route('/api/search_indian_category', methods=['POST'])
def api_search_indian_category():
    """Browse Indian data leaks by category and severity."""
    # Remove authentication check - direct API access
    
    data = request.get_json()
    if not data or 'search_type' not in data:
        return jsonify({'error': 'Search type is required'}), 400
    
    search_type = data['search_type']
    severity = data.get('severity')
    limit = min(int(data.get('limit', 200)), 500)  # Max 500 results
    
    try:
        # Search Indian data by category
        results = search_indian_data(search_type=search_type, limit=limit)
        
        # Filter by severity if specified
        if severity:
            filtered_results = []
            for row in results:
                if len(row) > 8 and row[8] == severity:
                    filtered_results.append(row)
            results = filtered_results
        
        # Convert to structured format
        formatted_results = []
        for row in results:
            result = {
                'id': row[0],
                'url': row[1],
                'title': row[2],
                'keywords': row[3].split(',') if row[3] else [],
                'run_id': row[4],
                'timestamp': row[5],
                'entities': row[6].split(',') if row[6] else [],
                'ai_classification': row[7] if len(row) > 7 else None,
                'leak_severity': row[8] if len(row) > 8 else None,
                'ai_confidence': row[9] if len(row) > 9 else 0,
                'ai_summary': row[10] if len(row) > 10 else None,
                'match_type': 'category_browse'
            }
            formatted_results.append(result)
        
        return jsonify({
            'success': True,
            'search_type': search_type,
            'severity_filter': severity,
            'total_results': len(formatted_results),
            'results': formatted_results
        })
    
    except Exception as e:
        return jsonify({'error': f'Category search failed: {str(e)}'}), 500

def highlight_keywords(text):
    if not text:
        return text
    keywords = ['india', 'drugs', 'arms', 'weapons', 'fake id', 'passport', 'bitcoin', 'hack', 'cybercrime', 'ransomware']
    for kw in keywords:
        text = text.replace(kw, f"<span class='highlight'>{kw}</span>")
        text = text.replace(kw.capitalize(), f"<span class='highlight'>{kw.capitalize()}</span>")
    return text

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
 
