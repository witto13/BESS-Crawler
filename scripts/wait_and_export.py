#!/usr/bin/env python3
"""
Wartet auf Crawl-Abschluss und erstellt dann automatisch einen Export.
"""
import time
import sys
import os
import subprocess

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from apps.db.client import get_pool

def check_crawl_status():
    """Prüft ob der Crawl noch läuft."""
    pool = get_pool()
    with pool.connection() as conn:
        with conn.cursor() as cur:
            # Prüfe ob noch Jobs in Queue sind (via Redis)
            try:
                import redis
                r = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)
                queue_size = r.llen('crawl')
                if queue_size > 0:
                    return True, queue_size
            except:
                pass
            
            # Prüfe ob Worker noch aktiv ist (letzte Updates)
            # Wenn in den letzten 60 Sekunden neue Procedures hinzugekommen sind, läuft noch was
            cur.execute("""
                SELECT COUNT(*) 
                FROM procedures 
                WHERE procedure_id != 'test-proc-999'
                AND updated_at > NOW() - INTERVAL '60 seconds'
            """)
            recent = cur.fetchone()[0]
            if recent > 0:
                return True, recent
            
            return False, 0

def wait_for_completion(check_interval=30, max_wait_minutes=60):
    """Wartet auf Crawl-Abschluss."""
    print("⏳ Warte auf Crawl-Abschluss...")
    print("   (Prüfe alle 30 Sekunden, max. 60 Minuten)")
    print()
    
    start_time = time.time()
    last_count = 0
    
    while True:
        elapsed = (time.time() - start_time) / 60
        
        # Timeout nach max_wait_minutes
        if elapsed > max_wait_minutes:
            print(f"\n⏰ Timeout nach {max_wait_minutes} Minuten.")
            print("   Erstelle Export mit aktuellen Daten...")
            return True
        
        is_running, info = check_crawl_status()
        
        # Hole aktuelle Statistik
        pool = get_pool()
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT COUNT(*) 
                    FROM procedures 
                    WHERE procedure_id != 'test-proc-999'
                """)
                current_count = cur.fetchone()[0]
        
        if not is_running:
            print(f"\n✅ Crawl scheint abgeschlossen!")
            print(f"   Total Procedures: {current_count}")
            return True
        
        # Zeige Fortschritt
        if current_count != last_count:
            diff = current_count - last_count
            print(f"⏱️  {elapsed:.1f} min | Procedures: {current_count} (+{diff}) | Queue: {info}")
            last_count = current_count
        else:
            print(f"⏱️  {elapsed:.1f} min | Warte... (keine neuen Procedures)")
        
        time.sleep(check_interval)

def create_export():
    """Erstellt Excel-Export."""
    print("\n📊 Erstelle Excel-Export...")
    
    output_path = "/workspace/bess_procedures_final.xlsx"
    
    try:
        from apps.export.to_excel import export_from_db
        from apps.orchestrator.config import settings
        
        export_from_db(settings.postgres_dsn, output_path, filter_high_confidence=False)
        
        print(f"✅ Export erstellt: {output_path}")
        
        # Zeige Statistiken
        pool = get_pool()
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(CASE WHEN bess_score >= 3 THEN 1 END) as high_bess,
                        COUNT(CASE WHEN grid_score >= 3 THEN 1 END) as high_grid,
                        COUNT(CASE WHEN confidence = 'high' THEN 1 END) as high_conf,
                        COUNT(CASE WHEN capacity_mw IS NOT NULL OR capacity_mwh IS NOT NULL THEN 1 END) as with_cap,
                        COUNT(CASE WHEN area_hectares IS NOT NULL THEN 1 END) as with_area,
                        COUNT(CASE WHEN decision_date IS NOT NULL THEN 1 END) as with_date,
                        COUNT(CASE WHEN developer_company IS NOT NULL THEN 1 END) as with_company
                    FROM procedures 
                    WHERE procedure_id != 'test-proc-999'
                """)
                stats = cur.fetchone()
                
                total, high_bess, high_grid, high_conf, with_cap, with_area, with_date, with_company = stats
                
                print("\n📈 FINALE STATISTIKEN:")
                print(f"   Total Procedures: {total}")
                print(f"   High BESS (>=3): {high_bess}")
                print(f"   High Grid (>=3): {high_grid}")
                print(f"   High Confidence: {high_conf}")
                print(f"   Mit Kapazität: {with_cap}")
                print(f"   Mit Fläche: {with_area}")
                print(f"   Mit Datum: {with_date}")
                print(f"   Mit Firma: {with_company}")
        
        return True
    except Exception as e:
        print(f"❌ Fehler beim Export: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 80)
    print("🚀 AUTO-EXPORT NACH CRAWL-ABSCHLUSS")
    print("=" * 80)
    print()
    
    # Warte auf Abschluss
    wait_for_completion()
    
    # Erstelle Export
    success = create_export()
    
    if success:
        print("\n✅ Fertig! Export ist bereit.")
    else:
        print("\n❌ Export fehlgeschlagen.")
        sys.exit(1)






