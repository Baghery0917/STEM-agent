import urllib.request
import urllib.error
import json
import time

# 禁用系统代理，避免本地开发时代理软件拦截 localhost 请求
_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
urllib.request.install_opener(_opener)

BASE_URL = "http://localhost:8000/api/v1"


def post(path, data):
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=json.dumps(data, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            time.sleep(0.2)
            return result
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        print(f"  ERROR {e.code}: {body}")
        time.sleep(0.2)
        return None


def main():
    print("=== STEM Educational Agent - 生成测试数据 ===\n")

    # 1. 学生
    print("1. 创建学生...")
    students = [
        {"name": "张伟", "gender": "male"},
        {"name": "李娜", "gender": "female"},
        {"name": "王强", "gender": "male"},
        {"name": "刘洋", "gender": "female"},
    ]
    student_ids = []
    for s in students:
        result = post("/students", s)
        if result:
            print(f"   ✓ {result['name']} (id={result['id']})")
            student_ids.append(result["id"])

    # 2. 知识体系
    print("\n2. 创建知识体系...")

    # 第一册：力学基础
    vol1 = post("/volumes", {
        "title": "第一册 · 力学基础",
        "description": "运动学、牛顿定律、功与能",
        "order": 1,
    })
    print(f"   ✓ 册: {vol1['title']} (id={vol1['id']})")

    ch1 = post("/chapters", {
        "volume_id": vol1["id"],
        "title": "第一章 运动的描述",
        "description": "质点、参考系、位移、速度、加速度",
        "order": 1,
    })
    print(f"     ✓ 章: {ch1['title']} (id={ch1['id']})")

    sec1_1 = post("/sections", {
        "chapter_id": ch1["id"],
        "title": "1.1 质点与参考系",
        "content": "质点是理想化模型，用来简化问题分析。参考系是描述物体运动所选择的参照物。",
        "order": 1,
    })
    sec1_2 = post("/sections", {
        "chapter_id": ch1["id"],
        "title": "1.2 时间与位移",
        "content": "位移是位置的变化，有大小和方向，是矢量。路程是路径的长度，是标量。",
        "order": 2,
    })
    sec1_3 = post("/sections", {
        "chapter_id": ch1["id"],
        "title": "1.3 速度与加速度",
        "content": "平均速度 = 位移 / 时间。瞬时速度是某一时刻的速度。加速度是速度变化率。",
        "order": 3,
    })
    print(f"       ✓ 3 个知识点已创建")

    ch2 = post("/chapters", {
        "volume_id": vol1["id"],
        "title": "第二章 匀变速直线运动",
        "description": "匀变速直线运动的规律、图像分析",
        "order": 2,
    })

    sec2_1 = post("/sections", {
        "chapter_id": ch2["id"],
        "title": "2.1 匀变速直线运动的规律",
        "content": "v = v₀ + at, x = v₀t + ½at², v² - v₀² = 2ax",
        "order": 1,
    })
    sec2_2 = post("/sections", {
        "chapter_id": ch2["id"],
        "title": "2.2 自由落体运动",
        "content": "自由落体是初速度为零、加速度为g的匀加速直线运动。",
        "order": 2,
    })
    print(f"     ✓ 章: {ch2['title']}")

    # 第二册：电磁学
    vol2 = post("/volumes", {
        "title": "第二册 · 电磁学",
        "description": "静电场、电流、磁场、电磁感应",
        "order": 2,
    })
    print(f"   ✓ 册: {vol2['title']} (id={vol2['id']})")

    ch3 = post("/chapters", {
        "volume_id": vol2["id"],
        "title": "第三章 静电场",
        "description": "电荷、电场强度、电势、电容器",
        "order": 1,
    })

    sec3_1 = post("/sections", {
        "chapter_id": ch3["id"],
        "title": "3.1 电荷与库仑定律",
        "content": "F = kQ₁Q₂/r²，描述两个点电荷之间的相互作用力。",
        "order": 1,
    })
    sec3_2 = post("/sections", {
        "chapter_id": ch3["id"],
        "title": "3.2 电场强度",
        "content": "E = F/q，描述电场对电荷的作用力特性。点电荷电场 E = kQ/r²。",
        "order": 2,
    })
    print(f"     ✓ 章: {ch3['title']}")

    # 收集知识点ID
    kp_ids = [sec1_1["id"], sec1_2["id"], sec1_3["id"], sec2_1["id"], sec2_2["id"], sec3_1["id"], sec3_2["id"]]

    # 3. 题目
    print("\n3. 创建题目...")
    questions = [
        # 单选题 - 简单
        {
            "type": "single_choice",
            "content": "关于质点，下列说法正确的是（  ）\nA. 只有体积很小的物体才能看作质点\nB. 只有质量很小的物体才能看作质点\nC. 研究地球绕太阳公转时，地球可以看作质点\nD. 研究跳水运动员的动作时，运动员可以看作质点",
            "answer": "C",
            "analysis": "质点是理想化模型，取决于研究问题，与物体实际大小无关。研究地球公转时，地球大小相对于轨道可以忽略。",
            "difficulty": "easy",
            "knowledge_point_ids": [sec1_1["id"]],
        },
        {
            "type": "single_choice",
            "content": "一物体做匀加速直线运动，初速度为 2 m/s，加速度为 1 m/s²，则 3s 末的速度为（  ）\nA. 3 m/s\nB. 4 m/s\nC. 5 m/s\nD. 6 m/s",
            "answer": "C",
            "analysis": "v = v₀ + at = 2 + 1×3 = 5 m/s",
            "difficulty": "easy",
            "knowledge_point_ids": [sec2_1["id"]],
        },
        # 单选题 - 中等
        {
            "type": "single_choice",
            "content": "从静止开始做匀加速直线运动的物体，在第1s内、第2s内、第3s内的位移之比为（  ）\nA. 1:2:3\nB. 1:3:5\nC. 1:4:9\nD. 2:3:4",
            "answer": "B",
            "analysis": "第n秒内位移 = sₙ - sₙ₋₁ = ½an² - ½a(n-1)² = ½a(2n-1)。所以第1、2、3秒内位移比为 1:3:5。",
            "difficulty": "medium",
            "knowledge_point_ids": [sec2_1["id"]],
        },
        {
            "type": "single_choice",
            "content": "两个点电荷相距为r时，它们之间的库仑力为F。若保持距离不变，将两个电荷的电量都增大为原来的2倍，则库仑力变为（  ）\nA. F/2\nB. F\nC. 2F\nD. 4F",
            "answer": "D",
            "analysis": "F' = k(2Q₁)(2Q₂)/r² = 4kQ₁Q₂/r² = 4F",
            "difficulty": "medium",
            "knowledge_point_ids": [sec3_1["id"]],
        },
        # 单选题 - 困难
        {
            "type": "single_choice",
            "content": "一物体从斜面顶端由静止开始匀加速下滑，经过斜面中点时的速度为v，则到达斜面底端时的速度为（  ）\nA. √2 v\nB. 2v\nC. √3 v\nD. (√2/2) v",
            "answer": "A",
            "analysis": "设斜面总长为L，加速度为a。中点时 v² = 2a(L/2) = aL。底端时 v'² = 2aL = 2v²，所以 v' = √2 v。",
            "difficulty": "hard",
            "knowledge_point_ids": [sec2_1["id"], sec2_2["id"]],
        },
        # 填空题
        {
            "type": "fill_blank",
            "content": "一物体做自由落体运动，下落高度为 20m，则下落时间为____s，落地速度为____m/s。（g = 10 m/s²）",
            "answer": "2, 20",
            "analysis": "h = ½gt² → t = √(2h/g) = √(40/10) = 2s。v = gt = 10×2 = 20 m/s。",
            "difficulty": "easy",
            "knowledge_point_ids": [sec2_2["id"]],
        },
        {
            "type": "fill_blank",
            "content": "电场强度 E = 2×10³ N/C 的匀强电场中，一个电荷 q = 3×10⁻⁶ C 所受的电场力为____N。",
            "answer": "6×10⁻³",
            "analysis": "F = qE = 3×10⁻⁶ × 2×10³ = 6×10⁻³ N",
            "difficulty": "easy",
            "knowledge_point_ids": [sec3_2["id"]],
        },
        # 计算题
        {
            "type": "calculation",
            "content": "一辆汽车以 10 m/s 的速度匀速行驶，突然发现前方 30m 处有障碍物，司机立即刹车，汽车以 2 m/s² 的加速度做匀减速直线运动。\n(1) 汽车停止需要多长时间？\n(2) 汽车能否在撞上障碍物前停下来？",
            "answer": "(1) 5s; (2) 能，刹车距离为 25m < 30m",
            "analysis": "(1) v = v₀ + at → 0 = 10 - 2t → t = 5s。\n(2) x = v₀t - ½at² = 10×5 - ½×2×25 = 50 - 25 = 25m < 30m，所以能停下。",
            "difficulty": "medium",
            "knowledge_point_ids": [sec2_1["id"]],
        },
        {
            "type": "calculation",
            "content": "两个点电荷 Q₁ = 4×10⁻⁸ C 和 Q₂ = -2×10⁻⁸ C 相距 0.2m。求：\n(1) 它们之间的库仑力大小和方向。\n(2) 在它们连线上何处电场强度为零？（k = 9×10⁹ N·m²/C²）",
            "answer": "(1) F = 1.8×10⁻⁴ N，吸引力；\n(2) 在 Q₂ 外侧 0.2(√2+1) m 处",
            "analysis": "(1) F = k|Q₁Q₂|/r² = 9×10⁹ × 8×10⁻¹⁶ / 0.04 = 1.8×10⁻⁴ N。异号电荷相吸。\n(2) 设距Q₂为x，kQ₁/(0.2+x)² = kQ₂/x²，解得 x = 0.2(√2+1) m。",
            "difficulty": "hard",
            "knowledge_point_ids": [sec3_1["id"], sec3_2["id"]],
        },
        # 多选题
        {
            "type": "multiple_choice",
            "content": "关于位移和路程，下列说法正确的是（  ）\nA. 位移是矢量，路程是标量\nB. 位移的大小不可能大于路程\nC. 物体沿直线运动，位移大小一定等于路程\nD. 物体做单向直线运动时，位移大小等于路程",
            "answer": "ABD",
            "analysis": "A正确，位移有方向，路程无方向。B正确，位移是起点到终点的直线距离，不可能大于实际路径。C错误，如往返直线运动。D正确，单向直线运动时二者相等。",
            "difficulty": "medium",
            "knowledge_point_ids": [sec1_2["id"]],
        },
        # 简答题
        {
            "type": "short_answer",
            "content": "解释为什么在研究地球绕太阳公转时可以把地球看作质点，而在研究地球自转时不能？",
            "answer": "地球公转时，地球大小相对于日地距离可以忽略；研究自转时，地球上各点运动情况不同，不能用一点代替。",
            "analysis": "质点模型的适用条件是物体的大小和形状对所研究问题的影响可以忽略。公转轨道半径约1.5亿km，地球半径仅6400km，占比极小；自转时各点线速度不同，不能用质点描述。",
            "difficulty": "easy",
            "knowledge_point_ids": [sec1_1["id"]],
        },
        # 更多题目
        {
            "type": "single_choice",
            "content": "一质点沿直线运动，其速度-时间图像是一条过原点的直线，则该质点的（  ）\nA. 位移与时间成正比\nB. 加速度恒定不变\nC. 平均速度等于初末速度之和的一半\nD. 以上都对",
            "answer": "B",
            "analysis": "v-t图是过原点的直线说明是初速为零的匀加速运动。A: x = ½at² ∝ t²，不是正比。B正确。C: v平均 = (0+v)/2 = v/2，正确。此题选BC。",
            "difficulty": "medium",
            "knowledge_point_ids": [sec1_3["id"], sec2_1["id"]],
        },
        {
            "type": "fill_blank",
            "content": "匀变速直线运动中，某段时间内的平均速度等于该段时间____时刻的瞬时速度。",
            "answer": "中间",
            "analysis": "匀变速直线运动的重要推论：平均速度等于中间时刻的瞬时速度。",
            "difficulty": "easy",
            "knowledge_point_ids": [sec2_1["id"]],
        },
        {
            "type": "single_choice",
            "content": "在电场中某点放一试探电荷q，受到的电场力为F，则该点的电场强度E = F/q。若将该试探电荷换为2q，则该点的电场强度（  ）\nA. 变为原来的2倍\nB. 变为原来的1/2\nC. 不变\nD. 无法确定",
            "answer": "C",
            "analysis": "电场强度是电场本身的属性，与试探电荷无关。E = F/q 是定义式，不是决定式。",
            "difficulty": "easy",
            "knowledge_point_ids": [sec3_2["id"]],
        },
        {
            "type": "calculation",
            "content": "一个物体从静止开始做匀加速直线运动，在第3秒内的位移为5m。求：\n(1) 物体的加速度；\n(2) 前5秒内的总位移。",
            "answer": "(1) a = 2 m/s²; (2) x = 25 m",
            "analysis": "(1) 第3秒内位移 = s₃ - s₂ = ½a×9 - ½a×4 = 5a/2 = 5 → a = 2 m/s²。\n(2) x₅ = ½×2×25 = 25 m。",
            "difficulty": "medium",
            "knowledge_point_ids": [sec2_1["id"]],
        },
        {
            "type": "single_choice",
            "content": "关于自由落体运动，下列说法正确的是（  ）\nA. 物体从静止开始下落的运动就是自由落体运动\nB. 自由落体运动的加速度随质量增大而增大\nC. 自由落体运动是初速度为零的匀加速直线运动\nD. 在空气中，羽毛下落比石块慢是因为羽毛不受重力",
            "answer": "C",
            "analysis": "A错误，需在只受重力作用下。B错误，g与质量无关。C正确。D错误，羽毛下落慢是因为空气阻力影响大，重力依然存在。",
            "difficulty": "easy",
            "knowledge_point_ids": [sec2_2["id"]],
        },
    ]

    question_ids = []
    for q in questions:
        result = post("/questions", q)
        if result:
            print(f"   ✓ 题目 #{len(question_ids)+1} ({result['difficulty']}, {result['type']})")
            question_ids.append(result["id"])

    print(f"\n=== 完成 ===")
    print(f"学生: {len(student_ids)} 名")
    print(f"知识体系: 2 册, 3 章, 7 个知识点")
    print(f"题目: {len(question_ids)} 道")
    print(f"\n前端访问: http://localhost:5174/")


if __name__ == "__main__":
    main()
