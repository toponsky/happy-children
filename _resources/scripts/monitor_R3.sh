#!/bin/bash
PID="46a433fd-6ba2-4e77-ba58-ffda699c1085"
OD="/home/pi5/ai_cartoon/happy_children/00-characters"

while true; do
  r=$(ssh liuyi@192.168.178.104 "curl -s http://127.0.0.1:8188/history/$PID" 2>/dev/null)
  st=$(echo "$r" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status',{}).get('status_str','?'))" 2>/dev/null)
  fn=$(echo "$r" | python3 -c "
import sys,json
d=json.load(sys.stdin)
for no in d.get('outputs',{}).values():
    for g in no.get('images',[]): print(g.get('filename','')); exit()
" 2>/dev/null)
  
  if [ "$st" = "success" ] && [ -n "$fn" ]; then
    echo "[$(date +%H:%M:%S)] R3: $st"
    scp -q "liuyi@192.168.178.104:D:/ComfyUI_Mie_2026_V8.0/ComfyUI/output/$fn" "$OD/R3_grandma_glasses.png"
    ls -lh "$OD/R3_grandma_glasses.png"
    break
  elif [ "$st" = "error" ]; then
    echo "R3 ERROR: $r"
    break
  fi
  echo "[$(date +%H:%M:%S)] waiting... (status=$st)"
  sleep 15
done
