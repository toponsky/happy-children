#!/bin/bash
# Monitor 10 shot Flux generations
OD="/home/pi5/ai_cartoon/happy_children/05-source"
mkdir -p "$OD"
declare -A done; count=0

while [ $count -lt 10 ]; do
  # Check output directory for new files
  files=$(ssh liuyi@192.168.178.104 "cmd /c \"dir /b /o-d D:\\ComfyUI_Mie_2026_V8.0\\ComfyUI\\output\\ep01_shot0*_00001_.png 2>nul && dir /b /o-d D:\\ComfyUI_Mie_2026_V8.0\\ComfyUI\\output\\ep01_shot1*_00001_.png 2>nul\"" 2>/dev/null)
  
  for fn in $files; do
    sn=$(echo "$fn" | grep -oP 'shot\d+')
    [ "${done[$sn]}" = "1" ] && continue
    scp -q "liuyi@192.168.178.104:D:/ComfyUI_Mie_2026_V8.0/ComfyUI/output/$fn" "$OD/ep01_${sn}_v1.png"
    done[$sn]=1
    count=$((count+1))
    echo "[$(date +%H:%M:%S)] $sn downloaded ($count/10) -> $OD/ep01_${sn}_v1.png"
  done
  
  [ $count -lt 10 ] && sleep 30
done

echo "=== All 10 source images done ==="
ls -lh "$OD"/ep01_shot*_v1.png
