# -*- coding: utf-8 -*-
"""端到端功能验证脚本（断言式，非交互）。

运行：python test_flow.py  （需后端已在 8000 端口运行）
验证：创建对象→画像Loop→导入聊天→时间轴→评分→匹配→约会→Skill→模拟对话。
"""
import json
import sys
import urllib.request

BASE = "http://127.0.0.1:8000/api"


def req(method, path, payload=None):
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
    r = urllib.request.Request(BASE + path, data=data, method=method,
                               headers={"Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(r, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    # 1. 创建对象 + 描述
    c = req("POST", "/persons", {"name": "林小雨",
            "description": "27岁，在上海做产品经理，喜欢旅游、摄影、咖啡，养了一只猫，性格慢热"})
    pid = c["person_id"]
    assert pid >= 1
    print("✓ 创建对象", c["name"], "| 抽取字段:", c.get("extracted"))
    assert "age" in c.get("extracted", []), "应抽取到 age"

    # 2. 画像 Loop 首轮问题
    loop = req("GET", f"/persons/{pid}/profile-loop")
    assert "questions" in loop and loop["questions"]
    print("✓ 画像Loop 问题数:", len(loop["questions"]),
          "| 完整度:", loop["completeness"], "| 阶段:", loop["stage_label"])

    # 3. 回答一个字段 + 一个"不知道"
    ans = req("POST", f"/persons/{pid}/profile-loop/answer",
              {"field": "relationship_view", "answer": "重视稳定，希望三年内结婚"})
    assert ans["recorded"] == "confirmed"
    ans2 = req("POST", f"/persons/{pid}/profile-loop/answer",
               {"field": "income", "answer": "不知道"})
    assert ans2["recorded"] == "unknown"
    print("✓ 画像回答 confirmed / unknown 均正常")

    # 4. 导入聊天
    chat = "\n".join([
        "2026-06-01 10:00 我: 周末有空吗",
        "2026-06-01 10:05 林小雨: 有呀，最近准备去云南旅游",
        "2026-06-01 10:06 我: 太好了，我也喜欢旅行",
        "2026-06-01 10:08 林小雨: 我喜欢摄影，想拍很多照片",
        "2026-06-02 09:00 林小雨: 我家猫今天好可爱",
        "2026-06-03 20:00 林小雨: 下次一起去看摄影展吧",
    ])
    imp = req("POST", "/import/text", {"person_name": "林小雨", "text": chat, "source": "text"})
    assert imp["imported"] == 6
    print("✓ 导入聊天", imp["imported"], "条 | 评分:", imp["score"], "| 状态:", imp["state"])

    # 5. 详情 / 时间轴 / 评分 / 匹配
    detail = req("GET", f"/persons/{pid}")
    assert detail["facts"], "应有画像字段"
    print("✓ 对象详情 | 阶段:", detail["stage_label"], "| 已确认字段:",
          len(detail["profile_summary"]["confirmed"]))
    tl = req("GET", f"/persons/{pid}/timeline")
    assert tl["events"]
    sc = req("GET", f"/persons/{pid}/score")
    assert 0 <= sc["overall"] <= 100
    print("✓ 时间轴事件:", len(tl["events"]), "| 评分:", sc["overall"], "| 趋势:", sc["trend"])
    match = req("GET", f"/persons/{pid}/match")
    print("✓ 匹配 | 总体:", match["overall"], "| 未知区域:", match["unknown"])

    # 6. 约会复盘
    date = req("POST", f"/persons/{pid}/dates",
               {"description": "今天和她吃了火锅，聊了工作、大学和旅游，她说最近想去杭州发展，整体很轻松，后来一起散了步"})
    assert date["date_id"]
    comp = req("POST", f"/persons/{pid}/dates/{date['date_id']}/complete")
    print("✓ 约会复盘 | 变化:", comp["review"]["关系变化"], "| 追问:", len(date["followup_questions"]))

    # 7. Persona Skill 蒸馏（版本化）
    sk = req("POST", f"/persons/{pid}/skill/distill")
    assert sk["version"] == 1
    sk2 = req("POST", f"/persons/{pid}/skill/distill")
    assert sk2["version"] == 2, "蒸馏应版本递增"
    print("✓ Persona Skill 蒸馏 v1→v2 | 引擎:", sk["skill"].get("_engine"))

    # 8. 模拟对话（训练模式）
    sim = req("POST", f"/persons/{pid}/simulate",
              {"message": "你周末喜欢做什么？最近忙吗？有空出来吗？", "mode": "training"})
    assert sim["reply"]
    print("✓ 模拟对话 | 引擎:", sim["engine"], "| 教练提示:", sim.get("coach", {}).get("tips"))

    # 9. Dashboard
    dash = req("GET", "/dashboard")
    assert dash["total"] >= 1 and dash["cards"] and dash["gantt"]
    print("✓ Dashboard | 对象数:", dash["total"], "| 甘特条数:", len(dash["gantt"]))

    print("\n全部端到端断言通过 ✓")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001
        print("✗ 失败:", repr(e))
        sys.exit(1)
