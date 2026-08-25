"""Sinh fixture golden (ảnh chụp hồi quy) cho build.py của dashboard xuất khẩu.

    python tests/make_golden.py

Khác dashboard nhập khẩu (golden đối chiếu với công thức Excel gốc), dashboard
xuất khẩu này KHÔNG kế thừa từ một workbook tay nào — nên không có nguồn "sự
thật độc lập" để build.py đối chiếu theo kiểu golden thật. Fixture ở đây là
ẢNH CHỤP output của build.py chạy trên chính data/trade_exports.csv +
products.yml hiện tại của repo, dùng làm bẫy HỒI QUY: nếu ai đó sửa logic
build.py mà không cố ý làm thay đổi kết quả, test_golden.py sẽ fail và buộc
người đó xem lại thay đổi, rồi tự chạy lại script này để chấp nhận baseline
mới nếu thay đổi là có chủ ý.

Chạy lại khi: data/trade_exports.csv có dữ liệu mới (NOAA công bố tháng mới),
hoặc products.yml đổi (thêm/bớt nhóm, đổi danh sách countries).
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from scripts import build
from scripts.console import fix_stdio_encoding

fix_stdio_encoding()

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")


def main():
    input_path = os.path.join(ROOT, "data", "trade_exports.csv")
    config_path = os.path.join(ROOT, "products.yml")

    rows = build.read_rows(input_path)
    groups = build.load_config(config_path)
    build.validate_config(rows, groups)  # raise sớm nếu products.yml lệch dữ liệu

    payload = build.build(rows, groups, "golden")
    # generated_at cố định "golden" ở trên (không dùng ngày hôm nay), nên
    # fixture ổn định giữa các lần chạy chừng nào input không đổi.

    os.makedirs(FIXTURES, exist_ok=True)
    out_path = os.path.join(FIXTURES, "export_golden.json")
    with open(out_path, "w", encoding="utf8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1, sort_keys=True)

    print(f"{out_path}: {len(payload['months'])} tháng, "
          f"{len(payload['groups'])} nhóm, mới nhất {payload['latest_period']}")


if __name__ == "__main__":
    main()
