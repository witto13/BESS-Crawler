#!/usr/bin/env python3
"""
Schätzt die verbleibende Zeit für den Crawl.
"""
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from apps.db.client import get_pool

def estimate_time():
    pool = get_pool()
    
    with pool.connection() as conn:
        with conn.cursor() as cur:
            # Hole aktuelle Statistiken
            cur.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN source_system = 'diplanung' THEN 1 END) as diplanung_count
                FROM procedures p
                LEFT JOIN sources s ON p.procedure_id = s.procedure_id
                WHERE p.procedure_id != 'test-proc-999'
            """)
            stats = cur.fetchone()
            total, diplanung_count = stats
            
            # Prüfe Queue
            try:
                import redis
                r = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)
                queue_size = r.llen('crawl')
            except:
                queue_size = 0
            
            # Schätze basierend auf:
            # - DiPlanung: 1102 Procedures (bekannt)
            # - Queue: verbleibende Jobs
            # - Rate: ~50-100 Procedures/Minute (je nach Komplexität)
            
            diplanung_total = 1102
            diplanung_done = diplanung_count
            
            # Schätze verbleibende DiPlanung
            diplanung_remaining = max(0, diplanung_total - diplanung_done)
            
            # Schätze Zeit für DiPlanung (bei ~50-80 Procedures/Minute)
            rate_per_min = 60  # konservative Schätzung
            diplanung_minutes = diplanung_remaining / rate_per_min if rate_per_min > 0 else 0
            
            # Schätze Zeit für Queue (RIS/Gazette/XPlanung sind schneller, ~100-200/Minute)
            queue_rate_per_min = 150
            queue_minutes = queue_size / queue_rate_per_min if queue_rate_per_min > 0 else 0
            
            total_minutes = diplanung_minutes + queue_minutes
            
            print("=" * 80)
            print("⏱️  ZEITSCHÄTZUNG FÜR CRAWL-ABSCHLUSS")
            print("=" * 80)
            print()
            print(f"📊 AKTUELLER STATUS:")
            print(f"   • Total Procedures: {total}")
            print(f"   • DiPlanung: {diplanung_done}/{diplanung_total} ({diplanung_done*100//diplanung_total if diplanung_total > 0 else 0}%)")
            print(f"   • Queue: {queue_size} Jobs")
            print()
            print(f"⏳ VERBLEIBEND:")
            print(f"   • DiPlanung: ~{diplanung_remaining} Procedures")
            print(f"   • Queue: {queue_size} Jobs")
            print()
            print(f"🚀 GESCHÄTZTE ZEIT:")
            if total_minutes < 1:
                print(f"   • < 1 Minute (fast fertig!)")
            elif total_minutes < 60:
                print(f"   • ~{int(total_minutes)} Minuten")
            else:
                hours = int(total_minutes // 60)
                mins = int(total_minutes % 60)
                print(f"   • ~{hours}h {mins}m")
            print()
            print(f"   (DiPlanung: ~{int(diplanung_minutes)}m, Queue: ~{int(queue_minutes)}m)")
            print()
            print("=" * 80)

if __name__ == "__main__":
    estimate_time()






