"""Write data/advisory.json: each client's specialist team, and the advisory track record.

The team is the client's RM and the five specialists around them; names, phone numbers, e-mails
and offices are made up for the demo. The track record is twelve months of what the AI advised
and what came of it, per AI step (the news reader, the impact assessor, the planner, the chat),
how much the client reads, and how their risk appetite moved. All of it is mock: the shape is
what a real record would hold. Deterministic: run it again and nothing changes.

    uv run python scripts/make_advisory.py
"""

from __future__ import annotations

import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "advisory.json"
AS_OF = "2026-10-09"
MONTHS = [f"{y}-{m:02d}" for y, m in [(2025, 11), (2025, 12)] + [(2026, m) for m in range(1, 11)]]

TY = 1_000_000_000
TR = 1_000_000

DOMAIN = "tcbwealth.example"
OFFICE_HCM = "Wealth Center, tầng 9, 23 Lê Duẩn, Quận 1, TP.HCM (địa chỉ giả định)"
OFFICE_HN = "Wealth Center, tầng 12, 191 Bà Triệu, Hai Bà Trưng, Hà Nội (địa chỉ giả định)"

RMS = {
    "hcm": {"name": "Hoàng Hải Yến", "email": f"yen.hoang@{DOMAIN}", "phone": "+84 28 3000 1101"},
    "hn": {"name": "Trần Quốc Bảo", "email": f"bao.tran@{DOMAIN}", "phone": "+84 24 3000 2201"},
    "private": {"name": "Ngô Minh Châu", "email": f"chau.ngo@{DOMAIN}", "phone": "+84 28 3000 1109"},
}

SPECIALISTS = [
    {
        "id": "real_estate",
        "role": "Real estate specialist",
        "role_vi": "Chuyên gia bất động sản",
        "name": "Phan Đức Thịnh",
        "email": f"thinh.phan@{DOMAIN}",
        "phone": "+84 28 3000 1201",
        "covers": ["Định giá BĐS (OneHousing)", "Mua, bán, cho thuê", "Vay thế chấp, đòn bẩy BĐS"],
    },
    {
        "id": "global",
        "role": "Global investment specialist",
        "role_vi": "Chuyên gia đầu tư toàn cầu",
        "name": "Lâm Bảo Ngọc",
        "email": f"ngoc.lam@{DOMAIN}",
        "phone": "+84 28 3000 1202",
        "covers": ["Cổ phiếu, trái phiếu, quỹ (TCBS, Techcom Capital)", "Tài sản ở nước ngoài", "Tỷ giá, ngoại tệ"],
    },
    {
        "id": "insurance",
        "role": "Insurance specialist",
        "role_vi": "Chuyên gia bảo hiểm",
        "name": "Đặng Thu Trang",
        "email": f"trang.dang@{DOMAIN}",
        "phone": "+84 28 3000 1203",
        "covers": ["Bảo hiểm nhân thọ, sức khỏe", "Bảo vệ khoản vay", "Quỹ học vấn cho con"],
    },
    {
        "id": "banking",
        "role": "Banking specialist",
        "role_vi": "Chuyên gia ngân hàng",
        "name": "Vũ Hoàng Long",
        "email": f"long.vu@{DOMAIN}",
        "phone": "+84 28 3000 1204",
        "covers": ["Tiền gửi, thẻ, thanh toán", "Tín dụng cá nhân và doanh nghiệp", "Chuyển tiền quốc tế"],
    },
    {
        "id": "private",
        "role": "Private specialist",
        "role_vi": "Chuyên gia Private Banking",
        "name": "Trịnh Khánh Linh",
        "email": f"linh.trinh@{DOMAIN}",
        "phone": "+84 28 3000 1205",
        "covers": ["Thừa kế, chuyển giao tài sản", "Pháp lý, thuế cá nhân", "Quản lý tài sản gia đình"],
    },
]

# who leads for each client: their RM, and which specialists matter most to their picture
CLIENTS = {
    "C01": {"rm": "hcm", "lead": ["global", "insurance", "real_estate"], "scale": 1.0},
    "C02": {"rm": "private", "lead": ["private", "real_estate", "banking"], "scale": 2.4},
    "C03": {"rm": "hn", "lead": ["global", "banking"], "scale": 0.35},
    "C04": {"rm": "hcm", "lead": ["insurance", "private", "banking"], "scale": 0.8},
    "C05": {"rm": "hcm", "lead": ["real_estate", "banking"], "scale": 0.3},
}

AGENTS = [
    {"id": "news", "name": "AI News Reader", "name_vi": "AI đọc báo, tổng hợp tin"},
    {"id": "impact", "name": "AI Impact Assessor", "name_vi": "AI đánh giá tác động lên danh mục"},
    {"id": "planner", "name": "AI Planning Advisor", "name_vi": "AI tư vấn kế hoạch và hành động"},
    {"id": "chat", "name": "AI Client Chat", "name_vi": "AI chat với khách hàng"},
]

# the advice a record holds: (month, agent, what was advised, outcome, value in VND at scale 1)
# outcome: right (the client acted, it paid), wrong (acted, it lost), missed (did not act, it
# would have paid), avoided (did not act on a wrong call), open (too early to say)
ADVICE = [
    ("2025-11", "planner", "Chốt lời một nửa cổ phiếu ngân hàng sau nhịp tăng 25%", "right", 182 * TR),
    ("2025-12", "impact", "Giảm trái phiếu BĐS trước kỳ đáo hạn lô lớn của tổ chức phát hành", "right", 96 * TR),
    ("2026-01", "planner", "Gửi kỳ hạn 12 tháng khi lãi suất đỉnh 6,1%", "right", 64 * TR),
    ("2026-02", "news", "Giá vàng miếng sẽ giảm khi NHNN tăng cung, bán bớt 30%", "wrong", -38 * TR),
    ("2026-03", "planner", "Mua ngoại tệ dần cho học phí du học", "missed", 71 * TR),
    ("2026-04", "impact", "Cổ phiếu FPT hưởng lợi từ hợp đồng AI, tăng tỷ trọng", "right", 143 * TR),
    ("2026-05", "planner", "Cơ cấu khoản vay thả nổi sang cố định 3 năm", "missed", 55 * TR),
    ("2026-06", "news", "Nâng hạng thị trường: mua thêm quỹ cổ phiếu trước công bố", "right", 118 * TR),
    ("2026-07", "impact", "Cổ phiếu VNM phục hồi sau báo cáo quý, giữ nguyên", "wrong", -64 * TR),
    ("2026-08", "planner", "Tăng tỷ trọng cổ phiếu khi VN-Index vượt 1.400", "avoided", 0),
    ("2026-09", "chat", "Cập nhật giá đất Long Thành sau quyết định khai thác sân bay", "right", 0),
    ("2026-10", "planner", "Khóa tỷ giá cho học phí kỳ tới bằng tiền gửi ngoại tệ", "open", 0),
]

# what the market showed that the news reader did not flag in time
MISSED_NEWS = [
    {
        "date": "2026-02-14",
        "title": "NHNN tăng cung vàng miếng, giá SJC giảm 8% trong hai tuần",
        "signal": "2026-01-28 · dự thảo sửa Nghị định 24 được đăng lấy ý kiến",
        "why": "Nguồn dự thảo chưa có trong danh sách nguồn theo dõi",
        "impact": -45 * TR,
    },
    {
        "date": "2026-05-06",
        "title": "Lãi suất cho vay thả nổi tăng 1,2 điểm sau đợt hút tiền của NHNN",
        "signal": "2026-04-22 · lãi suất liên ngân hàng tăng 3 phiên liền",
        "why": "Tín hiệu vĩ mô chưa được nối với khoản vay của khách",
        "impact": -32 * TR,
    },
    {
        "date": "2026-07-18",
        "title": "Bảng giá đất mới của TP.HCM áp dụng sớm hơn dự kiến",
        "signal": "2026-07-02 · HĐND thành phố đưa vào chương trình kỳ họp",
        "why": "Đánh giá xác suất thông qua thấp hơn thực tế",
        "impact": -21 * TR,
    },
]

# the risk tests a record holds before today's: (date, tolerance, capacity, profile)
RISK_TESTS = {
    "C01": [
        ("2025-04-12", 64, 70, "Tăng trưởng"),
        ("2025-10-20", 58, 66, "Cân bằng"),
        ("2026-04-18", 61, 63, "Tăng trưởng"),
    ],
    "C02": [
        ("2025-03-02", 72, 81, "Tăng trưởng"),
        ("2025-09-15", 68, 78, "Tăng trưởng"),
        ("2026-03-30", 55, 74, "Cân bằng"),
    ],
    "C03": [("2025-06-10", 84, 52, "Cân bằng"), ("2026-01-08", 88, 55, "Cân bằng"), ("2026-07-02", 79, 58, "Cân bằng")],
    "C04": [
        ("2025-02-21", 35, 48, "Thận trọng"),
        ("2025-08-30", 31, 45, "Thận trọng"),
        ("2026-02-27", 28, 44, "Thận trọng"),
    ],
    "C05": [
        ("2025-05-05", 70, 40, "Thận trọng"),
        ("2025-11-11", 76, 38, "Thận trọng"),
        ("2026-05-14", 81, 36, "Thận trọng"),
    ],
}


def team(cid: str) -> dict:
    c = CLIENTS[cid]
    rm = RMS[c["rm"]]
    office = OFFICE_HN if c["rm"] == "hn" else OFFICE_HCM
    return {
        "rm": {
            "role": "Relationship manager",
            "role_vi": "Chuyên viên quan hệ khách hàng",
            **rm,
            "office": office,
            "hours": "8:00 – 18:00, thứ Hai – thứ Bảy",
        },
        "specialists": [{**s, "office": office, "lead": s["id"] in c["lead"]} for s in SPECIALISTS],
    }


def track(cid: str, rng: random.Random) -> dict:
    scale = CLIENTS[cid]["scale"]
    advice = []
    for month, agent, text, outcome, value in ADVICE:
        if rng.random() < 0.12:  # not every client got every call
            continue
        advice.append(
            {
                "date": f"{month}-{rng.randint(3, 27):02d}",
                "agent": agent,
                "text": text,
                "outcome": outcome,
                "value": round(value * scale * rng.uniform(0.8, 1.2), -6),
            }
        )
    right = [a for a in advice if a["outcome"] == "right"]
    wrong = [a for a in advice if a["outcome"] == "wrong"]
    missed = [a for a in advice if a["outcome"] == "missed"]
    news = [{**n, "impact": round(n["impact"] * scale, -6)} for n in MISSED_NEWS]
    decided = len(right) + len(wrong) + len([a for a in advice if a["outcome"] == "avoided"])

    def monthly(base: float, spread: float, drift: float = 0.0) -> list:
        return [max(0, round(base * (1 + drift * i) + rng.uniform(-spread, spread))) for i in range(len(MONTHS))]

    minutes = monthly(55 * (1.4 if scale > 1 else 1), 18, 0.03)
    days = [min(30, max(2, round(m / 6 + rng.uniform(-2, 2)))) for m in minutes]

    def series(base: float) -> list:
        return [round(min(0.98, max(0.4, base + rng.uniform(-0.06, 0.06) + 0.004 * i)), 3) for i in range(len(MONTHS))]

    articles = rng.randint(15_000, 21_000)
    sent = rng.randint(120, 190)
    agents = [
        {
            **AGENTS[0],
            "score": round(rng.uniform(78, 88)),
            "trend": series(0.8),
            "metrics": [
                {"label": "Bài báo, văn bản đã đọc", "value": f"{articles:,}".replace(",", ".")},
                {"label": "Tin liên quan gửi khách hàng", "value": str(sent)},
                {"label": "Tin quan trọng bị bỏ lỡ", "value": str(len(news)), "tone": "bad"},
                {
                    "label": "Thời gian từ lúc tin ra đến lúc gửi",
                    "value": f"{rng.uniform(1.5, 3.5):.1f} giờ".replace(".", ","),
                },
            ],
        },
        {
            **AGENTS[1],
            "score": round(rng.uniform(72, 84)),
            "trend": series(0.74),
            "metrics": [
                {"label": "Đánh giá tác động đã chạy", "value": str(rng.randint(260, 340))},
                {"label": "Đúng chiều tăng / giảm", "value": f"{rng.randint(76, 86)}%"},
                {"label": "Sai số ước tính trung bình", "value": f"±{rng.uniform(18, 30):.0f}%"},
                {"label": "Sai nhiều nhất", "value": "Bảng giá đất TP.HCM", "tone": "bad"},
            ],
        },
        {
            **AGENTS[2],
            "score": round(rng.uniform(70, 86)),
            "trend": series(0.72),
            "metrics": [
                {"label": "Khuyến nghị đưa ra", "value": str(len(advice))},
                {"label": "Khách hàng đã thực hiện", "value": str(decided)},
                {"label": "Đúng / sai", "value": f"{len(right)} / {len(wrong)}"},
                {"label": "Hành động bỏ lỡ", "value": str(len(missed)), "tone": "bad" if missed else None},
            ],
        },
        {
            **AGENTS[3],
            "score": round(rng.uniform(80, 92)),
            "trend": series(0.84),
            "metrics": [
                {"label": "Hội thoại", "value": str(rng.randint(30, 90))},
                {"label": "Khai báo đã ghi nhận", "value": str(rng.randint(6, 18))},
                {"label": "Chuyển sang chuyên gia", "value": f"{rng.randint(8, 18)}%"},
                {"label": "Mức hài lòng", "value": f"{rng.uniform(4.3, 4.8):.1f} / 5".replace(".", ",")},
            ],
        },
    ]
    return {
        "summary": {
            "advice": len(advice),
            "right": len(right),
            "wrong": len(wrong),
            "missed": len(missed),
            "open": len([a for a in advice if a["outcome"] == "open"]),
            "gained": sum(a["value"] for a in right),
            "lost": sum(a["value"] for a in wrong),
            "missed_value": sum(a["value"] for a in missed),
            "missed_news": len(news),
            "missed_news_value": sum(n["impact"] for n in news),
        },
        "agents": agents,
        "advice": sorted(advice, key=lambda a: a["date"], reverse=True),
        "missed_news": news,
        "engagement": {
            "months": MONTHS,
            "minutes": minutes,
            "days": days,
            "alerts_opened": f"{rng.randint(62, 91)}%",
            "streak": rng.randint(3, 21),
        },
        "risk_tests": [{"date": d, "tolerance": t, "capacity": c, "profile": p} for d, t, c, p in RISK_TESTS[cid]],
    }


def main() -> None:
    rng = random.Random(20261013)
    out = {
        "as_of": AS_OF,
        "note": "Dữ liệu giả định cho demo: tên, số điện thoại, e-mail, địa chỉ và kết quả tư vấn đều không có thật.",
        "team": {cid: team(cid) for cid in CLIENTS},
        "tracking": {cid: track(cid, rng) for cid in CLIENTS},
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
