# Codex v2 桌宠跨电脑复用流程

这套流程把任意角色参考图转换成 Codex v2 桌宠。目标不是简单缩放原图，而是先建立一个稳定的桌宠角色基准，再分别生成动作行、视线方向、透明图集和安装包。

适用范围：安装了 Codex、Python 3.11+ 和 `imagegen` / `hatch-pet` skills 的 macOS、Linux 或 Windows 电脑。不同电脑可以使用不同的图像生成供应商，但认证凭据和 API 地址必须匹配。

## 最终规格

| 项目 | 规格 |
| --- | --- |
| 图集版本 | `spriteVersionNumber: 2` |
| 网格 | 8 列 × 11 行 |
| 单格 | 192 × 208 px |
| 总尺寸 | 1536 × 2288 px |
| 格式 | RGBA PNG 或 lossless WebP |
| 标准动作 | 9 行 |
| 视线方向 | 16 个，顺时针排列 |

标准动作固定为：

| 行 | 状态 | 有效帧数 |
| ---: | --- | ---: |
| 0 | `idle` | 6 |
| 1 | `running-right` | 8 |
| 2 | `running-left` | 8 |
| 3 | `waving` | 4 |
| 4 | `jumping` | 5 |
| 5 | `failed` | 8 |
| 6 | `waiting` | 6 |
| 7 | `running`（处理任务，不是跑步） | 6 |
| 8 | `review` | 6 |
| 9 | `000` 到 `157.5` | 8 |
| 10 | `180` 到 `337.5` | 8 |

`000` 表示向上，不是正面静止。没有方向输入时使用 `idle`。

## 一、一次性环境准备

需要以下组件：

- Codex Desktop、Codex CLI 或 IDE 扩展。
- Python 3.11 或更高版本。
- Pillow。
- `${CODEX_HOME}/skills/.system/imagegen`。
- `${CODEX_HOME}/skills/hatch-pet`。
- 本仓库的 `scripts/imagegen-from-codex-auth.py`，仅在使用 Codex 自定义模型供应商时需要。

默认路径：

- macOS / Linux：`CODEX_HOME=$HOME/.codex`
- Windows：`CODEX_HOME=%USERPROFILE%\.codex`

环境预检：

```bash
python scripts/check-hatch-pet-env.py --workspace .
```

必须使用 CLI 生成时：

```bash
python scripts/check-hatch-pet-env.py --workspace . --require-cli
```

PowerShell：

```powershell
py scripts\check-hatch-pet-env.py --workspace . --require-cli
```

预检脚本不会打印密钥，只报告凭据来源是否存在、shell key 是否与 Codex 保存的凭据相同，以及可选生成通道。预检不发送真实 API 请求，因此只能证明配置完整，不能证明余额、权限或服务状态正常。

## 二、选择图像生成通道

按以下优先级选择：

1. Codex 当前任务内置的 `$imagegen`。它使用 Codex 额度，不需要 `OPENAI_API_KEY`。
2. 官方 OpenAI API CLI。适用于已设置有效 `OPENAI_API_KEY` 的电脑。
3. Codex 自定义供应商桥接。适用于 Codex 通过 OneAPI 或企业代理登录的电脑。

### 官方 API

设置环境变量，不要把密钥写进仓库或聊天：

```bash
export OPENAI_API_KEY="..."
python "$CODEX_HOME/skills/.system/imagegen/scripts/image_gen.py" --help
```

PowerShell：

```powershell
$env:OPENAI_API_KEY="..."
py "$env:USERPROFILE\.codex\skills\.system\imagegen\scripts\image_gen.py" --help
```

### Codex 自定义供应商

当 `~/.codex/config.toml` 中存在 `model_provider` 和对应的 `base_url`，而 `auth.json` 保存了该供应商的凭据时，使用：

```bash
python scripts/imagegen-from-codex-auth.py edit --help
```

这个桥接会同时读取 Codex 保存的凭据与供应商地址。不要只拿企业代理的 key 请求 `api.openai.com`，否则通常会得到 `401 invalid_api_key`。

## 三、准备输入

最少需要一张角色参考图。推荐：

- 全身或接近全身，轮廓完整。
- 正面或三分之四正面。
- 发型、脸、服装、颜色和标志性道具清晰。
- 背景干净；透明背景最好，但不是必须。

生成前写一份身份锁定说明：

- 必须保留：脸型、发型、主色、服装、道具、左右不对称元素。
- 可以简化：过细纹理、小首饰、难以在 192×208 中读取的装饰。
- 必须避免：文字、水印、地面、阴影、漂浮特效、额外道具。

长发、翅膀、裙摆、琴弦等细结构应改成连续、较粗、可连接的桌宠轮廓。道具要与手或身体接触，避免透明化后成为独立碎片。

## 四、创建标准运行目录

先从 Codex 获取 bundled Python 路径；如果无法获取，使用已安装 Pillow 的 Python 3.11+。

POSIX 示例：

```bash
export CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
export HATCH_PET="$CODEX_HOME/skills/hatch-pet"
export PYTHON="python3"
export RUN_DIR="$PWD/generated-pets/<pet-id>"

"$PYTHON" "$HATCH_PET/scripts/prepare_pet_run.py" \
  --pet-name "<显示名称>" \
  --pet-id "<pet-id>" \
  --description "<一句话描述>" \
  --reference "/absolute/path/reference.png" \
  --output-dir "$RUN_DIR" \
  --pet-notes "<身份锁定说明>" \
  --style-preset auto \
  --style-notes "<风格与简化规则>" \
  --chroma-key auto
```

该命令会生成：

```text
<run-dir>/
├── pet_request.json
├── imagegen-jobs.json
├── prompts/
├── decoded/
├── frames/
├── final/
├── qa/
└── references/layout-guides/
```

`pet_request.json` 是运行规格，`imagegen-jobs.json` 是依赖图。不要凭记忆跳过其中的输入图。

## 五、生成主视觉

读取 `prompts/base-pet.md`，将所有列出的参考图传给 `$imagegen`。

基准图必须满足：

- 单个、居中、完整全身桌宠。
- 在 192×208 中仍可识别。
- 使用运行目录指定的纯色 chroma key。
- 无场景、文字、边框、阴影或漂浮特效。

通过后复制为：

```text
decoded/base.png
references/canonical-base.png
```

后续所有动作都必须同时参考原图和 `canonical-base.png`。原图锁定人物身份，基准图锁定桌宠比例与画风。

## 六、生成九个标准动作

推荐依赖顺序：

1. `idle` 与 `running-right`。
2. 判断 `running-left` 是否允许镜像。
3. 并行生成 `waving`、`jumping`、`failed`、`waiting`、`running`、`review`。

只有角色和道具完全左右对称时，才允许用 `derive_running_left_from_running_right.py` 逐帧镜像。眼罩、单侧发饰、持剑手、竖琴等都会让镜像改变身份，此时必须独立生成左移动作。

每条 row 必须：

- 精确帧数。
- 角色完整、等比例、稳定基线。
- 每帧之间有从顶到底连续的纯色间隔。
- 头发、裙摆、道具和描边不得连接相邻帧。
- 不得复制 layout guide 的边框、文字或底色结构。

每生成一行立刻检查：

```bash
"$PYTHON" "$HATCH_PET/scripts/extract_strip_frames.py" \
  --decoded-dir "$RUN_DIR/decoded" \
  --output-dir "$RUN_DIR/qa/rows/<state>/frames" \
  --states "<state>" \
  --method auto

"$PYTHON" "$HATCH_PET/scripts/inspect_frames.py" \
  --frames-root "$RUN_DIR/qa/rows/<state>/frames" \
  --json-out "$RUN_DIR/qa/rows/<state>/review.json" \
  --states "<state>" \
  --require-components
```

只有 `review.json` 的 `ok` 为 `true` 才能将任务标记为完成。

## 七、组装并检查 8×9 中间图集

```bash
"$PYTHON" "$HATCH_PET/scripts/extract_strip_frames.py" \
  --decoded-dir "$RUN_DIR/decoded" \
  --output-dir "$RUN_DIR/frames" \
  --states all \
  --method auto

"$PYTHON" "$HATCH_PET/scripts/inspect_frames.py" \
  --frames-root "$RUN_DIR/frames" \
  --json-out "$RUN_DIR/qa/review.json" \
  --require-components

"$PYTHON" "$HATCH_PET/scripts/compose_atlas.py" \
  --frames-root "$RUN_DIR/frames" \
  --output "$RUN_DIR/final/spritesheet.png" \
  --webp-output "$RUN_DIR/final/spritesheet.webp"

"$PYTHON" "$HATCH_PET/scripts/make_contact_sheet.py" \
  "$RUN_DIR/final/spritesheet.webp" \
  --output "$RUN_DIR/qa/contact-sheet.png"

"$PYTHON" "$HATCH_PET/scripts/render_animation_previews.py" \
  --frames-root "$RUN_DIR/frames" \
  --output-dir "$RUN_DIR/qa/previews"
```

这个 8×9 图集只是中间产物，不能作为新桌宠发布。

## 八、生成 16 个视线方向

先写 `qa/look-mechanics.md`，说明：

- 什么部位先引导视线。
- 眼睛、眼睑、头、颈、身体和道具如何跟随。
- 哪个部位保持锚定。
- 左右转向时哪些面可见、哪些被遮挡。
- 道具是否延迟、转向或保持稳定。

人形角色通常采用：眼睛先动，眼睑与眉形配合，头颈和上身轻微跟随；脚、裙摆底部或身体底座保持固定。禁止旋转整张精灵来伪造视线。

### 四方向锚点

一次生成四格，顺序固定：

```text
000 up | 090 screen-right | 180 down | 270 screen-left
```

左右方向是观看者屏幕坐标。人形角色要检查瞳孔、鼻尖和下巴是否越过头部中心。

提取并检查：

```bash
"$PYTHON" "$HATCH_PET/scripts/extract_cardinal_anchors.py" \
  --strip "$RUN_DIR/decoded/look-cardinals.png" \
  --output-dir "$RUN_DIR/decoded/look-anchors" \
  --chroma-key "<pet_request 中的色键>" \
  --json-out "$RUN_DIR/qa/cardinal-anchors.json"

"$PYTHON" "$HATCH_PET/scripts/compose_cardinal_anchor_strip.py" \
  --anchors-dir "$RUN_DIR/decoded/look-anchors" \
  --output "$RUN_DIR/decoded/look-anchors-approved.png"
```

### Row 9

顺序固定：

```text
000, 022.5, 045, 067.5, 090, 112.5, 135, 157.5
```

八个姿态必须作为一个 coherent row 一次生成。通过后先注册 row 9，记录固定尺度和基线。

### Row 10

顺序固定：

```text
180, 202.5, 225, 247.5, 270, 292.5, 315, 337.5
```

必须同时参考四方向锚点和完成的 row 9。`157.5→180` 与 `337.5→000` 是跨行连续性重点。

## 九、最终装配和唯一一次透明边缘清理

使用 skill 中的 `assemble_extended_atlas.py` 将两条方向行装配到 8×9 中间图集。row 10 必须复用 row 9 已批准的注册尺度。

装配完成后，对最终 8×11 图集执行且只执行一次：

```bash
"$PYTHON" "$HATCH_PET/scripts/despill_chroma_edges.py" \
  "$RUN_DIR/final/spritesheet-extended.png" \
  --output "$RUN_DIR/final/spritesheet-extended.png" \
  --webp-output "$RUN_DIR/final/spritesheet-extended.webp" \
  --chroma-key "<色键>" \
  --json-out "$RUN_DIR/qa/chroma-despill-extended.json"

"$PYTHON" "$HATCH_PET/scripts/validate_atlas.py" \
  "$RUN_DIR/final/spritesheet-extended.webp" \
  --json-out "$RUN_DIR/final/validation-extended.json" \
  --chroma-key "<色键>" \
  --require-v2
```

必须满足：

- `1536×2288`。
- RGBA。
- `spriteVersionNumber: 2`。
- 有效格非空，无效格全透明。
- 透明像素 RGB 残留为 0。
- 验证报告无错误。

## 十、方向盲测与最终视觉验收

生成两张 QA 图：

```bash
"$PYTHON" "$HATCH_PET/scripts/make_direction_qa_sheet.py" \
  "$RUN_DIR/final/spritesheet-extended.webp" \
  --output "$RUN_DIR/qa/look-directions.png"

"$PYTHON" "$HATCH_PET/scripts/make_direction_blind_qa_sheet.py" \
  "$RUN_DIR/final/spritesheet-extended.webp" \
  --output "$RUN_DIR/qa/direction-blind-pairs.png" \
  --answer-key "$RUN_DIR/qa/direction-blind-answer-key.json"
```

让三名互相隔离的检查者只看 `direction-blind-pairs.png`，不能看到标签、答案、提示词或其他人的判断。用严格多数票合并，再用隐藏答案验证。

四个主方向是硬门槛：`000 up`、`090 right`、`180 down`、`270 left`。主方向错误必须重做。中间角度的轻微不明确可以作为警告，但带标签的连续播放不能出现错象限、倒退、身份变化或明显跳帧。

最后检查：

- `qa/contact-sheet-extended.png`
- `qa/look-directions.png`
- `qa/previews/*.gif`
- `qa/look-continuity.json`
- `qa/direction-blind-validation.json`
- `final/validation-extended.json`

## 十一、安装

最终目录必须只有同一版本的 manifest 和 spritesheet：

```text
${CODEX_HOME}/pets/<pet-id>/
├── pet.json
└── spritesheet.webp
```

`pet.json`：

```json
{
  "id": "<pet-id>",
  "displayName": "<显示名称>",
  "description": "<一句话描述>",
  "spriteVersionNumber": 2,
  "spritesheetPath": "spritesheet.webp"
}
```

安装后再次对安装目录的 `spritesheet.webp` 运行 `validate_atlas.py --require-v2`。项目文件和安装文件的 SHA-256 应一致。

通过 Codex UI 选择该桌宠；需要手工配置时，备份 `config.toml` 后设置：

```toml
[desktop]
selected-avatar-id = "custom:<pet-id>"
```

重启 Codex App 使其重新加载。

## 十二、常见故障和修复策略

### `401 invalid_api_key`

先核对 key 属于哪个供应商。企业 OneAPI 凭据不能直接请求 `api.openai.com`。同时传递正确 key 和 `base_url`，或使用 `imagegen-from-codex-auth.py`。

### API 长时间无响应

- 检查进程是否仍存在、输出文件是否已经写出。
- 多参考图任务可等待 5–10 分钟。
- 超时后终止该单次请求，不要重启整个流程。
- 保持模型不变，将 `quality` 从 `high` 降到 `medium` 或 `low` 后重试。

### 看起来有足够帧，但组件提取失败

通常是长发、裙摆、道具或描边连接了相邻帧。重生成整行，要求每帧之间存在从顶到底连续的 chroma-key 竖向间隔。不要手工切开前景。

只有源条带本身槽位稳定、失败纯粹来自组件识别时，才可使用 `stable-slots`，并必须查看 GIF 是否发生尺度跳变。

### 左右方向被模型画反

- 明确使用“画布左边缘 / 画布右边缘”，不要只写角色左/右。
- 指定鼻尖、瞳孔、下巴相对头部中心的位置。
- 先批准四方向锚点，再生成中间角度。
- 如果整行大部分方向正确，编辑完整 row，只重绘头部和上身方向；不要拼补单格，也不要程序镜像人形角色。

### 方向正确但跨行尺度跳变

编辑完整 row，统一调整全部八个姿态的尺度，保持脚底锚点、槽位中心、方向语义和道具连接。重新装配后比较：

- `centerDelta`
- `areaRatio`
- `diffPixels`

数值警告只是复核证据；最终以正常桌宠尺寸下是否真的出现跳变为准。

### 修复边缘问题后方向又漂移

将“布局变化”和“语义变化”拆成两轮整行编辑。第一轮只改朝向，第二轮只改统一尺度或间隔。每轮都重跑确定性检查和独立视觉 QA。

## 十三、最简复用指令

在安装好 skills 的新电脑上，附上角色图后可直接发送：

```text
$hatch-pet
把附图角色制作成 Codex v2 桌宠。保留角色的脸、发型、服装、主色、左右不对称元素和标志性道具；将细节简化为 192×208 可读的紧凑全身桌宠。完成 9 个标准动作、4 个主方向锚点、16 个顺时针视线方向、透明 8×11 图集、三路方向盲测、最终视觉 QA，并安装到本机 Codex pets 目录。发现单行失败时只修复完整的失败行，不拼补单格。优先使用内置 imagegen；若不可用，先确认再使用与当前供应商匹配的 CLI 认证。
```

这条指令适用于大多数角色；具体风格、名字和道具约束可在末尾补充。
