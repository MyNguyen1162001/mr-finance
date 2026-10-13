"""Write the demo's fixtures under data/: the market on the demo date, and five sample clients.

The numbers are made up (prices, rates and the bonds' issuers are mock values, not quotes); the
shapes are what each source would send. Deterministic: run it again and nothing changes.

    uv run python scripts/make_fixtures.py
"""

from __future__ import annotations

import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
AS_OF = "2026-10-09"
MONTHS = [f"{y}-{m:02d}" for y, m in [(2025, 10), (2025, 11), (2025, 12)] + [(2026, m) for m in range(1, 10)]]

TY = 1_000_000_000
TR = 1_000_000

MARKET = {
    "as_of": AS_OF,
    "note": "Mock market data for the demo: not quotes.",
    "stocks": {
        "FPT": {"price": 128_000, "prev_month": 122_000, "ytd_base": 118_000, "sector": "Công nghệ", "beta": 1.05, "issuer": "FPT", "div": 2_000, "div_months": [6, 12]},
        "TCB": {"price": 26_500, "prev_month": 25_800, "ytd_base": 23_000, "sector": "Ngân hàng", "beta": 1.15, "issuer": "Techcombank", "div": 1_000, "div_months": [7]},
        "VCB": {"price": 64_000, "prev_month": 63_000, "ytd_base": 61_000, "sector": "Ngân hàng", "beta": 0.85, "issuer": "Vietcombank", "div": 0, "div_months": []},
        "MBB": {"price": 24_500, "prev_month": 24_000, "ytd_base": 21_500, "sector": "Ngân hàng", "beta": 1.10, "issuer": "MB", "div": 500, "div_months": [7]},
        "VNM": {"price": 62_000, "prev_month": 63_500, "ytd_base": 66_000, "sector": "Tiêu dùng", "beta": 0.60, "issuer": "Vinamilk", "div": 3_850, "div_months": [1, 8]},
        "HPG": {"price": 27_500, "prev_month": 26_000, "ytd_base": 25_500, "sector": "Thép", "beta": 1.30, "issuer": "Hòa Phát", "div": 0, "div_months": []},
        "VHM": {"price": 45_000, "prev_month": 42_000, "ytd_base": 40_000, "sector": "Bất động sản", "beta": 1.40, "issuer": "Vinhomes", "div": 0, "div_months": []},
        "MWG": {"price": 68_000, "prev_month": 65_000, "ytd_base": 58_000, "sector": "Bán lẻ", "beta": 1.20, "issuer": "Thế Giới Di Động", "div": 500, "div_months": [9]},
        "DGC": {"price": 92_000, "prev_month": 95_000, "ytd_base": 98_000, "sector": "Hóa chất", "beta": 1.30, "issuer": "Đức Giang", "div": 3_000, "div_months": [11]},
        "SSI": {"price": 33_000, "prev_month": 31_500, "ytd_base": 28_000, "sector": "Chứng khoán", "beta": 1.50, "issuer": "SSI", "div": 1_000, "div_months": [10]},
    },
    "funds": {
        "TCBF": {"name": "Quỹ trái phiếu TCBF", "nav": 25_000, "prev_month": 24_900, "ytd_base": 24_300, "type": "bond", "drawdown": 0.05, "liquid": True},
        "TCEF": {"name": "Quỹ cổ phiếu TCEF", "nav": 31_000, "prev_month": 30_000, "ytd_base": 28_500, "type": "equity", "drawdown": 0.30, "liquid": False},
        "TCMF": {"name": "Quỹ tiền tệ TCMF", "nav": 12_000, "prev_month": 11_950, "ytd_base": 11_700, "type": "money", "drawdown": 0.01, "liquid": True},
    },
    "bonds": {
        "TCB12401": {"issuer": "Techcombank", "sector": "Ngân hàng", "kind": "bank", "price": 101_200, "par": 100_000, "coupon": 0.065, "coupon_months": [5, 11], "maturity": "2029-05-20", "duration": 2.4},
        "SMR12501": {"issuer": "BĐS Sao Mai (mock)", "sector": "Bất động sản", "kind": "corporate", "price": 98_000, "par": 100_000, "coupon": 0.105, "coupon_months": [3, 9], "maturity": "2027-09-15", "duration": 1.0},
        "HBE12403": {"issuer": "Năng lượng Hòa Bình (mock)", "sector": "Năng lượng", "kind": "corporate", "price": 100_000, "par": 100_000, "coupon": 0.09, "coupon_months": [6, 12], "maturity": "2028-12-01", "duration": 2.0},
        "TD2535": {"issuer": "Kho bạc Nhà nước", "sector": "Chính phủ", "kind": "government", "price": 102_000, "par": 100_000, "coupon": 0.032, "coupon_months": [4], "maturity": "2035-04-10", "duration": 7.5},
    },
    "areas": {
        "thao_dien": {"name": "Thảo Điền, TP. Thủ Đức", "city": "TP.HCM", "price_sqm": 120 * TR, "prev_month": 118 * TR, "yoy": 0.08, "months_to_sell": 6},
        "phu_my_hung": {"name": "Phú Mỹ Hưng, Quận 7", "city": "TP.HCM", "price_sqm": 95 * TR, "prev_month": 95 * TR, "yoy": 0.05, "months_to_sell": 8},
        "vinhomes_grand_park": {"name": "Vinhomes Grand Park, TP. Thủ Đức (Q9 cũ)", "city": "TP.HCM", "price_sqm": 52 * TR, "prev_month": 51 * TR, "yoy": 0.07, "months_to_sell": 5},
        "quan_3": {"name": "Võ Văn Tần, Quận 3", "city": "TP.HCM", "price_sqm": 140 * TR, "prev_month": 140 * TR, "yoy": 0.04, "months_to_sell": 9},
        "long_thanh": {"name": "Đất nền Long Thành, Đồng Nai", "city": "Đồng Nai", "price_sqm": 18 * TR, "prev_month": 17_500_000, "yoy": 0.12, "months_to_sell": 18},
    },
    "gold": {"name": "Vàng miếng SJC", "price_per_luong": 150 * TR, "prev_month": 146 * TR, "ytd_base": 120 * TR, "world_gap": 0.12},
    "crypto": {
        "BTC": {"price": 2_635 * TR, "prev_month": 2_480 * TR, "ytd_base": 2_300 * TR},
        "ETH": {"price": 90 * TR, "prev_month": 86 * TR, "ytd_base": 95 * TR},
    },
    "fx": {"USDVND": {"rate": 26_350, "prev_month": 26_200, "ytd_base": 25_500}},
    "benchmarks": {
        "VNINDEX": {"name": "VN-Index", "ytd": 0.145, "month": 0.021},
        "TD12M": {"name": "Lãi tiết kiệm 12 tháng", "ytd": 0.038, "month": 0.004},
    },
    "rates": {"deposit_12m": 0.05, "policy": 0.045, "mortgage_floating": 0.095},
    # what a stress shaves off each class (a stock's is 25% × its beta, a fund's its own)
    "stress_drawdown": {"cash": 0.0, "deposit": 0.0, "bond_government": 0.05, "bond_bank": 0.08,
                        "bond_corporate": 0.15, "stock_base": 0.25, "real_estate": 0.10, "gold": 0.10,
                        "business": 0.25, "crypto": 0.60, "insurance": 0.0},
}


def salary_rows(rng, months, label, amount, day=5):
    return [{"date": f"{m}-{day:02d}", "amount": round(amount * rng.uniform(0.99, 1.01), -4),
             "direction": "in", "desc": f"{label} T{int(m[5:])}/{m[:4]}", "category": "salary"}
            for m in months]


def monthly_out(rng, months, label, amount, category, day=15, jitter=0.0):
    return [{"date": f"{m}-{day:02d}", "amount": round(amount * rng.uniform(1 - jitter, 1 + jitter), -4),
             "direction": "out", "desc": label, "category": category} for m in months]


def quarterly_out(months, label, amount, category, which=(1, 4, 7, 10), day=10):
    return [{"date": f"{m}-{day:02d}", "amount": amount, "direction": "out", "desc": label,
             "category": category} for m in months if int(m[5:]) in which]


def noise(rng, months, n_per_month, low, high):
    shops = ["VINMART", "GRAB", "SHOPEE", "CIRCLE K", "HIGHLANDS", "CGV", "PETROLIMEX", "GUARDIAN"]
    rows = []
    for m in months:
        for _ in range(n_per_month):
            rows.append({"date": f"{m}-{rng.randint(1, 28):02d}", "amount": round(rng.uniform(low, high), -3),
                         "direction": "out", "desc": f"THANH TOAN THE {rng.choice(shops)}", "category": "living"})
    return rows


def client_c01(rng):
    tx = (salary_rows(rng, MONTHS, "LUONG CONG TY CONG NGHE TECHVN", 120 * TR)
          + monthly_out(rng, MONTHS, "TRA NO VAY THE CHAP 1902xxxx", 38 * TR, "loan", day=20)
          + monthly_out(rng, MONTHS, "THANH TOAN DU NO THE TIN DUNG", 35 * TR, "card", day=25, jitter=0.15)
          + quarterly_out(MONTHS, "HOC PHI TRUONG QUOC TE (2 CON)", 90 * TR, "school", which=(1, 4, 8, 11))
          + noise(rng, MONTHS, 6, 300_000, 4 * TR))
    return {
        "id": "C01", "name": "Nguyễn Minh Khoa", "age": 42, "occupation": "Giám đốc công nghệ",
        "segment": "Priority", "persona_hint": "Chuyên gia", "city": "TP.HCM",
        "income_monthly": 120 * TR, "spending_monthly": 115 * TR, "benchmark": "VNINDEX", "drawdown_limit": 0.15,
        "household": [{"id": "C01S", "relation": "Vợ", "consent": True}],
        "dependents": [{"name": "Nguyễn Minh An", "relation": "Con", "birth_year": 2012},
                       {"name": "Nguyễn Minh Châu", "relation": "Con", "birth_year": 2016}],
        "sources": {
            "techcombank": {
                "accounts": [
                    {"id": "1902-CASA-01", "type": "CASA", "name": "Tài khoản thanh toán", "balance": 680 * TR},
                    {"id": "1902-TD-01", "type": "TD", "name": "Tiền gửi 12 tháng", "balance": 2_500 * TR, "rate": 0.052,
                     "opened": "2025-12-20", "maturity": "2026-12-20"},
                ],
                "cards": [{"id": "VISA-SIG-01", "name": "Visa Signature", "limit": 300 * TR, "outstanding": 45 * TR}],
                "loans": [{"id": "LN-HOME-01", "name": "Vay mua nhà Thảo Điền", "outstanding": 2_400 * TR, "rate": 0.092,
                           "rate_type": "floating", "monthly_payment": 38 * TR, "end": "2034-06-20", "collateral": "OH-TD-01"}],
                "transactions": tx,
            },
            "tcbs": {
                "stocks": [{"ticker": "FPT", "qty": 15_000, "avg_price": 95_000, "bought": "2023-03-14"}, {"ticker": "TCB", "qty": 40_000, "avg_price": 21_000, "bought": "2024-06-05"},
                           {"ticker": "VNM", "qty": 8_000, "avg_price": 70_000, "bought": "2022-11-21"}, {"ticker": "HPG", "qty": 20_000, "avg_price": 24_000, "bought": "2025-02-18"}],
                "bonds": [{"code": "TCB12401", "qty": 10_000, "avg_price": 100_000, "bought": "2025-01-08"}, {"code": "SMR12501", "qty": 5_000, "avg_price": 100_000, "bought": "2025-07-22"}],
                "realized_ytd": 320 * TR,
            },
            "techcom_capital": {"funds": [{"code": "TCBF", "units": 40_000, "avg_nav": 23_500, "bought": "2024-09-10"}, {"code": "TCEF", "units": 20_000, "avg_nav": 27_000, "bought": "2025-04-02"}]},
            "onehousing": {"properties": [{"id": "OH-TD-01", "name": "Căn hộ Thảo Điền", "area": "thao_dien", "type": "Căn hộ",
                                           "sqm": 120, "purchase_year": 2019, "purchase_price": 8 * TY, "rental_monthly": 0, "use": "Ở"}]},
            "open_api": [{"institution": "VPBank", "consent": True, "accounts": [{"id": "VPB-001", "type": "CASA", "name": "Tài khoản VPBank", "balance": 420 * TR}]}],
        },
        "declared": [
            {"id": "D-GOLD-01", "class": "gold", "name": "Vàng miếng SJC", "qty": 10},
            {"id": "D-INS-01", "class": "insurance", "name": "Bảo hiểm nhân thọ (liên kết chung)", "value": 300 * TR,
             "premium_annual": 60 * TR, "premium_month": 3},
        ],
        "events": [{"date": "2027-03-15", "direction": "out", "amount": 1_800 * TR, "label": "Học phí du học (Úc) – Minh An", "category": "school"},
                   {"date": "2027-03-31", "direction": "out", "amount": 85 * TR, "label": "Quyết toán thuế TNCN 2026", "category": "tax"}],
        "behaviour": [{"date": "2026-04-15", "market_move": -0.06, "action": "hold", "note": "Giữ nguyên danh mục khi VN-Index giảm 6%"}],
        "samples": ["vps_C01.csv"],
    }


def client_c01s(rng):
    tx = (salary_rows(rng, MONTHS, "LUONG CONG TY XNK SAI GON", 55 * TR)
          + [{"date": f"{m}-03", "amount": 22 * TR, "direction": "in", "desc": "TIEN THUE CAN HO PMH", "category": "rent"} for m in MONTHS]
          + noise(rng, MONTHS, 4, 300_000, 3 * TR))
    return {
        "id": "C01S", "name": "Trần Thu Hà", "age": 40, "occupation": "Kế toán trưởng", "segment": "Priority",
        "persona_hint": "Chuyên gia", "city": "TP.HCM", "member_of": "C01",
        "income_monthly": 77 * TR, "spending_monthly": 20 * TR, "benchmark": "VNINDEX", "drawdown_limit": 0.12,
        "household": [], "dependents": [],
        "sources": {
            "techcombank": {"accounts": [{"id": "2207-CASA-01", "type": "CASA", "name": "Tài khoản thanh toán", "balance": 350 * TR},
                                         {"id": "2207-TD-01", "type": "TD", "name": "Tiền gửi 6 tháng", "balance": 1_500 * TR, "rate": 0.047,
                                          "opened": "2026-04-10", "maturity": "2027-04-10"}],
                            "cards": [], "loans": [], "transactions": tx},
            "tcbs": {"stocks": [{"ticker": "VCB", "qty": 10_000, "avg_price": 58_000, "bought": "2023-08-16"}], "bonds": [], "realized_ytd": 25 * TR},
            "techcom_capital": {"funds": []},
            "onehousing": {"properties": [{"id": "OH-PMH-01", "name": "Căn hộ Phú Mỹ Hưng (cho thuê)", "area": "phu_my_hung", "type": "Căn hộ",
                                           "sqm": 85, "purchase_year": 2021, "purchase_price": 6_500 * TR, "rental_monthly": 22 * TR, "use": "Cho thuê"}]},
            "open_api": [],
        },
        "declared": [], "events": [], "samples": [],
    }


def client_c02(rng):
    tx = (salary_rows(rng, MONTHS, "CHIA LOI NHUAN CTY LOGISTICS PHAT DAT", 250 * TR, day=10)
          + monthly_out(rng, MONTHS, "TRA NO VAY MUA DAT LONG THANH", 85 * TR, "loan", day=18)
          + monthly_out(rng, MONTHS, "THANH TOAN DU NO THE TIN DUNG", 90 * TR, "card", day=25, jitter=0.2)
          + [{"date": f"{m}-05", "amount": 12 * TR, "direction": "in", "desc": "TIEN THUE CAN HO VGP", "category": "rent"} for m in MONTHS]
          + noise(rng, MONTHS, 8, 1 * TR, 15 * TR))
    return {
        "id": "C02", "name": "Lê Văn Phát", "age": 55, "occupation": "Chủ doanh nghiệp logistics",
        "segment": "Private", "persona_hint": "F1", "city": "TP.HCM",
        "income_monthly": 262 * TR, "spending_monthly": 180 * TR, "benchmark": "VNINDEX", "drawdown_limit": 0.20,
        "household": [{"id": "C02S", "relation": "Vợ", "consent": False}],
        "dependents": [{"name": "Lê Phát Đạt", "relation": "Con", "birth_year": 2004},
                       {"name": "Lê Bảo Ngọc", "relation": "Con", "birth_year": 2009}],
        "sources": {
            "techcombank": {
                "accounts": [{"id": "0301-CASA-01", "type": "CASA", "name": "Tài khoản thanh toán", "balance": 2_100 * TR},
                             {"id": "0301-TD-01", "type": "TD", "name": "Tiền gửi 12 tháng", "balance": 6 * TY, "rate": 0.053,
                              "opened": "2026-01-15", "maturity": "2027-01-15"}],
                "cards": [{"id": "VISA-INF-01", "name": "Visa Infinite", "limit": 1 * TY, "outstanding": 120 * TR}],
                "loans": [{"id": "LN-LAND-01", "name": "Vay mua đất Long Thành", "outstanding": 5 * TY, "rate": 0.098,
                           "rate_type": "floating", "monthly_payment": 85 * TR, "end": "2031-03-18", "collateral": "OH-LT-01"}],
                "transactions": tx,
            },
            "tcbs": {
                "stocks": [{"ticker": "TCB", "qty": 300_000, "avg_price": 18_000, "bought": "2019-05-06"}, {"ticker": "VCB", "qty": 60_000, "avg_price": 55_000, "bought": "2021-10-12"},
                           {"ticker": "MBB", "qty": 200_000, "avg_price": 17_000, "bought": "2020-04-15"}, {"ticker": "VHM", "qty": 50_000, "avg_price": 48_000, "bought": "2022-12-01"}],
                "bonds": [{"code": "SMR12501", "qty": 30_000, "avg_price": 100_000, "bought": "2025-07-22"}, {"code": "HBE12403", "qty": 20_000, "avg_price": 100_000, "bought": "2024-11-25"}],
                "realized_ytd": 1_100 * TR,
            },
            "techcom_capital": {"funds": []},
            "onehousing": {"properties": [
                {"id": "OH-PMH-02", "name": "Biệt thự Phú Mỹ Hưng", "area": "phu_my_hung", "type": "Biệt thự", "sqm": 250,
                 "purchase_year": 2012, "purchase_price": 9 * TY, "rental_monthly": 0, "use": "Ở"},
                {"id": "OH-LT-01", "name": "Đất nền Long Thành", "area": "long_thanh", "type": "Đất nền", "sqm": 1_000,
                 "purchase_year": 2018, "purchase_price": 7 * TY, "rental_monthly": 0, "use": "Đầu tư"},
                {"id": "OH-VGP-01", "name": "Căn hộ Vinhomes Grand Park", "area": "vinhomes_grand_park", "type": "Căn hộ", "sqm": 70,
                 "purchase_year": 2020, "purchase_price": 2_300 * TR, "rental_monthly": 12 * TR, "use": "Cho thuê"},
            ]},
            "open_api": [{"institution": "SSI", "consent": True, "accounts": [{"id": "SSI-001", "type": "SECURITIES_CASH", "name": "Tiền tại SSI", "balance": 800 * TR}],
                          "stocks": [{"ticker": "HPG", "qty": 100_000, "avg_price": 22_000, "bought": "2023-01-30"}]}],
        },
        "declared": [
            {"id": "D-GOLD-02", "class": "gold", "name": "Vàng miếng SJC", "qty": 50},
            {"id": "D-BIZ-01", "class": "business", "name": "30% cổ phần Logistics Phát Đạt", "value": 12 * TY, "sector": "Logistics"},
        ],
        "events": [{"date": "2026-11-20", "direction": "out", "amount": 1_200 * TR, "label": "Học phí đại học (Mỹ) – Phát Đạt", "category": "school"},
                   {"date": "2027-06-30", "direction": "out", "amount": 2 * TY, "label": "Góp vốn mở rộng kho bãi", "category": "business"}],
        "behaviour": [{"date": "2026-04-15", "market_move": -0.06, "action": "buy", "note": "Mua thêm 50.000 cổ phiếu MBB khi VN-Index giảm 6%"}],
        "samples": [],
    }


def client_c02s(rng):
    return {
        "id": "C02S", "name": "Hoàng Thị Mai", "age": 52, "occupation": "Nội trợ", "segment": "Private",
        "persona_hint": "F1", "city": "TP.HCM", "member_of": "C02",
        "income_monthly": 0, "spending_monthly": 30 * TR, "benchmark": "TD12M", "drawdown_limit": 0.10,
        "household": [], "dependents": [],
        "sources": {"techcombank": {"accounts": [{"id": "0302-TD-01", "type": "TD", "name": "Tiền gửi 12 tháng", "balance": 4 * TY,
                                                  "rate": 0.053, "opened": "2026-02-01", "maturity": "2027-02-01"}],
                                    "cards": [], "loans": [], "transactions": []},
                    "tcbs": {"stocks": [], "bonds": [], "realized_ytd": 0}, "techcom_capital": {"funds": []},
                    "onehousing": {"properties": []}, "open_api": []},
        "declared": [], "events": [], "samples": [],
    }


def client_c03(rng):
    tx = (salary_rows(rng, MONTHS, "LUONG CONG TY FINTECH ZEN", 80 * TR)
          + monthly_out(rng, MONTHS, "THANH TOAN DU NO THE TIN DUNG", 30 * TR, "card", day=25, jitter=0.25)
          + monthly_out(rng, MONTHS, "CHUYEN TIEN THUE NHA CHUNG CU", 15 * TR, "rent_out", day=2)
          + noise(rng, MONTHS, 8, 200_000, 3 * TR))
    return {
        "id": "C03", "name": "Phạm Gia Huy", "age": 29, "occupation": "Đồng sáng lập startup fintech",
        "segment": "Priority", "persona_hint": "F2", "city": "Hà Nội",
        "income_monthly": 80 * TR, "spending_monthly": 45 * TR, "benchmark": "VNINDEX", "drawdown_limit": 0.30,
        "household": [], "dependents": [],
        "sources": {
            "techcombank": {"accounts": [{"id": "0909-CASA-01", "type": "CASA", "name": "Tài khoản thanh toán", "balance": 300 * TR}],
                            "cards": [{"id": "VISA-PLT-03", "name": "Visa Platinum", "limit": 150 * TR, "outstanding": 28 * TR}],
                            "loans": [], "transactions": tx},
            "tcbs": {"stocks": [{"ticker": "FPT", "qty": 5_000, "avg_price": 110_000, "bought": "2024-02-27"}, {"ticker": "SSI", "qty": 40_000, "avg_price": 26_000, "bought": "2025-03-11"},
                                {"ticker": "DGC", "qty": 10_000, "avg_price": 105_000, "bought": "2024-08-19"}, {"ticker": "MWG", "qty": 10_000, "avg_price": 50_000, "bought": "2025-05-06"},
                                {"ticker": "HPG", "qty": 30_000, "avg_price": 26_000, "bought": "2026-01-15"}],
                     "bonds": [], "realized_ytd": 180 * TR,
                     "margin": {"id": "MRG-03", "name": "Vay ký quỹ TCBS", "outstanding": 600 * TR, "rate": 0.12}},
            "techcom_capital": {"funds": [{"code": "TCEF", "units": 30_000, "avg_nav": 26_000, "bought": "2025-06-24"}]},
            "onehousing": {"properties": []},
            "open_api": [],
        },
        "declared": [
            {"id": "D-BTC-01", "class": "crypto", "name": "Bitcoin", "symbol": "BTC", "qty": 0.8},
            {"id": "D-ETH-01", "class": "crypto", "name": "Ethereum", "symbol": "ETH", "qty": 5},
        ],
        "events": [{"date": "2027-05-01", "direction": "out", "amount": 400 * TR, "label": "Góp vốn vòng hạt giống startup", "category": "business"}],
        "behaviour": [{"date": "2026-04-15", "market_move": -0.06, "action": "panic_sell", "note": "Bán 60% danh mục cổ phiếu khi VN-Index giảm 6%, mua lại sau 3 tuần"}],
        "samples": [],
    }


def client_c04(rng):
    tx = ([{"date": f"{m}-10", "amount": 12 * TR, "direction": "in", "desc": "LUONG HUU BHXH TP.HCM", "category": "pension"} for m in MONTHS]
          + [{"date": f"{m}-03", "amount": 25 * TR, "direction": "in", "desc": "TIEN THUE CAN HO VO VAN TAN", "category": "rent"} for m in MONTHS]
          + monthly_out(rng, MONTHS, "CHI PHI KHAM CHUA BENH DINH KY", 6 * TR, "health", day=12, jitter=0.3)
          + noise(rng, MONTHS, 6, 300_000, 3 * TR))
    return {
        "id": "C04", "name": "Đỗ Thị Hạnh", "age": 63, "occupation": "Nghỉ hưu (nguyên giảng viên)",
        "segment": "Priority", "persona_hint": "Nghỉ hưu", "city": "TP.HCM",
        "income_monthly": 37 * TR, "spending_monthly": 40 * TR, "benchmark": "TD12M", "drawdown_limit": 0.08,
        "household": [], "dependents": [],
        "sources": {
            "techcombank": {"accounts": [
                {"id": "0505-CASA-01", "type": "CASA", "name": "Tài khoản thanh toán", "balance": 500 * TR},
                {"id": "0505-TD-01", "type": "TD", "name": "Tiền gửi 12 tháng", "balance": 5 * TY, "rate": 0.052, "opened": "2025-11-25", "maturity": "2026-11-25"},
                {"id": "0505-TD-02", "type": "TD", "name": "Tiền gửi 12 tháng", "balance": 3 * TY, "rate": 0.053, "opened": "2026-02-14", "maturity": "2027-02-14"}],
                "cards": [], "loans": [], "transactions": tx},
            "tcbs": {"stocks": [], "bonds": [{"code": "TD2535", "qty": 30_000, "avg_price": 100_500, "bought": "2025-09-17"}, {"code": "TCB12401", "qty": 20_000, "avg_price": 100_000, "bought": "2025-01-08"}],
                     "realized_ytd": 40 * TR},
            "techcom_capital": {"funds": [{"code": "TCBF", "units": 80_000, "avg_nav": 23_000, "bought": "2023-07-04"}, {"code": "TCMF", "units": 50_000, "avg_nav": 11_500, "bought": "2024-12-09"}]},
            "onehousing": {"properties": [{"id": "OH-Q3-01", "name": "Căn hộ Võ Văn Tần (cho thuê)", "area": "quan_3", "type": "Căn hộ", "sqm": 80,
                                           "purchase_year": 2010, "purchase_price": 3 * TY, "rental_monthly": 25 * TR, "use": "Cho thuê"}]},
            "open_api": [],
        },
        "declared": [
            {"id": "D-HOUSE-04", "class": "real_estate", "name": "Nhà phố Quận 3 (đang ở)", "value": 18 * TY, "area": "quan_3"},
            {"id": "D-GOLD-04", "class": "gold", "name": "Vàng miếng SJC", "qty": 20},
            {"id": "D-INS-04", "class": "insurance", "name": "Bảo hiểm sức khỏe cao cấp", "value": 0, "premium_annual": 40 * TR, "premium_month": 6},
        ],
        "events": [{"date": "2027-01-20", "direction": "out", "amount": 350 * TR, "label": "Phẫu thuật khớp gối (dự kiến)", "category": "health"}],
        "behaviour": [{"date": "2026-04-15", "market_move": -0.06, "action": "hold", "note": "Không giao dịch"}],
        "samples": ["vcb_C04.pdf"],
    }


def client_c05(rng):
    tx = (salary_rows(rng, MONTHS, "LUONG CONG TY QUANG CAO SAO VIET", 60 * TR)
          + monthly_out(rng, MONTHS, "TRA NO VAY MUA CAN HO VGP", 26 * TR, "loan", day=20)
          + monthly_out(rng, MONTHS, "THANH TOAN DU NO THE TIN DUNG", 14 * TR, "card", day=25, jitter=0.2)
          + noise(rng, MONTHS, 6, 200_000, 2 * TR))
    return {
        "id": "C05", "name": "Vũ Ngọc Anh", "age": 35, "occupation": "Trưởng phòng marketing",
        "segment": "Priority", "persona_hint": "Mới chạm ngưỡng", "city": "TP.HCM",
        "income_monthly": 60 * TR, "spending_monthly": 30 * TR, "benchmark": "VNINDEX", "drawdown_limit": 0.15,
        "household": [], "dependents": [{"name": "Trần Ngọc Bảo", "relation": "Con", "birth_year": 2021}],
        "sources": {
            "techcombank": {"accounts": [{"id": "0707-CASA-01", "type": "CASA", "name": "Tài khoản thanh toán", "balance": 180 * TR},
                                         {"id": "0707-TD-01", "type": "TD", "name": "Tiền gửi 6 tháng", "balance": 800 * TR, "rate": 0.047,
                                          "opened": "2026-06-01", "maturity": "2026-12-01"}],
                            "cards": [{"id": "VISA-PLT-05", "name": "Visa Platinum", "limit": 100 * TR, "outstanding": 12 * TR}],
                            "loans": [{"id": "LN-HOME-05", "name": "Vay mua căn hộ Vinhomes Grand Park", "outstanding": 2_100 * TR, "rate": 0.095,
                                       "rate_type": "floating", "monthly_payment": 26 * TR, "end": "2042-02-20", "collateral": "OH-VGP-05"}],
                            "transactions": tx},
            "tcbs": {"stocks": [{"ticker": "VCB", "qty": 3_000, "avg_price": 60_000, "bought": "2025-10-20"}, {"ticker": "FPT", "qty": 2_000, "avg_price": 120_000, "bought": "2026-02-03"}],
                     "bonds": [], "realized_ytd": 8 * TR},
            "techcom_capital": {"funds": [{"code": "TCEF", "units": 10_000, "avg_nav": 29_000, "bought": "2026-03-23"}]},
            "onehousing": {"properties": [{"id": "OH-VGP-05", "name": "Căn hộ Vinhomes Grand Park", "area": "vinhomes_grand_park", "type": "Căn hộ",
                                           "sqm": 75, "purchase_year": 2022, "purchase_price": 3_200 * TR, "rental_monthly": 0, "use": "Ở"}]},
            "open_api": [],
        },
        "declared": [],
        "events": [],
        "behaviour": [{"date": "2026-04-15", "market_move": -0.06, "action": "sell", "note": "Bán một nửa quỹ cổ phiếu TCEF khi VN-Index giảm 6%, chưa mua lại"}],
        "samples": ["ssi_C05.xlsx"],
    }


def main() -> None:
    rng = random.Random(20261009)
    (DATA / "clients").mkdir(parents=True, exist_ok=True)
    (DATA / "market.json").write_text(json.dumps(MARKET, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for make in (client_c01, client_c01s, client_c02, client_c02s, client_c03, client_c04, client_c05):
        c = make(rng)
        tb = c["sources"]["techcombank"]
        tb["transactions"] = sorted(tb.get("transactions", []), key=lambda r: r["date"])
        (DATA / "clients" / f"{c['id']}.json").write_text(
            json.dumps(c, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
