#!/bin/bash
set -e
cd "$(dirname "$0")"
NB="bun $HOME/tools/nano-banana-2/src/cli.ts"

PREFIX="Chibi anime style character, cute martial arts wuxia swordsman, big head small body ratio about 2.5 to 1, wearing flowing traditional Chinese"
SUFFIX="long black hair tied up with a red ribbon headband, large expressive eyes, soft cel-shading, full body view, facing right side view, clean lines, consistent character design, game sprite asset"

echo "⚔ 武俠修煉場素材生成器"
echo "========================"
echo ""

echo "🖼  [1/43] 生成背景..."
$NB "A mystical wuxia martial arts training courtyard at night, wide panoramic view of an ancient Chinese mountain academy, distinct training zones, meditation area on left, sword training ground in center, library pavilion on right, raised stone platform for qi training, stone path at bottom, bamboo forest both sides, stone lanterns, full moon, falling leaves, fireflies, traditional Chinese anime style, atmospheric night, game environment, no characters, empty scene" \
  -s 2K -a 16:9 -o bg

COLORS=("deep blue" "crimson red" "jade green" "royal purple" "warm brown" "teal cyan")
NAMES=("blue" "red" "green" "purple" "brown" "teal")
STATES=("idle" "thinking" "writing" "reading" "running" "done" "walk")
DESCS=(
  "sitting cross-legged meditating, eyes closed, serene, hands on knees, faint qi aura, robe spread on ground"
  "standing arms raised channeling qi energy, swirling green blue energy around hands, focused expression, hair flowing upward"
  "dynamic sword thrust attack pose, silver jian sword, bow stance, fierce expression, sword energy slash, robe flowing behind"
  "standing reading ancient scroll with both hands, scroll unrolled showing text, curious studious expression, scholarly pose"
  "running high speed sprint, light footwork, wind blur trailing, robe streaming backward, excited expression"
  "traditional fist-palm salute, right fist left palm at chest, gentle smile, golden sparkle particles, dignified accomplished"
  "walking casually relaxed stride, one foot forward mid-walk, arms swinging, pleasant expression, robe swaying gently"
)
EMOJIS=("🧘" "🌀" "⚔" "📜" "💨" "✨" "🚶")

COUNT=1
TOTAL=43

for i in "${!COLORS[@]}"; do
  COLOR="${COLORS[$i]}"
  NAME="${NAMES[$i]}"
  echo ""
  echo "🎨 生成 ${NAME} 袍角色..."

  for j in "${!STATES[@]}"; do
    COUNT=$((COUNT+1))
    echo "  ${EMOJIS[$j]} [$COUNT/$TOTAL] ${NAME}-${STATES[$j]}"
    $NB "$PREFIX $COLOR hanfu robe with gold sash belt, $SUFFIX, ${DESCS[$j]}" \
      -s 1K -a 1:1 -t -o "${NAME}-${STATES[$j]}"
    sleep 2
  done
done

echo ""
echo "✅ 完成！共 $TOTAL 張素材已生成"
echo "把 index.html 放到這個資料夾就能用了"
