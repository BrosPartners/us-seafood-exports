"""Đối chiếu build.py với fixture hồi quy (không phải golden Excel thật).

Dashboard xuất khẩu không kế thừa từ workbook Excel tay nào (khác dashboard
nhập khẩu), nên không có nguồn "sự thật độc lập" để đối chiếu ASP/volume theo
đúng nghĩa golden test. `tests/fixtures/export_golden.json` là ẢNH CHỤP
output của build.py chạy trên chính data/trade_exports.csv + products.yml
hiện tại (sinh bằng `tests/make_golden.py`) — test này chỉ bắt HỒI QUY: nếu
build.py hoặc products.yml đổi mà không cố ý làm thay đổi kết quả, test sẽ
fail. Thay đổi kết quả có chủ ý -> chạy lại `tests/make_golden.py` để chấp
nhận baseline mới, đừng sửa fixture bằng tay.

Ngoài ra vẫn giữ vài kiểm tra bất biến thật sự (không phụ thuộc fixture đóng
băng): "Other" phải đúng bằng phần còn lại của tổng nhóm ở mọi tháng, và vài
con số mốc đối chiếu thủ công với data/dashboard.json tại thời điểm build này
được viết (2026-08-25) để bắt lỗi rõ ràng nếu build.py tính sai đơn vị.
"""

import json
import pathlib

import pytest

from scripts import build

FIXTURES = pathlib.Path(__file__).parent / "fixtures"
ROOT = pathlib.Path(__file__).parent.parent

GOLDEN = json.loads((FIXTURES / "export_golden.json").read_text(encoding="utf8"))
ROWS = build.read_rows(ROOT / "data" / "trade_exports.csv")
GROUPS = build.load_config(ROOT / "products.yml")
ACTUAL = build.build(ROWS, GROUPS, "golden")

BY_KEY = {g["key"]: g for g in ACTUAL["groups"]}
GOLDEN_BY_KEY = {g["key"]: g for g in GOLDEN["groups"]}


def test_months_match_golden():
    assert ACTUAL["months"] == GOLDEN["months"]
    assert ACTUAL["latest_period"] == GOLDEN["latest_period"]


@pytest.mark.parametrize("key", list(GOLDEN_BY_KEY))
def test_group_matches_golden(key):
    assert BY_KEY[key]["product"] == GOLDEN_BY_KEY[key]["product"]
    assert BY_KEY[key]["volume"] == GOLDEN_BY_KEY[key]["volume"]
    assert BY_KEY[key]["value"] == GOLDEN_BY_KEY[key]["value"]
    assert BY_KEY[key]["asp"] == GOLDEN_BY_KEY[key]["asp"]


@pytest.mark.parametrize("key", list(GOLDEN_BY_KEY))
def test_country_breakdown_matches_golden(key):
    got_all = {c["name"]: c for c in BY_KEY[key]["countries"]}
    want_all = {c["name"]: c for c in GOLDEN_BY_KEY[key]["countries"]}
    assert set(got_all) == set(want_all)
    for name, want in want_all.items():
        got = got_all[name]
        assert got["volume"] == want["volume"], (key, name)
        assert got["value"] == want["value"], (key, name)
        assert got["asp"] == want["asp"], (key, name)


def test_other_row_closes_the_gap_to_group_total():
    """Tổng các nước liệt kê cộng Other phải bằng đúng tổng nhóm, mọi tháng —
    bất biến thật sự, không phụ thuộc fixture đóng băng."""
    for group_data in ACTUAL["groups"]:
        if not group_data["countries"]:
            continue
        for i in range(len(ACTUAL["months"])):
            parts = sum(c["volume"][i] for c in group_data["countries"])
            assert parts == group_data["volume"][i], (
                f"{group_data['key']} tháng {ACTUAL['months'][i]}")


def test_lobster_april_2026_matches_manually_verified_figures():
    """Chốt kiểm tra thủ công tại thời điểm viết test (2026-08-25), đối
    chiếu với data/dashboard.json đã build từ dữ liệu NOAA thật."""
    i = ACTUAL["months"].index("2026-04")
    lobster = BY_KEY["lobster"]
    countries = {c["name"]: c for c in lobster["countries"]}

    assert lobster["volume"][i] == 363782
    assert lobster["value"][i] == 8196287
    assert lobster["asp"][i] == pytest.approx(22.530766, abs=1e-6)
    assert countries["CANADA"]["volume"][i] == 20927
    assert countries["CHINA"]["volume"][i] == 149272
    assert countries["ITALY"]["volume"][i] == 70702
    assert countries["CHINA - HONG KONG"]["volume"][i] == 35079
    assert countries["SPAIN"]["volume"][i] == 34508
    assert countries["Other"]["volume"][i] == 53294
