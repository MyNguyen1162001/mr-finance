"""Write data/views.json: the house views shown beside the headlines — what research houses and
funds expect for the market, rates, gold and property over the next months.

Every view is **mock**: the houses are the kind a client reads (a fund manager, brokers' research,
a wire service, Techcombank's own research), but the titles, numbers and dates are invented for the
demo. Swap in the real reports before showing it to anyone. ``touches`` says which holdings a view is
about (tickers, asset classes, property areas), so the page can show each client what it means for them.

    uv run python scripts/make_views.py
"""

from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "data" / "views.json"

# stance: positive | neutral | cautious
VIEWS = [
    {
        "id": "V01",
        "house": "Dragon Capital",
        "kind": "Quỹ đầu tư",
        "date": "2026-10-02",
        "horizon": "Đến cuối 2027",
        "topic": "Thị trường cổ phiếu",
        "title": "Nâng hạng mở đường cho dòng vốn ngoại quay lại nhóm vốn hóa lớn",
        "stance": "positive",
        "target": "VN-Index 1.850 điểm",
        "summary": "Kỳ vọng dòng vốn ETF và quỹ chủ động vào nhóm ngân hàng, công nghệ, bán lẻ; ưu tiên doanh nghiệp tăng trưởng lợi nhuận trên 15%/năm.",
        "touches": {"tickers": ["FPT", "TCB", "VCB", "MBB", "MWG"], "classes": ["fund"]},
    },
    {
        "id": "V02",
        "house": "SSI Research",
        "kind": "Công ty chứng khoán",
        "date": "2026-09-28",
        "horizon": "12 tháng",
        "topic": "Ngân hàng",
        "title": "Ngân hàng: tăng trưởng tín dụng 15%, biên lãi ròng chịu áp lực nhẹ",
        "stance": "neutral",
        "target": "TCB 32.000 · VCB 98.000",
        "summary": "Lợi nhuận ngành dự báo tăng 14% năm 2027; nợ xấu bất động sản là rủi ro chính. Khuyến nghị nắm giữ nhóm ngân hàng tư nhân lớn.",
        "touches": {"tickers": ["TCB", "VCB", "MBB"]},
    },
    {
        "id": "V03",
        "house": "SHS Research",
        "kind": "Công ty chứng khoán",
        "date": "2026-10-05",
        "horizon": "6 tháng",
        "topic": "Thép, vật liệu",
        "title": "Thép: giá phục hồi chậm, thuế chống bán phá giá hỗ trợ thị phần nội địa",
        "stance": "neutral",
        "target": "HPG 29.000",
        "summary": "Sản lượng Dung Quất 2 giúp HPG tăng trưởng, nhưng giá thép thế giới còn yếu; biên lợi nhuận cải thiện từ quý 2/2027.",
        "touches": {"tickers": ["HPG"]},
    },
    {
        "id": "V04",
        "house": "Bloomberg Economics",
        "kind": "Hãng tin, kinh tế học",
        "date": "2026-10-07",
        "horizon": "Quý 4/2026 – Quý 2/2027",
        "topic": "Vàng, tỷ giá",
        "title": "Vàng thế giới đi ngang sau đỉnh; Fed cắt lãi suất chậm hơn kỳ vọng",
        "stance": "cautious",
        "target": "Vàng 2.450 – 2.600 USD/oz",
        "summary": "Đồng USD mạnh lại khi Fed giữ lãi suất lâu hơn; vàng khó lập đỉnh mới trong ngắn hạn. Chênh lệch vàng miếng trong nước có thể thu hẹp thêm.",
        "touches": {"classes": ["gold"]},
    },
    {
        "id": "V05",
        "house": "Techcombank Research",
        "kind": "Nghiên cứu nội bộ",
        "date": "2026-10-08",
        "horizon": "12 tháng",
        "topic": "Lãi suất",
        "title": "Lãi suất tiết kiệm đã chạm đáy; lãi vay thả nổi có thể tăng 0,5–1 điểm",
        "stance": "cautious",
        "target": "Tiết kiệm 12 tháng 5,0–5,5%",
        "summary": "Thanh khoản hệ thống thu hẹp cuối năm; nên khóa kỳ hạn dài cho tiền gửi và xem lại khoản vay thả nổi lớn.",
        "touches": {"classes": ["deposit", "loan"]},
    },
    {
        "id": "V06",
        "house": "VNDirect Research",
        "kind": "Công ty chứng khoán",
        "date": "2026-09-30",
        "horizon": "12 tháng",
        "topic": "Bất động sản TP.HCM",
        "title": "Căn hộ khu Đông TP.HCM: giá tăng chậm lại, thanh khoản cải thiện nhờ Metro số 1",
        "stance": "positive",
        "target": "Giá căn hộ +6–8%/năm",
        "summary": "Nguồn cung mới hạn chế giữ giá; khu Thảo Điền, Thủ Đức hưởng lợi từ hạ tầng. Đất nền vùng ven còn chờ tiến độ sân bay Long Thành.",
        "touches": {"classes": ["real_estate"], "areas": ["thao_dien", "vinhomes_grand_park", "long_thanh"]},
    },
    {
        "id": "V07",
        "house": "Techcom Capital",
        "kind": "Quỹ đầu tư",
        "date": "2026-10-01",
        "horizon": "12 tháng",
        "topic": "Trái phiếu",
        "title": "Trái phiếu doanh nghiệp: chọn lọc tổ chức phát hành, tránh nhóm BĐS đòn bẩy cao",
        "stance": "neutral",
        "target": "Lợi suất kỳ vọng 7–8,5%",
        "summary": "Áp lực đáo hạn 2027 tập trung ở nhóm bất động sản; ưu tiên trái phiếu ngân hàng và quỹ trái phiếu đa dạng hóa.",
        "touches": {"classes": ["bond"]},
    },
    {
        "id": "V08",
        "house": "Bloomberg Intelligence",
        "kind": "Hãng tin, kinh tế học",
        "date": "2026-09-25",
        "horizon": "12 tháng",
        "topic": "Công nghệ",
        "title": "Dịch vụ CNTT châu Á: đơn hàng AI giữ tăng trưởng hai chữ số",
        "stance": "positive",
        "target": "Doanh thu ngành +18%",
        "summary": "Nhu cầu chuyển đổi số và AI từ Nhật, Mỹ giữ đà; rủi ro chính là tỷ giá Yên và chi phí nhân sự.",
        "touches": {"tickers": ["FPT"]},
    },
]


def main() -> None:
    OUT.write_text(
        json.dumps(
            {
                "as_of": "2026-10-09",
                "note": "Dữ liệu giả định cho demo: tên tổ chức để minh họa, nội dung, con số và ngày không phải báo cáo thật. "
                "Thay bằng báo cáo gốc trước khi trình bày.",
                "views": VIEWS,
            },
            ensure_ascii=False,
            indent=1,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
