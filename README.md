# Stackable Bin Rack — kệ khay xếp chồng

Cấu trúc thư mục và vai trò dữ liệu: [docs/STRUCTURE.md](docs/STRUCTURE.md).

Hai stand được dựng riêng từ profile và các mặt lắp cần thiết, giữ phong cách rack và gầm 20 mm. Quy tắc khay giữ `[100*dài,100*sâu+35,80*cao]` mm. Source hiện tại: `F377786477FA56ABE9B54C9868E0953C59197B70D1FEED311F759A7B4B74457B`. Tóm tắt kiểm chứng công khai tại [docs/validation/summary.md](docs/validation/summary.md); hồ sơ làm việc chi tiết là local-only.

`stackable-bin-rack.scad` là nguồn CSG có tham số cho `cap`, `frame`, `bin`, `stand` và `stand_bin`. Đơn vị mm. OpenSCAD 2026.09.29, backend Manifold. Mesh tham chiếu gốc không nằm trong snapshot công khai.

## Sử dụng

Danh mục có ảnh: [Chi tiết, tên gọi và vị trí lắp](docs/CHI-TIET.md). Tài liệu dùng mã CT01–CT05 cho năm part, kèm selector, mô tả, mặt lắp, tư thế in và STL của mẫu 1×1×1.

Mở `stackable-bin-rack.scad`. Mặc định `part="assembly"`, `size=[1,1,1]`, `asm_spec=[[size[0]]]`: một cụm khung, khay và nắp tại vị trí lắp. Đổi `size=[length,width,height]` bằng số nguyên dương để thay số ô theo ba chiều.

Khay ở tư thế sử dụng, theo thứ tự dài × sâu × cao:

- `[1,1,1]`: 100 × 135 × 80 mm.
- `[2,1,1]`: 200 × 135 × 80 mm.
- `[1,2,1]`: 100 × 235 × 80 mm, gồm thân sâu 200 mm và phần nhô 35 mm.
- `[1,1,2]`: 100 × 135 × 160 mm.
- `[2,2,2]`: 200 × 235 × 160 mm.

- `part="cap"`, `"frame"`, `"bin"`: xuất riêng ba chi tiết gốc tại tư thế in.
- `part="stand"`: vòng đế dựng riêng, bốn chân và bốn chốt nối frame. Tấm đế dày 8 mm nằm trên gầm 20 mm. Tổng chiều cao bản in, gồm chốt: 33 mm. Đường bao sạch với cửa sổ vát cạnh.
- `part="stand_bin"`: đế riêng thu vào 4 mm, rail/gờ tựa dựng chủ động để giữ bin trực tiếp, có bốn chân liền. Tổng chiều cao bản in, gồm rail: 38 mm. Các mẩu cột, notch và tab của frame được loại khỏi thiết kế stand.
- Hai stand in chân xuống bàn và dùng support dưới các nhịp đế. `foot_h=20` là khoảng cách từ mặt bàn đến mặt dưới tấm đế cho cả hai mẫu; gân chéo nằm sát chân. `stand_inset=4` điều khiển phần cắt vào trong của `stand_bin`.
- Chân của cả hai stand nằm sát bốn góc của chính tấm đế; bỏ khoảng lùi 1–2 mm cũ. Riêng `stand` giữ sai lệch dựng hình 0,01 mm theo X để tránh mặt suy biến. Hai gân bên hông cùng tiết diện tam giác danh nghĩa 10 × 10 mm và dày 7,98 mm, neo theo chân để không bị mask cắt lệch. Vát đáy chân 2 mm vẫn giữ.
- `part="layout"`: các chi tiết đặt cách nhau theo kích thước hiện tại để chuẩn bị in.
- `part="assembly"`: cụm lắp theo `asm_spec`; `[[1,2],[1,2]]` tạo hai tầng có cùng bố trí khung đơn và khung đôi. Các tầng dùng cùng thứ tự chia part để chốt/socket thẳng hàng. `[2]` và `[1,1]` có chiều dài vật lý khác nhau do viền riêng của từng frame; cấu hình trộn hai hàng này được báo lỗi.
- `part="assembly_bin"`: khay bin trên `stand_bin` tại vị trí lắp. `asm_stand=false` tắt stand của cụm frame thông thường.

Fusion native và hướng dẫn Change Parameters: [fusion/README.md](fusion/README.md). Fusion mặc định dựng một cụm lắp; tùy chọn layout đặt khoảng cách theo kích thước.

## Kích thước và vị trí

Khay dài `100*n`; frame tương ứng dài `span(n)=100*n+20`. Theo chiều sâu, thân tăng 100 mm mỗi ô, phần nhô giữ 35 mm; tấm frame rộng `100*size[1]+24`. Khay cao `80*size[2]`; đỉnh cột ở `80*size[2]+11`. Locator, thành và mép giữ kích thước. Các frame nối cạnh dùng bước `span(n)-0.07` của từng part; riêng khung đơn có pitch 119,93 mm.

Frame nằm tại mốc gốc. Cap lật socket xuống chốt. Miệng khay hướng −X, mặt sau tựa về rail +X; khay nhô 19 mm ra trước. Khi đổi size, cap và bin đi theo các mặt lắp của frame. Các frame chồng nhau theo `post_top`; frame cạnh nhau theo pitch dovetail.

Khe hở danh nghĩa quanh thân chốt 0,1 mm theo bán kính, đầu chốt 1 mm, mỗi bên khay 1 mm, phía trên khay 3 mm. Mặt đỡ khay, cap trên cột và dovetail tiếp xúc tại 0 mm. Dovetail giữ biên dạng tham chiếu với dung sai danh nghĩa bằng 0; độ chặt khi in cần mẫu thử thực tế.

## Kiểm chứng hiện hành

Ma trận SCAD hiện hành: `[1,1,1]`, `[2,1,1]`, `[3,1,1]`, `[1,2,1]`, `[1,1,2]`, `[2,2,2]`, `[1,3,2]`. Mỗi part có một mesh kín, winding nhất quán, 0 mặt suy biến; hai stand có gầm 20 mm. Hình học cap/frame/bin ở cả 7 size được giữ qua bounds và Boolean hai chiều so với revision trước khi dựng riêng stand.

- Khớp stand/frame giữ khe hướng kính khoảng 0,1 mm và khe đầu chốt 1 mm; hai đế đều có mặt tựa đo được với part tương ứng. Có thêm 9 vị trí mẫu khi cắm frame và 8 vị trí mẫu khi trượt bin.
- Các scene assembly, assembly_bin, cụm `[[1,2],[1,2]]` và layout `[2,2,2]` giữ đúng số object, mesh sạch và giao nhau dưới 0,001 mm³.
- Script Fusion và Contract được đồng bộ công thức; 31 kiểm tra offline công khai đạt trên bản copy chỉ gồm file bàn giao. Bộ local đầy đủ đạt34test, gồm thêm3test fit dùng helper/report local. Live/native Fusion của revision này mang trạng thái `not_run`.

STL hiện hành nằm tại `exports/size-multiplier/<size>/`, kèm manifest kích thước và hash. Các giới hạn kiểm chứng công khai nằm tại [docs/validation/summary.md](docs/validation/summary.md); báo cáo chi tiết, `fusion/validation/` và log là local-only. Lắp thực tế, lực kéo/đẩy và độ bền mang trạng thái `not_run`.

Kiểm tra in FDM ngày 2026-10-26 được tóm tắt tại [docs/validation/summary.md](docs/validation/summary.md). `NhietGiam` (230/210°C, flow 16) và preset đối chiếu (255/255°C, flow 8) là hai profile riêng; không được coi là cùng một mặc định. Slicing có bằng chứng offline, còn chất lượng bản in thực tế cần thử riêng.

## Xuất và kiểm tra

```powershell
$openscad = if ($env:OPENSCAD_BIN) { $env:OPENSCAD_BIN } else { 'openscad.com' }
& $openscad --backend=manifold --export-format=binstl -D 'part="frame"' -D 'size=[2,1,1]' -o frame.stl stackable-bin-rack.scad
$py = if (Get-Command python -ErrorAction SilentlyContinue) { 'python' } else { 'py' }
& $py -m unittest discover -s fusion/tests
& $py tools/render-parts-catalogue.py
```

3MF với lazy union giữ từng object riêng tại vị trí lắp. STL assembly hợp các mặt tiếp xúc thành mesh chung. STL từng part và layout phục vụ in riêng.

## Nguồn và giới hạn dựng lại

STL gốc tham chiếu và các bản sao trước rebuild không nằm trong snapshot công khai. Source dùng CSG độc lập; hash source và STL canonical được ghi trong manifest.

Các bo mép nhỏ của bin và một số fillet frame được giản lược; panel dùng biên góc đơn giản hơn tham chiếu. Khung dài giữ bốn cột góc theo mẫu x2 với kích thước theo quy tắc mới. Sai lệch toàn bề mặt STL/SCAD/Fusion được báo riêng với kiểm tra khớp lắp.

Bản tài liệu chi tiết trước cập nhật và checkpoint local không nằm trong snapshot công khai.
