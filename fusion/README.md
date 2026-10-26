# Stackable Bin Rack — Fusion native

Source hiện hành: `BCF8E5D5388478CD60DC3BD1944C13579CE0F58C3AAB314F0B9A3D16F40083A2`. Script và Contract đã đồng bộ công thức khay `[100*len_n,100*wid_n+35,80*hgt_n]` mm ở tư thế sử dụng. Bộ công khai đạt31test; bộ local đầy đủ đạt34test, gồm thêm3test fit dùng helper/report local. Native runtime của revision này mang trạng thái `not_run`. Hai stand được dựng riêng trong SCAD; số liệu và giới hạn public nằm tại `../docs/validation/summary.md`.

Mặc định script dựng một cụm `cap` / `frame` / `bin` tại vị trí lắp. Các part là native solid, có sketch, feature và User Parameters. Kích thước dùng mm; Fusion API dùng cm.

Các kết quả live/native dưới đây thuộc source lịch sử `4BD55424EBFA4615D7207815DF69282AECFCACD0EC37124F41C7DFB751BC54ED`. Script hiện dựng ba part cap/frame/bin; hai stand cần bổ sung native riêng.

## Chạy và thay đổi kích thước

1. Fusion → Utilities → Scripts and Add-Ins → Scripts → thêm thư mục `StackableBinRack` → Run.
2. Script tạo document mới. Modify → Change Parameters → đổi `len_n`, `wid_n`, `hgt_n` bằng số nguyên dương.
3. `BUILD_POSE = "assembly"` đặt cụm lắp. `BUILD_POSE = "layout"` đặt tư thế in; đổi pose rồi Run tạo document mới.

Copy cả thư mục `StackableBinRack` để giữ script, Contract và manifest cùng nhau. SCAD có `asm_spec` cho nhiều hàng; script Fusion hiện dựng một cụm theo ba tham số kích thước.

Frame làm mốc tọa độ. Cap xoay 180° quanh X và đi theo `span`, `post_top + plate_t`. Bin xoay vào tư thế lắp và đi theo `plate_w - side_rail_w`, `(span + bin_W) / 2`, `plate_t`. Occurrence giữ transform identity; MoveFeature XYZ dùng expression để cập nhật vị trí cùng hình học.

## Phạm vi kiểm chứng

Ngày 2026-10-25, Fusion 2706.1.14, Windows. Ma trận local đã khảo sát: `[1,1,1]`, `[2,1,1]`, `[3,1,1]`, `[1,2,1]`, `[1,1,2]`, `[2,2,2]`, `[1,3,2]`. Chi tiết native local không phát hành; giới hạn public nằm tại `../docs/validation/summary.md`.

Mỗi trạng thái local kiểm tra số body, solid, timeline health, bounds theo công thức độc lập và native interference. Bản public không chứa RPC/log/report máy cục bộ.

Khe hở thiết kế: quanh thân chốt khoảng 0,1 mm theo bán kính, đầu chốt 1 mm, hai bên khay 1 mm mỗi bên, phía trên khay 3 mm. Dovetail và các mặt đỡ có tiếp xúc danh nghĩa 0 mm. Kết quả đo chi tiết và sai số mesh nằm trong progress log.

## Sửa lỗi resize

- Cache điểm sketch dùng expression thay vì giá trị số tại baseline, giữ dependency riêng khi các điểm ban đầu có cùng tọa độ.
- Polygon bo góc dùng construction support có dimension; profile fillet gắn vào support bằng constraints. Các cạnh sau trim giữ dependency khi span đổi.
- Gốc và đỉnh chốt dùng native Loft; pocket sàn/lưng dùng CutLoft theo biên dạng mặt thực.
- Miệng socket dùng CutLoft từ biên mở đến biên họng; cặp profile được ghép theo tâm XY.

## Kiểm tra lại

Từ project root (Python và Fusion chạy native được cài riêng):

```powershell
$py = if (Get-Command python -ErrorAction SilentlyContinue) { 'python' } else { 'py' }
& $py -m unittest discover -s fusion/tests
```

Chạy thư mục `fusion/StackableBinRack` như một script Fusion bình thường theo hướng dẫn ở trên. Các adapter RPC, build scratch và bộ đo fit local không thuộc snapshot public.

## Giới hạn và lịch sử

Miền kích thước đã kiểm tra là ma trận số nguyên dương phía trên. Fusion Change Parameters nhận đầu vào trực tiếp; người dùng nhập số ô nguyên dương. Thay đổi đồng thời về thành, bán kính, panel và kích thước cell cần kiểm tra riêng.

Pocket trang trí bên hông còn dùng chiến lược taper hiện có. Hình học Fusion có xấp xỉ so với SCAD; phép đo cơ cấu lắp và phép đo toàn bề mặt có phạm vi riêng. Slicer, sai số máy in, độ chặt thực tế và độ bền cơ học mang trạng thái `not_run`.

Evidence native chi tiết, adapter RPC, `validation/` và các báo cáo lịch sử là local-only. Snapshot public chỉ giữ core script folder, Contract, manifest, test tĩnh và bản tóm tắt đã sanitize.
