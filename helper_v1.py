def clean_prefix(input_file: str, output_file: str):
    with open(input_file, "r", encoding="utf-8") as fin, \
         open(output_file, "w", encoding="utf-8") as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            # Loại bỏ tiền tố
            if line.startswith("Thừa Thiên "):
                line = line.replace("Thừa Thiên ", "", 1)

            # Ghi lại với format chuẩn
            fout.write(f"{line}\n")


if __name__ == "__main__":
    clean_prefix("list_province.txt", "list_province_clean.txt")
