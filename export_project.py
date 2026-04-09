import os

# ✅ Change these paths
project_path = r"C:\Users\dell\PycharmProjects\E-Commerce\stylemart"   # your project folder
output_file = r"C:\Users\dell\PycharmProjects\ecommerce_project_code.txt"  # where the result will be saved

with open(output_file, "w", encoding="utf-8") as f:
    for root, dirs, files in os.walk(project_path):
        for file in files:
            # Include the file types you want
            if file.endswith((".py", ".html", ".css", ".js", ".txt", ".json")):
                file_path = os.path.join(root, file)
                f.write(f"\n\n===== FILE: {file_path} =====\n\n")
                try:
                    with open(file_path, "r", encoding="utf-8") as src:
                        f.write(src.read())
                except Exception as e:
                    f.write(f"[Error reading file: {e}]")

print("✅ All files copied to:", output_file)
