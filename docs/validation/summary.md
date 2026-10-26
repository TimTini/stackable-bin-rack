# Tóm tắt kiểm chứng

Hồ sơ này ghi nguồn, artifact và phạm vi kiểm chứng của bản công khai ngày 26/10/2026.

## Source và hình học

- `stackable-bin-rack.scad`: SHA-256 `BCF8E5D5388478CD60DC3BD1944C13579CE0F58C3AAB314F0B9A3D16F40083A2`.
- Ma trận size: `[1,1,1]`, `[2,1,1]`, `[3,1,1]`, `[1,2,1]`, `[1,1,2]`, `[2,2,2]`, `[1,3,2]`.
- Năm part cap/frame/bin/stand/stand_bin qua bảy size tạo 35 mesh kín, một shell, winding nhất quán và 0 mặt suy biến trong audit local.
- Hai stand có khoảng cách mặt bàn–mặt dưới tấm đế 20 mm. Audit có kiểm tra khớp locator và các vị trí mẫu khi cắm frame/trượt bin.
- [Manifest canonical](../../exports/size-multiplier/manifest.json) ghi source hash và hash 35 STL.

## Kiểm tra offline

Bản công khai chạy độc lập **31 test**, đã xác minh trên bản copy chỉ gồm file bàn giao. Bộ local đầy đủ đạt **34 test**, gồm thêm 3 test fit-measurement dùng helper và report local. Các test công khai kiểm tra Contract, công thức, placement và cấu trúc source của builder.

Native Fusion của revision hiện hành giữ trạng thái `not_run`. Script core nằm tại [fusion/StackableBinRack](../../fusion/StackableBinRack/); hướng dẫn chạy nằm trong [Fusion README](../../fusion/README.md).

## FDM và profile

Hồ sơ local gồm 35 trường hợp Auto Orient và 10 job slice mẫu `[1,1,1]`: 5 baseline tắt support và 5 variant support45. Profile thực sự đã slice là `NhietGiam`: nozzle 230/210°C, bàn 90/85°C và lưu lượng tối đa 16 mm³/s.

Preset Generic PETG A1 hệ thống được đối chiếu qua JSON: nozzle 255/255°C, bàn 80/80°C, lưu lượng 8 mm³/s. Các số liệu slice đã ghi thuộc profile NhietGiam. Ngưỡng45° là lựa chọn sàng lọc/variant audit; preset support mặc định là30° và support tắt.

Audit đo hai facet trong bin khoảng41,4729°, mép cap gần45° và bridge tại trần socket frame. Variant support đã xử lý cảnh báo cantilever cụ thể của hai stand trong slicer. Chất lượng mặt dưới, tháo support, dung sai sau in, lực lắp, tải và độ bền vật lý giữ trạng thái `not_run`.

## Tái tạo

Dùng source SCAD ở gốc và [renderer portable](../../tools/render-parts-catalogue.py). `OPENSCAD_BIN` chọn executable; mặc định dùng `openscad.com` trong PATH. `requirements.txt` khai báo NumPy cho hai helper audit STL. Renderer ghi sáu ảnh và manifest trong `docs/parts/`; tùy chọn `--output` chọn thư mục xuất riêng.
