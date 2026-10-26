# Cấu trúc dự án stackable-bin-rack

Điểm bắt đầu: [README](../README.md). Source chính và script chạy giữ ở thư mục gốc. Chuẩn thư mục áp dụng ngày 26/10/2026.

## File và thư mục hiện có

Source: `stackable-bin-rack.scad; check_assembly.scad`.

- `reference/`: input tham chiếu local-only, không phát hành.
- [exports/](../exports/): đầu ra CAD, preview và report theo pipeline.
- [docs/](../docs/): tài liệu project và ảnh minh họa.
- [fusion/](../fusion/): script/manifest, hướng dẫn và test Fusion.
- `work/` và `backups/`: checkpoint/snapshot local-only, không phát hành.

Bộ STL hiện hành: `exports/size-multiplier/<size>/` với `manifest.json`. `docs/CHI-TIET.md` và `docs/parts` chứa catalogue. Kiểm thử tĩnh Fusion tại `fusion/tests`; chạy native theo workflow trong `fusion/README.md`.

## Quy ước dùng chung

- `exports/` chứa đầu ra; README/manifest xác định bộ hiện hành và revision nguồn.
- `reference/`, `work/`, `backups/` và các log/RPC là dữ liệu local-only; không dùng đường dẫn của chúng làm liên kết public.
- `docs/validation/summary.md` là bản tóm tắt đã sanitize của các giới hạn và số liệu cần thiết.
- `archive/` giữ phiên bản lịch sử khi project dùng cơ chế đó. Các thư mục chuyên biệt tiếp tục theo pipeline hiện có.
- Kiểm source/đường dẫn, render, native Fusion, slicer và thử vật lý có trạng thái bằng chứng riêng trong hồ sơ kỹ thuật.

## Tra đường dẫn lịch sử

Các tên lịch sử `out/`, `ref/`, `backup/`, `tmp/` chỉ áp dụng cho hồ sơ local cũ. Snapshot public chỉ dùng các đường dẫn tương đối đang tồn tại trong allowlist.
