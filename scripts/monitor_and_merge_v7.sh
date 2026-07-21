#!/bin/bash
# Simplified: monitor Wan 2.2 v7 by checking history for completed outputs
set -e

OD="/home/pi5/ai_cartoon/happy_children/06-video"
AD="/home/pi5/ai_cartoon/happy_children/07-final"
WIN_HOST="liuyi@192.168.178.104"
WIN_OUT="D:/ComfyUI_Mie_2026_V8.0/ComfyUI/output"

SHOTS="01 02 05 06 09 10 11 12"
TOTAL=8

echo "=== Monitoring Wan 2.2 v7 ($TOTAL shots) ==="
declare -A dm
c=0

while [ $c -lt $TOTAL ]; do
  # Get all completed outputs from history in one call
  completed=$(python3 -c "
import urllib.request,json
h=json.loads(urllib.request.urlopen('http://192.168.178.104:8188/history',timeout=10).read())
for pid,e in h.items():
    if e.get('status',{}).get('completed') and e['status'].get('status_str')=='success':
        for n,o in e.get('outputs',{}).items():
            for g in o.get('gifs',[]):
                fn=g.get('filename','')
                if fn.startswith('ep01_shot') and 'v6' in fn:
                    print(f'{fn}')
" 2>&1)

  for sn in $SHOTS; do
    [ "${dm[$sn]}" = "1" ] && continue
    prefix="ep01_shot${sn}_v6"
    fn=$(echo "$completed" | grep "^${prefix}" | head -1)
    if [ -n "$fn" ]; then
      ((c++)); dm[$sn]=1
      echo "[$(date +%H:%M:%S)] Shot $sn: success ($c/$TOTAL)"
      scp -q "${WIN_HOST}:${WIN_OUT}/${fn}" "${OD}/ep01_shot${sn}_v7.mp4"
    fi
  done
  
  [ $c -lt $TOTAL ] && sleep 30
done

echo ""
echo "=== All $TOTAL shots done! Merging v7 ==="

# Merge with corrected audio delays
ffmpeg -y \
  -i ${OD}/ep01_shot01_v7.mp4 \
  -i ${OD}/ep01_shot02_v7.mp4 \
  -i ${OD}/ep01_shot03_anim_fixed.mp4 \
  -i ${OD}/ep01_shot04_anim_fixed.mp4 \
  -i ${OD}/ep01_shot05_v7.mp4 \
  -i ${OD}/ep01_shot06_v7.mp4 \
  -i ${OD}/ep01_shot07_anim_fixed.mp4 \
  -i ${OD}/ep01_shot08_anim_fixed.mp4 \
  -i ${OD}/ep01_shot09_v7.mp4 \
  -i ${OD}/ep01_shot10_v7.mp4 \
  -i ${OD}/ep01_shot11_v7.mp4 \
  -i ${OD}/ep01_shot12_v7.mp4 \
  -i ${AD}/ep01_shot05_michael.wav \
  -i ${AD}/ep01_shot07_michael.wav \
  -i ${AD}/ep01_shot08_granny.wav \
  -i ${AD}/ep01_shot10_granny.wav \
  -i ${AD}/ep01_shot11_michael.wav \
  -i ${AD}/ep01_shot12_narrator.wav \
  -i ${AD}/bgm_ep01.flac \
  -filter_complex "
    [0:v][1:v][2:v][3:v][4:v][5:v][6:v][7:v][8:v][9:v][10:v][11:v]concat=n=12:v=1:a=0[v];
    [12:a]adelay=17250|17250[a5];
    [13:a]adelay=23375|23375[a7];
    [14:a]adelay=27438|27438[a8];
    [15:a]adelay=37563|37563[a10];
    [16:a]adelay=41625|41625[a11];
    [17:a]adelay=45688|45688[a12];
    [a5][a7][a8][a10][a11][a12]amix=6:normalize=0[voices];
    [18:a]volume=0.3[bgm];
    [voices][bgm]amix=2:normalize=0[a]
  " -map "[v]" -map "[a]" -c:v libx264 -preset fast -crf 23 -c:a aac -b:a 192k -ar 44100 -shortest \
  ${AD}/ep01_v7.mp4 2>&1 | tail -2

echo ""
ls -lh ${AD}/ep01_v7.mp4
echo ""

# Upload to NAS
scp -O ${AD}/ep01_v7.mp4 TopOnSky@192.168.178.20:/volume1/photo/n8n_workflow/output/happy_children/
echo "=== NAS ✓ ==="
echo "v7: ep01_v7.mp4"
