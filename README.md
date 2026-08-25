# US Seafood Exports

Dashboard sản lượng, giá trị và giá bình quân (ASP) hàng thủy sản Mỹ **xuất khẩu**
ra thế giới, dữ liệu NOAA Fisheries, cập nhật tự động hằng ngày.

Đây là dashboard chị em của `us-seafood-imports` (nhập khẩu), dựng trên cùng
pipeline nhưng đổi bộ lọc nguồn NOAA sang `source=EXP` và chọn lại nhóm sản
phẩm theo cơ cấu xuất khẩu (khác hẳn cơ cấu nhập khẩu).

URL production: https://brospartners.github.io/us-seafood-exports/

## Nguồn dữ liệu

NOAA ODS `trade_data`: https://apps-st.fisheries.noaa.gov/ods/foss/trade_data/

Công khai, không cần API key. Bắt buộc gửi header `User-Agent`, thiếu là bị trả 403.

Lọc cố định `source=EXP` và `edible_code=E`. Grain sau khi gộp:
year × month × product × country (ở đây "country" là **thị trường xuất khẩu
đến**, không phải nước xuất xứ như bên dashboard nhập khẩu).

Nhóm sản phẩm khai báo ở `products.yml` — 7 nhóm thủy sản Mỹ xuất khẩu có tổng
giá trị (`value_usd`) lớn nhất trong toàn bộ lịch sử 2023-01 → 2026-06:

1. **Lobster** — `LOBSTER (HOMARUS SPP.) LIVE/FRESH`
2. **Pollock surimi** — `GROUNDFISH POLLOCK ALASKA SURIMI`
3. **Pollock fillet** — `GROUNDFISH POLLOCK ALASKA FILLET FROZEN`
4. **Salmon sockeye** — `SALMON SOCKEYE FROZEN`
5. **Salmon roe** — `SALMON NSPF ROE FROZEN`
6. **Cod** — `GROUNDFISH COD NSPF FROZEN`
7. **Crab** — `CRAB NSPF LIVE/FRESH`

Mỗi nhóm liệt kê riêng vài thị trường xuất khẩu lớn nhất (theo giá trị cộng
dồn); phần còn lại gộp vào "Other". Xem mục "Thêm một nhóm sản phẩm mới"
bên dưới để biết cách thêm nhóm khác.

**Không có số liệu thuế.** API không cung cấp trường Calculated Duty, nên
dashboard không có `ASP after tariff` — số liệu là giá khai báo hải quan xuất
khẩu, chưa cộng thuế nhập khẩu ở nước đến. Duty chỉ tồn tại trên giao diện
web FOSS, mà giao diện đó chặn IP datacenter nên không tự động lấy được.

Dữ liệu hiện đang commit trong repo: 2023-01 → 2026-06 (42 tháng), 47.229
dòng, trong `data/trade_exports.csv`. Hai tháng gần nhất tính tới ngày build
(2026-07, 2026-08) chưa có dữ liệu — NOAA công bố trễ khoảng 1,5 tháng, đây
là bình thường, không phải lỗi.

## Chạy local

```bash
pip install -r requirements.txt
python -m scripts.fetch     # ~3 phút, kéo lại toàn bộ từ 2023-01
python -m scripts.build     # nhanh
python -m http.server 8123 --directory .
```

## Thêm một nhóm sản phẩm mới

Thêm một mục vào `products.yml` rồi chạy `python -m scripts.build`. Không cần sửa code
và không cần kéo lại dữ liệu — `data/trade_exports.csv` đã chứa cả 500+ sản phẩm của NOAA.

`product` phải trùng tuyệt đối trường `name` của NOAA. Tra tên đúng bằng:

```bash
python -c "import csv;print(sorted({r['product'] for r in csv.DictReader(open('data/trade_exports.csv',encoding='utf8'))}))" | tr ',' '\n' | grep -i shrimp
```

**Lưu ý quan trọng:** `scripts.build` chỉ đọc `data/trade_exports.csv`, không tự chạy
trong job hằng ngày trừ khi CSV thay đổi (xem mục "Tự động cập nhật"). Nếu bạn chỉ sửa
`products.yml` mà không có dữ liệu NOAA mới, hãy tự chạy `python -m scripts.build` và
commit `data/dashboard.json` — job hằng ngày sẽ KHÔNG làm việc này giúp bạn.

## Nhóm mốc so sánh trên tab "Tổng hợp"

Tab "Tổng hợp" có một chart chênh lệch ASP giữa các nhóm so với một nhóm mốc
(`BASE_GROUP_KEY` trong `assets/app.js`). Dashboard nhập khẩu dùng "cá tra"
làm mốc (loài giá rẻ tham chiếu). Dashboard xuất khẩu này không có loài mốc
tự nhiên tương tự, nên chọn **tôm hùm (lobster)** — nhóm có tổng giá trị xuất
khẩu lớn nhất — làm mốc so sánh. Đổi mốc chỉ cần sửa hằng số `BASE_GROUP_KEY`.

## Test

```bash
python -m pytest -v
```

Một số test trong `tests/test_chart_colors.py` gọi ra Node để chạy trực tiếp các hàm
export từ `assets/app.js`. Các test này tự động skip nếu máy không có Node. Node không
cần thiết để chạy pipeline dữ liệu, chỉ cần để chạy nhóm test đó.

`tests/test_golden.py` đối chiếu `build.py` với một fixture tự sinh từ chính
`data/trade_exports.csv` + `products.yml` hiện tại của repo này (sinh bằng
`tests/make_golden.py`), không phải từ file Excel gốc như bên dashboard nhập
khẩu — vì dashboard xuất khẩu không kế thừa từ một workbook Excel tay nào.

Sinh lại fixture (khi `data/trade_exports.csv` hoặc `products.yml` đổi):

```bash
python tests/make_golden.py
```

## Tự động cập nhật

`.github/workflows/update.yml` chạy 22:00 UTC hằng ngày (05:00 giờ Việt Nam).
Chạy hằng ngày chứ không hằng tháng vì NOAA công bố trễ khoảng 1,5 tháng và không có
ngày cố định. Không có dữ liệu mới thì không commit.

Mỗi lần chạy kéo lại **toàn bộ** lịch sử, không kéo tăng dần, vì NOAA hiệu chỉnh lại
số của các tháng đã công bố.

Chặn an toàn: nếu NOAA trả về ít hơn 80% số dòng lần trước, `fetch.py` dừng và không
ghi đè. Test golden chạy trước bước commit nên dữ liệu hỏng không lên được dashboard.

Job quyết định "có gì thay đổi không" bằng cách diff duy nhất `data/trade_exports.csv`,
không phải toàn bộ thư mục `data/`. Lý do: `build.py` luôn ghi `generated_at` là ngày
chạy hiện tại vào `data/dashboard.json`, nên file này lúc nào cũng khác giữa hai lần
chạy và không dùng được làm tín hiệu "có thay đổi thật".

## Deploy

Đã bật GitHub Pages phục vụ thẳng nhánh `main` từ thư mục gốc, không có bước build riêng.
Vì Pages phục vụ ở đường dẫn con `/us-seafood-exports/`, mọi link nội bộ là đường dẫn
tương đối kèm đuôi `.html`.

Gắn vào BP Data Portal (`../bp-data-portal`) là một bước riêng, chưa thực hiện.

## Ngoài phạm vi

- Nạp Duty thủ công và các chỉ tiêu sau thuế (`ASP after tariff`, `% tariff estimated`).
- Dữ liệu nhập khẩu (`source=IMP`) — xem repo `us-seafood-imports`.
- Hàng không ăn được (`edible_code` khác `E`).
- Bộ lọc động cho toàn bộ 500+ sản phẩm trên giao diện.
