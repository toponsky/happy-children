#!/bin/bash
# Monitor 3 prop jobs and download results
PIDS=("d3779bb5-e3aa-40d5-99ec-d67061acdb0d" "968ebab8-bb57-45a4-90af-609571123ac2" "bf7dcda5-e21d-420b-95d8-b27e6436571e")
NAMES=("R4_glasses" "R5_wheelchair" "R6_bag")
PREFIXES=("ep01_ref_glasses" "ep01_ref_wheelchair" "ep01_ref_bag")
OD="/home/pi5/ai_cartoon/happy_children/00-characters"
declare -A done
count=0

while [ $count -lt 3 ]; do
  for i in "${!PIDS[@]}"; do
    pid="${PIDS[$i]}"; nm="${NAMES[$i]}"; pf="${PREFIXES[$i]}"
    [ "${done[$nm]}" = "1" ] && continue
    
    r=$(ssh liuyi@192.168.178.104 "python3 -c \"
import urllib.request,json
h=json.loads(urllib.request.urlopen('http://127.0.0.1:8188/history/$pid',timeout=10).read())
ss=h.get('status',{}).get('status_str','?')
fn=''
for no in h.get('outputs',{}).values():
    for g in no.get('images',[]):
        fn=g.get('filename',''); break
print(f'{ss}|{fn}')
\"" 2>/dev/null)
    
    if [ -n "$r" ]; then
      st="${r%%|*}"; fn="${r#*|}"
      echo "[$(date +%H:%M:%S)] $nm: $st"
      if [ "$st" = "success" ] && [ -n "$fn" ]; then
        scp -q "liuyi@192.168.178.104:D:/ComfyUI_Mie_2026_V8.0/ComfyUI/output/$fn" "$OD/${nm}.png"
        count=$((count+1)); done[$nm]=1
        echo "  -> $OD/${nm}.png"
      fi
    fi
  done
  [ $count -lt 3 ] && sleep 20
done
echo "=== All 3 props done ==="
ls -lh $OD/R4_glasses.png $OD/R5_wheelchair.png $OD/R6_bag.png 2>/dev/null
