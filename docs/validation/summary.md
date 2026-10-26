# Tóm tắt kiểm chứng

Hồ sơ này ghi nguồn, artifact và phạm vi kiểm chứng của bản công khai ngày 26/10/2026.

## Source và hình học

- `stackable-bin-rack.scad`: SHA-256 `9E519D4E3312E77B0DE24FFB8A723AFE75BC02D0FB733013B7B6C5CB413130C9`.
- Ma trận size: `[1,1,1]`, `[2,1,1]`, `[3,1,1]`, `[1,2,1]`, `[1,1,2]`, `[2,2,2]`, `[1,3,2]`.
- Năm part cap/frame/bin/stand/stand_bin qua bảy size tạo 35 mesh kín, một shell, winding nhất quán và 0 mặt suy biến trong audit local.
- Hai stand có khoảng cách mặt bàn–mặt dưới tấm đế 20 mm. Audit có kiểm tra khớp locator và các vị trí mẫu khi cắm frame/trượt bin.
- [Manifest canonical](../../exports/size-multiplier/manifest.json) ghi source hash và hash 35 STL.

## Kiểm tra offline

Bản công khai chạy độc lập **31 test**, đã xác minh trên bản copy chỉ gồm file bàn giao. Bộ local đầy đủ đạt **34 test**, gồm thêm 3 test fit-measurement dùng helper và report local. Các test công khai kiểm tra Contract, công thức, placement và cấu trúc source của builder.

Native Fusion của revision hiện hành giữ trạng thái `not_run`. Script core nằm tại [fusion/StackableBinRack](../../fusion/StackableBinRack/); hướng dẫn chạy nằm trong [Fusion README](../../fusion/README.md).

## FDM và profile

Hồ sơ revision trước gồm 35 trường hợp Auto Orient và 10 job slice mẫu `[1,1,1]`: 5 baseline tắt support và 5 variant support45. Profile thực sự đã slice là `NhietGiam`: nozzle 230/210°C, bàn 90/85°C và lưu lượng tối đa 16 mm³/s.

Preset Generic PETG A1 hệ thống được đối chiếu qua JSON: nozzle 255/255°C, bàn 80/80°C, lưu lượng 8 mm³/s. Các số liệu slice đã ghi thuộc profile NhietGiam. Ngưỡng45° là lựa chọn sàng lọc/variant audit; preset support mặc định là30° và support tắt.

Audit đo hai facet trong bin khoảng41,4729°, mép cap gần45° và bridge tại trần socket frame. Variant support đã xử lý cảnh báo cantilever cụ thể của hai stand trong slicer. Chất lượng mặt dưới, tháo support, dung sai sau in, lực lắp, tải và độ bền vật lý giữ trạng thái `not_run`.

## Tái tạo

Dùng source SCAD ở gốc và [renderer portable](../../tools/render-parts-catalogue.py). `OPENSCAD_BIN` chọn executable; mặc định dùng `openscad.com` trong PATH. `requirements.txt` khai báo NumPy cho hai helper audit STL. Renderer ghi sáu ảnh và manifest trong `docs/parts/`; tùy chọn `--output` chọn thư mục xuất riêng.

## Cập nhật chân sát góc — 26/10/2026

- Bỏ khoảng lùi chân 1–2 mm; chân theo mép tấm của từng stand. `stand_bin` vẫn có tấm thu vào 4 mm so với frame. `stand` chỉ giữ sai lệch dựng hình 0,01 mm theo X để tránh facet suy biến. Gầm 20 mm và vát đáy 2 mm giữ nguyên.
- Hai gân bên hông 10 × 10 × 7,98 mm của revision trước đã bỏ trên cả `stand` và `stand_bin`. Tâm khối cũ của mỗi gân phải nằm ngoài mesh; bốn chân và vát đáy 2 mm giữ nguyên.
- Regression đo đúng bốn chân ở cả 7 size; 35 mesh qua kiểm tra kín, một shell, winding và 0 facet suy biến. Khớp lắp, các vị trí mẫu khi cắm frame/trượt bin và hình học cap/frame/bin được kiểm tra lại so với STL revision trước. 34 test offline local đạt.
- Bốn scene assembly, assembly_bin, cụm hỗn hợp và layout đạt; thể tích giao nhau dưới 0,001 mm³. Kiểm tra riêng hai stand ghép cạnh nhau bắt lỗi nới mask 0,01 mm và xác nhận hết cấn sau khi bỏ phần nới.
- Đối chiếu revision `870a09f` trước khi bỏ bốn gân, Bambu A1 0,4 mm, lớp 0,20 mm, profile NhietGiam và support45, giữ tư thế chân xuống bàn: bốn job đối chiếu hai mẫu cũ/mới đều trả mã 0, có G-code và không có cảnh báo. Dự tính slicer: stand 149,35 → 144,61 phút, 75,96 → 74,97 g; stand_bin 143,03 → 142,49 phút, 72,96 → 73,08 g. Đây là dự tính của slicer với support bật; các nhịp đế dài vẫn cần support.
- STL canonical, ảnh catalogue và manifest đã cập nhật theo source hash đầu tài liệu. Native Fusion, chất lượng in, fit và tải vật lý của revision mới vẫn `not_run`.

Bốn gân XZ trước/sau đã bỏ ở revision trước; hai gân YZ bên hông của revision đó cũng đã bỏ trên cả hai mẫu. Regression chân 7 size xác nhận tâm khối cũ của gân nằm ngoài mesh. 34 test offline đạt. Chưa slice lại và chưa in bản không gân; các nhịp đế dài vẫn cần support.
