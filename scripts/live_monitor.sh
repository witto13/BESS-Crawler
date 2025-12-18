#!/bin/bash
# Live Monitor für Crawl-Fortschritt

echo "═══════════════════════════════════════════════════════════════════════════════"
echo "🔍 BESS/PV CRAWL - LIVE MONITOR"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo ""

while true; do
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📊 $(date '+%H:%M:%S') - DATENBANK-STATISTIKEN:"
    echo ""
    
    docker compose exec db psql -U bess -d bess -c "
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN bess_score >= 1 THEN 1 END) as bess_1plus,
            COUNT(CASE WHEN bess_score >= 3 THEN 1 END) as bess_3plus,
            COUNT(CASE WHEN grid_score >= 1 THEN 1 END) as grid_1plus,
            COUNT(CASE WHEN grid_score >= 3 THEN 1 END) as grid_3plus,
            COUNT(CASE WHEN confidence = 'high' THEN 1 END) as high_conf
        FROM procedures 
        WHERE procedure_id != 'test-proc-999';
    " 2>/dev/null | grep -v "level=warning" | tail -3
    
    echo ""
    echo "📈 EXTRAKTIONEN:"
    docker compose exec db psql -U bess -d bess -c "
        SELECT 
            COUNT(CASE WHEN capacity_mw IS NOT NULL OR capacity_mwh IS NOT NULL THEN 1 END) as with_cap,
            COUNT(CASE WHEN area_hectares IS NOT NULL THEN 1 END) as with_area,
            COUNT(CASE WHEN decision_date IS NOT NULL THEN 1 END) as with_date,
            COUNT(CASE WHEN developer_company IS NOT NULL THEN 1 END) as with_company
        FROM procedures 
        WHERE procedure_id != 'test-proc-999';
    " 2>/dev/null | grep -v "level=warning" | tail -3
    
    echo ""
    echo "📋 QUEUE:"
    QUEUE=$(docker compose exec redis redis-cli LLEN crawl 2>/dev/null | grep -v "level=warning" | tr -d ' ')
    echo "   Jobs in Queue: $QUEUE"
    
    echo ""
    echo "⚙️  WORKER STATUS (letzte 3 Zeilen):"
    docker compose logs worker --tail=3 2>/dev/null | grep -E "(Progress|completed|Job completed)" | tail -3
    
    echo ""
    echo "⏱️  Nächstes Update in 5 Sekunden... (Ctrl+C zum Beenden)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    sleep 5
done






