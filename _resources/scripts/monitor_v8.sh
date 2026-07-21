#!/bin/bash
# Monitor Wan 2.2 v8 jobs, download, merge, upload
set -e

PIDS_FILE="/home/pi5/ai_cartoon/happy_children/06-video/wan_v8_pids.json"
OD="/home/pi5/ai_cartoon/happy_children/06-video"
AD="/home/pi5/ai_cartoon/happy_children/07-final"
WIN_HOST="liuyi@192.168.178.104"
WIN_OUT="D:/ComfyUI_Mie_2026_V8.0/ComfyUI/output"
TOTAL=12

echo "=== Monitoring Wan 2.2 v8 (${TOTAL} shots) ==="

declare -A dm
c=0

while [ $c -lt $TOTAL ]; do
  for sn in $(seq -w 1 12); do
    [ "${dm[$sn]}" = "1" ] && continue
    
    r=$(python3 -c "
import urllib.request,json
pid_prefix='$(python3 -c "import json; d=json.load(open('$PIDS_FILE')); print(d.get('$sn',''))")'[:12]
h=json.loads(urllib.request.urlopen('http://192.168.178.104:8188/history',timeout=10).read())
for pid,e in h.items():
    if pid.startswith(pid_prefix) and e.get('status',{}).get('completed'):
        ss=e['status']['status_str']
        for n,o in e.get('outputs',{}).items():
            for g in o.get('gifs',[]):
                print(f'{ss} {g[\"filename\"]}')
                exit(0)
print('WAIT')
" 2>&1)
    
    if [[ "$r" == success* ]]; then
      fn=$(echo "$r" | awk '{print $2}')
      ((c++)); dm[$sn]=1
      echo "[$(date +%H:%M:%S)] Shot $sn: success ($c/$TOTAL)"
      scp -q "${WIN_HOST}:${WIN_OUT}/${fn}" "${OD}/ep01_shot${sn}_v8.mp4"
    fi
  done
  [ $c -lt $TOTAL ] && sleep 20
done

echo ""
echo "=== Merging v8 ==="

ffmpeg -y \
  -i ${OD}/ep01_shot01_v8.mp4 -i ${OD}/ep01_shot02_v8.mp4 \
  -i ${OD}/ep01_shot03_v8.mp4 -i ${OD}/ep01_shot04_v8.mp4 \
  -i ${OD}/ep01_shot05_v8.mp4 -i ${OD}/ep01_shot06_v8.mp4 \
  -i ${OD}/ep01_shot07_v8.mp4 -i ${OD}/ep01_shot08_v8.mp4 \
  -i ${OD}/ep01_shot09_v8.mp4 -i ${OD}/ep01_shot10_v8.mp4 \
  -i ${OD}/ep01_shot11_v8.mp4 -i ${OD}/ep01_shot12_v8.mp4 \
  -i ${AD}/ep01_shot05_michael.wav -i ${AD}/ep01_shot07_michael.wav \
  -i ${AD}/ep01_shot08_granny.wav -i ${AD}/ep01_shot10_granny.wav \
  -i ${AD}/ep01_shot11_michael.wav -i ${AD}/ep01_shot12_narrator.wav \
  -i ${AD}/bgm_ep01.flac \
  -filter_complex "
    [0:v][1:v][2:v][3:v][4:v][5:v][6:v][7:v][8:v][9:v][10:v][11:v]concat=n=12:v=1:a=0[v];
    [12:a]adelay=17240|17240[a5];
    [13:a]adelay=23360|23360[a7];
    [14:a]adelay=27420|27420[a8];
    [15:a]adelay=37540|37540[a10];
    [16:a]adelay=41600|41600[a11];
    [17:a]adelay=45660|45660[a12];
    [a5][a7][a8][a10][a11][a12]amix=6:normalize=0[voices];
    [18:a]volume=0.3[bgm];
    [voices][bgm]amix=2:normalize=0[a]
  " -map "[v]" -map "[a]" -c:v libx264 -preset fast -crf 23 -c:a aac -b:a 192k -ar 44100 -shortest \
  ${AD}/ep01_v8.mp4 2>&1 | tail -2

echo ""
ls -lh ${AD}/ep01_v8.mp4
scp -O ${AD}/ep01_v8.mp4 TopOnSky@192.168.178.20:/volume1/photo/n8n_workflow/output/happy_children/
echo "=== v8 complete! ==="
