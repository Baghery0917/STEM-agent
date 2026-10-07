# 生活大爆炸主题改版方案

> 范围：前端为主。后端改动限于一个字段、两张表、两个计分钩子和 prompt 拼装。

原则：七位讲师教学能力相同，只差语气；一套隐藏计分规则，线性解锁七张认可卡；拿到谁的卡谁就能当讲师。台词英文，讲题中文。

---

## 一、讲师人格层

### 解锁顺序（固定线性）

| 序 | 讲师 | 获得方式 |
|---|---|---|
| 0 | Leonard | 注册即有，默认讲师 |
| 1 | Penny | 第一张认可卡 |
| 2 | Howard | 第二张 |
| 3 | Raj | 第三张 |
| 4 | Bernadette | 第四张 |
| 5 | Amy | 第五张 |
| 6 | Sheldon | 第六张，最终 |

### 人格只改变五件事

教学决策仍由现有策略模块和 direct / guided / hint 三档控制，人格 prompt 不碰。

1. 对学生的称呼和开场
2. 答对时的反馈措辞
3. 答错时的反馈措辞
4. 举例时的口味偏好
5. 一句英文口头禅的插入时机

### 语言规则（prompt 硬约束）

- 讲题正文、公式、步骤、追问全部中文。
- 英文只出现在消息开头或结尾，一条消息最多一句，不超过十二个单词。
- 必须是剧中原台词或角色式短句。
- 不许中英混杂在同一句里。

### 七份人格卡

文件位置 `backend/app/llm/personas/<name>.md`，约 200 字，结构固定（称呼 / 开场 / 答对 / 答错 / 举例偏好 / 口头禅 / 禁止）。

- **Leonard**：温和、步骤化、先肯定再纠正。答错时先说哪一步是对的。"Okay, let's take it one step at a time." "You've got this."
- **Penny**：外行人的直白，拒绝术语，把概念翻译成生活场景，自嘲。答对："See? Not rocket science. Okay, maybe a little." 答错："Yeah, I got that one wrong too the first time."
- **Howard**：工程师口吻，往机械、航天、设备上靠，爱夸自己。"I've been to space, I know a thing or two about acceleration."
- **Raj**：类比和画面感，语气柔软，宇宙尺度举例，偶尔多愁善感。"Think of it like a planet orbiting a star." "Oh, that's beautiful."
- **Bernadette**：语气甜、要求狠。答错时先一句甜的再一句狠的。"Sweetie, that's wrong." "Let's try that again, shall we?"
- **Amy**：从认知角度复盘"你为什么会这么想"，学术但有温度。"Fascinating. Your brain took a shortcut here."
- **Sheldon**：高傲，从定义和第一性原理出发，答对也挑措辞，不人身攻击。答对："Correct. Though I'd have phrased it with more precision." 答错："I'm not saying you're wrong. I'm saying the universe disagrees with you." 彩蛋："Bazinga."

### 情绪安全阀

情绪识别判定为"受挫"时，当前人格 prompt 追加降温指令：去掉调侃，保留语气标识。Sheldon 此状态下不说 Bazinga。

### 生产方式

用 `alchaincyf/nuwa-skill`（女娲）作提取工具，只取流程中的一段：

1. 找全集英文字幕，按角色切分台词，每人数千行。
2. 对七个角色分别跑女娲，需求澄清阶段选"本地语料优先"、用途选"角色扮演"，把网络搜索降为补充。
3. 只保留产出中的"表达 DNA"和"价值观与反模式"两节，另从语料里挑每人十句备用口头禅。
4. 压缩成上面的 200 字人格卡，加语言规则硬约束。

不直接使用女娲的完整 SKILL.md：它的心智模型和决策启发式会让角色用自己的方式教，与"教学能力相同、只差语气"冲突；它的角色扮演规则也会和教学策略模块打架。

验证：用十道典型题跑七个人格对比输出，调到语气可辨、内容无差。

### 前端落点

- 设置页"讲解风格"下方加"讲师"一行，七个头像，未解锁为剪影并显示"第 N 张认可卡解锁"。
- 教学页输入框左侧加当前讲师头像，可切换已解锁讲师，切换只对新会话生效。
- 气泡头像、气泡主色随讲师变。
- 流水线面板第三步显示为"Leonard 决定：先让你自己找错"。
- 系统文案由当前讲师配音：空状态、计时超时提醒、练习总结第一句。静态文案表，每位讲师一份，不走 LLM。跳题不配音，必须是即时动作。

---

## 二、认可卡与成长

### 一套规则，一个隐藏分数，六个阈值

分数叫"认可值"，不下发前端，只在后端累加。

| 事件 | 得分 |
|---|---|
| 练习中回答一题（不含跳过） | 基础 2 分，答对 ×2 |
| 一次练习结束，掌握度增量 Δ 为正 | Δ × 10 |
| 一次教学会话正常结束并填自评 | 15 分 |
| 自评"能自己做"且之后 7 天内该知识点练习正确率 ≥ 70% | 额外 30 分 |
| 星标题之后真的去问了 | 10 分 |
| 计时模式完成整场练习 | 整场 ×1.2 |
| 连续学习天数 streak | 当日所有得分 ×(1 + 0.1 × min(streak, 7)) |

防刷：每日前 30 题全额，31 到 60 题半额，之后两折。跳题 0 分不扣分。分数只增不减，无衰减。

| 卡 | 阈值 |
|---|---|
| Penny | 150 |
| Howard | 400 |
| Raj | 800 |
| Bernadette | 1500 |
| Amy | 2600 |
| Sheldon | 4500 |

上线前用种子数据模拟四种学生画像校准：每天 10 题、隔天 20 题、只做教学不做练习、周末突击。目标：四种画像都能在三个月内拿到 Sheldon，速度差三倍以上。

### 黑盒程度

不展示分数、进度条、"还差多少"。学生只知道顺序和"越努力越快"。唯一外显是卡本身。规则表在后端配置文件，运营可调。

### 获卡时刻

练习总结页或教学会话结束后触发。全屏卡片翻转动画，正面是角色插画和一句英文台词，背面是获得日期和"选为讲师"按钮。

- Penny："Okay, you're officially one of the nerds now. Welcome."
- Howard："Not bad. I'd let you near my rocket. Supervised."
- Raj："You know what? I think you're going to be great."
- Bernadette："Aww, I'm so proud of you. Now don't slack off."
- Amy："Your neural pathways have clearly been reorganized. Impressive."
- Sheldon："You may sit in my spot. Once. Today only. Bazinga, you may not."

### 收藏页

侧栏新增"认可卡"，路由 `/cards`。背景用整层户型建模图（`frontend/public/tbbt/apartment/floorplan-render-light.jpg`），七个卡位落在七个房间上，而不是平铺：

| 讲师 | 房间 |
|---|---|
| Leonard | 4A 客厅沙发 |
| Penny | 4B 客厅 |
| Howard | 4A 厨房 |
| Raj | 4A 书桌区 |
| Bernadette | 4B 卧室 |
| Amy | 4A 走廊 |
| Sheldon | 4A 他的卧室 |

已得卡位显示角色头像加主题色描边，未得为灰色剪影。点开卡位看台词和日期，可直接设为讲师。户型图按容器宽度等比缩放，卡位坐标用百分比定位。

### 用途

只解锁讲师。不做皮肤、不做榜单。

---

## 三、视觉与页面巧思

**全局 token**：主色公寓芥末黄，强调色 Green Lantern 绿，错误色砖红，浅色模式背景公寓日光米白，深色模式夜晚深棕。正文字体、KaTeX 不动。

**图标**：教学用原子，练习用白板，报告用折线加沙发剪影，设置用恒温器，收藏页用公寓门钥匙。星标改为坐垫图形（"放进 Sheldon 的座位"）。

**登录页**：公寓走廊，4A 门。进入时三次敲门动画和 "Penny? Penny? Penny?" 字幕，学生名单是门口信箱名牌。教师入口做成 Roommate Agreement 签署页，口令框占位符 "Section 7, Clause B"。

**主页问候**（中文主标题不变，英文副标题按星期）：周一 Thai food night、周二 Cheesecake Factory、周三 new comic book day、周四 pizza night、周五 vintage video game night、周六 laundry night 8:15、周日 Sheldon's day off。

**教学页**：流水线运行中的加载指示用片头转场的原子轨道球体，三条轨道旋转，四步完成时轨道依次点亮。卡片尺寸和文案不变，只换这一个图形。

**练习页**：进度条是楼层指示，计时器加小字 "Bernadette is watching"。跳过是即时动作，点击立刻进下一题，不弹确认，不配音。

**练习总结页**：副标题 "Mission report"，等宽字体。

**报告页**：不做梗。情绪曲线和掌握度保持严肃。周评开头由当前讲师配音一句英文，正文中文。

**空状态**：Soft Kitty 插画和歌词第一行。**404**：薛定谔的猫箱，"This page both exists and doesn't."

---

## 后端改动清单

1. `students` 表加 `persona` 字段，枚举七值，可空，空等于 Leonard。
2. 新表 `score_events`：student_id、source_type、source_id、points、created_at；按 source 唯一，幂等。
3. 新表 `student_cards`：student_id、card_key、acquired_at。
4. 练习结束和教学结束的 service 各加一个计分钩子，算完检查阈值并写卡。
5. 新接口：读取卡列表、更新 persona。练习总结和教学结束的返回带 `new_card` 字段。
6. 教学 chat service 组 prompt 时拼入人格文件和情绪降温段。

## 前端改动清单（feat/teaching-emotion-strategy 分支）

- `Login.tsx` 重做
- `Rail.tsx` 加收藏页入口和图标替换
- `Composer.tsx` 加讲师头像切换
- `Message.tsx`、`AgentTrace.tsx`、`SelfRate.tsx` 文案和头像随讲师
- `PracticeSummary.tsx`、`Teaching.tsx` 接 `new_card` 触发获卡动画
- `Settings.tsx` 加讲师行
- 新建 `pages/student/Cards.tsx`、`components/cards/CardFlip.tsx`、`data/personaCopy.ts`
- `global.css` 重写 token
- 素材：已整理到 `frontend/public/tbbt/`，见该目录 README。仍缺：Soft Kitty 插画、公寓门廊背景（现用沙发合照替代）

## 实施记录

- 第一期（换肤、登录页、文案、空状态、404）：已合入 `bigbang-theory`。暗色模式按决定移除。
- 第二期（人格层）：已实现。后端 `students.persona`、`teaching_sessions.persona` 快照，`app/llm/personas/` 七份人格文件，prompt 在首轮与追问轮都注入人格段、语言规则、受挫降温段（阈值与情绪指引一致，>=3）。前端设置页讲师选择、输入框讲师头像、气泡按讲师配色、流水线策略步骤署名、主页与练习总结配音。
  - 本期七位讲师全部可选，解锁门槛在第三期随认可卡一起上。
  - 计时超时提醒的配音文案已备好（`PERSONA_COPY.overtime`），但当前代码没有超时提醒功能，待后续接。

## 分期

1. 换肤、登录页、文案、空状态。纯前端，一到两周。
2. 人格层。一个字段、七份 prompt、讲师切换 UI。一周。
3. 认可卡。两张表、计分钩子、收藏页、获卡动画。两周，含阈值校准。

## 素材与讲师主题色

角色图统一采用 Funko Pop 风格（`frontend/public/tbbt/`），八人一图切分，自动去底、裁头像、生成剪影。切分脚本按行列投影分割，白底泛洪填充去背景，头像取人物宽度为边的方框。

讲师主题色不从 Funko 图取（玩偶衣着与剧中形象不一致），按剧中标志物手定：

| 讲师 | 主色 | 来源 |
|---|---|---|
| Leonard | `#8A6D3B` 卡其 | 常穿的卡其外套 |
| Penny | `#E0457B` 玫红 | 粉色上衣 |
| Howard | `#C8322B` 砖红 | 红色格子衬衫、高领毛衣 |
| Raj | `#5B4A9E` 紫 | 紫色开衫 |
| Bernadette | `#D9A520` 芥末黄 | 黄色开衫 |
| Amy | `#5F7A3D` 橄榄绿 | 绿色毛衣 |
| Sheldon | `#1E8C4A` 绿 | Green Lantern T 恤 |

气泡用主色 12% 透明度做底、主色做头像描边；卡面用主色到深 20% 的渐变。

## 未定项

- Funko 玩偶形象的版权归 Funko 与华纳，内部演示可用，公开部署需换原创插画。
- Penny 当讲师是否成立。可解释为"跟那群人住了十二年"，或换成 Stuart / Leslie Winkle。
- 阈值校准需真实数据，上线头两周按内部配置放宽。
