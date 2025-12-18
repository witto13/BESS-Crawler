#!/usr/bin/env python3
"""
Live Monitor für Crawl-Fortschritt
"""
import time
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from apps.db.client import get_pool

def clear_screen():
    os.system('clear' if os.name != 'nt' else 'cls')

def format_number(n):
    return f"{n:,}".replace(",", ".")

def monitor():
    pool = get_pool()
    
    last_total = 0
    
    while True:
        try:
            with pool.connection() as conn:
                with conn.cursor() as cur:
                    # Gesamt-Statistiken
                    cur.execute("""
                        SELECT 
                            COUNT(*) as total,
                            COUNT(CASE WHEN bess_score >= 1 THEN 1 END) as with_bess,
                            COUNT(CASE WHEN grid_score >= 1 THEN 1 END) as with_grid,
                            COUNT(CASE WHEN bess_score >= 3 THEN 1 END) as high_bess,
                            COUNT(CASE WHEN grid_score >= 3 THEN 1 END) as high_grid,
                            COUNT(CASE WHEN confidence = 'high' THEN 1 END) as high_conf,
                            COUNT(CASE WHEN capacity_mw IS NOT NULL OR capacity_mwh IS NOT NULL THEN 1 END) as with_capacity,
                            COUNT(CASE WHEN area_hectares IS NOT NULL THEN 1 END) as with_area,
                            COUNT(CASE WHEN decision_date IS NOT NULL THEN 1 END) as with_date,
                            COUNT(CASE WHEN developer_company IS NOT NULL THEN 1 END) as with_company
                        FROM procedures 
                        WHERE procedure_id != 'test-proc-999'
                    """)
                    stats = cur.fetchone()
                    
                    # Queue-Status (Redis)
                    try:
                        import redis
                        r = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)
                        queue_size = r.llen('crawl')
                    except:
                        queue_size = "?"
                    
                    # Quellen-Verteilung
                    cur.execute("""
                        SELECT source_system, COUNT(DISTINCT p.procedure_id) as count
                        FROM procedures p
                        LEFT JOIN sources s ON p.procedure_id = s.procedure_id
                        WHERE p.procedure_id != 'test-proc-999'
                        GROUP BY source_system
                        ORDER BY count DESC
                    """)
                    sources = cur.fetchall()
                    
                    clear_screen()
                    
                    total, with_bess, with_grid, high_bess, high_grid, high_conf, with_capacity, with_area, with_date, with_company = stats
                    
                    # Berechne Rate
                    if last_total > 0:
                        rate = total - last_total
                        rate_str = f" (+{rate}/5s)" if rate > 0 else ""
                    else:
                        rate_str = ""
                    last_total = total
                    
                    print("=" * 80)
                    print("🔍 BESS/PV CRAWL - LIVE MONITOR")
                    print("=" * 80)
                    print()
                    print(f"📊 TOTAL PROCEDURES: {format_number(total)}{rate_str}")
                    print(f"📋 QUEUE SIZE: {queue_size} jobs")
                    print()
                    print("─" * 80)
                    print("SCORING:")
                    print(f"  • BESS Score >= 1: {format_number(with_bess)}")
                    print(f"  • BESS Score >= 3: {format_number(high_bess)}")
                    print(f"  • Grid Score >= 1: {format_number(with_grid)}")
                    print(f"  • Grid Score >= 3: {format_number(high_grid)}")
                    print(f"  • High Confidence: {format_number(high_conf)}")
                    print()
                    print("─" * 80)
                    print("EXTRAKTIONEN:")
                    print(f"  • Mit Kapazität (MW/MWh): {format_number(with_capacity)}")
                    print(f"  • Mit Fläche (Hektar): {format_number(with_area)}")
                    print(f"  • Mit Datum: {format_number(with_date)}")
                    print(f"  • Mit Firma: {format_number(with_company)}")
                    print()
                    print("─" * 80)
                    print("QUELLEN:")
                    for source, count in sources:
                        source_name = source or "unbekannt"
                        print(f"  • {source_name}: {format_number(count)}")
                    print()
                    print("─" * 80)
                    print(f"⏱️  Letztes Update: {time.strftime('%H:%M:%S')}")
                    print("   (Drücke Ctrl+C zum Beenden)")
                    print("=" * 80)
                    
        except Exception as e:
            print(f"Fehler: {e}")
            time.sleep(1)
        
        time.sleep(5)

if __name__ == "__main__":
    try:
        monitor()
    except KeyboardInterrupt:
        print("\n\nMonitor beendet.")
        sys.exit(0)






