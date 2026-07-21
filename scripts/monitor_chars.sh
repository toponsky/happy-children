#!/bin/bash
PIDS=("5ffe452e-47d9-4855-9953-b666eafd1692" "ac379df4-17c6-4bc6-88dc-7b83d23490c3")
NAMES=("R1_michael" "R2_grandma_noglass")
PFS=("ep01_ref_michael" "ep01_ref_grandma_noglass")
OD="/home/pi5/ai_cartoon/happy_children/00-characters"
declare -A done; count=0

while [ $count -lt 2 ]; do
  for i in "${!PIDS[@]}"; do
    pid="${PIDS[$i]}"; nm="${NAMES[$i]}"; pf="${PFS[$i]}"
    [ "${done[$nm]}" = "1" ] && continue
    r=$(ssh liuyi@192.168.178.104 "D:\\ComfyUI_Mie_2026_V8.0\\python_embeded\\python.exe -c \"import urllib.request,json; h=json.loads(urllib.request.urlopen('http://127.0.0.1:8188/history/$pid',timeout=10).read()); ss=h.get('status',{}).get('status_str','?'); fn=''; [fn:=g.get('filename','') for no in h.get('outputs',{}).values() for g in no.get('images',[])]; print(f'{ss}|{fn}')\"" 2>/dev/null)
    if [ -n "$r" ]; then
      st="${r%%|*}"; fn="${r#*|}"
      echo "[$(date +%H:%M:%S)] $nm: $st"
      if [ "$st" = "success" ] && [ -n "$fn" ]; then
        scp -q "liuyi@192.168.178.104:D:/ComfyUI_Mie_2026_V8.0/ComfyUI/output/$fn" "$OD/${nm}.png"
        count=$((count+1)); done[$nm]=1; echo "  -> $OD/${nm}.png"
      fi
    fi
  done
  [ $count -lt 2 ] && sleep 20
done
echo "=== Both done ==="
ls -lh "$OD"/R1_michael.png "$OD"/R2_grandma_noglass.png
