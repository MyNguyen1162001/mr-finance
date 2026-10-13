"""Vietnamese labels for the codes the data uses."""

CLASSES = {
    "cash": "Tiền mặt & thanh toán",
    "deposit": "Tiền gửi",
    "stock": "Cổ phiếu",
    "bond": "Trái phiếu",
    "fund": "Chứng chỉ quỹ",
    "real_estate": "Bất động sản",
    "gold": "Vàng",
    "business": "Cổ phần doanh nghiệp",
    "insurance": "Bảo hiểm",
    "crypto": "Tài sản số",
    "loan": "Khoản vay",
    "card": "Dư nợ thẻ",
}

# the dashboard's allocation groups (cash and deposits read as one line)
GROUPS = {
    "cash": "Tiền & tiền gửi",
    "deposit": "Tiền & tiền gửi",
    "stock": "Cổ phiếu",
    "bond": "Trái phiếu",
    "fund": "Chứng chỉ quỹ",
    "real_estate": "Bất động sản",
    "gold": "Vàng",
    "business": "Cổ phần DN",
    "insurance": "Bảo hiểm",
    "crypto": "Tài sản số",
}

SOURCES = {
    "techcombank": {
        "label": "Techcombank",
        "tier": 1,
        "what": "Tiền gửi, thẻ, khoản vay, giao dịch",
    },
    "tcbs": {"label": "TCBS", "tier": 1, "what": "Cổ phiếu, trái phiếu, lãi lỗ"},
    "techcom_capital": {"label": "Techcom Capital", "tier": 1, "what": "Chứng chỉ quỹ"},
    "onehousing": {"label": "OneHousing", "tier": 1, "what": "Định giá bất động sản"},
    "open_api": {"label": "Open API (ngân hàng / CTCK khác)", "tier": 2, "what": "Số dư, danh mục"},
    "statement": {"label": "Sao kê tải lên", "tier": 2, "what": "Đọc sao kê PDF / Excel"},
    "declared": {
        "label": "Bạn tự khai",
        "tier": 3,
        "what": "Vàng, BĐS ngoài hệ thống, cổ phần, bảo hiểm",
    },
}

TRUST = {
    "verified": "Đã xác thực",
    "statement": "Từ sao kê",
    "declared": "Bạn tự khai",
}

# how much an analysis leans on a holding, by where it came from
TRUST_WEIGHT = {"verified": 1.0, "statement": 0.85, "declared": 0.6}
