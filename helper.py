def clean_prefix(input_file: str, output_file: str):
    with open(input_file, "r", encoding="utf-8") as fin, \
         open(output_file, "w", encoding="utf-8") as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue

            parts = [p.strip() for p in line.split(",")]
            if len(parts) != 3:
                continue  # bỏ qua dòng sai định dạng

            ward, district, province = parts

            # Loại bỏ tiền tố "Tỉnh "
            if ward.startswith("Thị Trấn "):
                ward = ward.replace("Thị Trấn ", "", 1)

            # Ghi lại với format chuẩn
            fout.write(f"{ward}, {district}, {province}\n")


if __name__ == "__main__":
    clean_prefix("reference.txt", "ref_clean.txt")
