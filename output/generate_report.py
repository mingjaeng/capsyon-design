import re
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

# 1. 기업 리스트
companies = ["셀바스헬스케어", "성우하이텍", "데브시스터즈","고려제강", "메카로", "한선엔지니어링"]

# 2. 한글 → 영문 기업명 매핑
company_name_map = {
    "셀바스헬스케어": "selvashealthcare",
    "성우하이텍": "sungwoo",
    "데브시스터즈": "devsisters",
    "고려제강": "kiswire",
    "메카로": "mecaro",
    "한선엔지니어링": "ehansun"
}

# 3. 마크다운 파일에서 최종 판단과 본문 추출
def parse_md_file(file_path):
    with open(file_path, encoding="utf-8") as f:
        lines = f.readlines()

    last_line = lines[-1].strip()
    body_md = "".join(lines)

    match = re.search(r"최종[\s]*판단[:：]?[\s]*(\w+)", last_line)
    opinion = match.group(1) if match else "의견 없음"

    return {
        "opinion": opinion,
        "markdown": body_md
    }

# 4. 이미지 그룹 빌드
def build_image_groups(company):
    categories = ["성장성", "수익성", "안정성", "시장가치", "활동성", "거시경제지표"]
    base_dir = Path(__file__).resolve().parent
    img_base = base_dir / "img" / company
    group_dict = {}

    for cat in categories:
        group_dir = img_base / cat
        if group_dir.exists():
            images = [f"../img/{company}/{cat}/{p.name}" for p in group_dir.glob("*.png")]
            if images:
                group_dict[cat] = images

    return group_dict

# 5. HTML 렌더링 및 저장
def generate_report(md_path, company: str):
    parsed = parse_md_file(md_path)
    image_groups = build_image_groups(company)
    base_dir = Path(__file__).resolve().parent
    templates_path = base_dir / "templates"
    env = Environment(loader=FileSystemLoader(str(templates_path)))
    template = env.get_template("markdown_viewer.html")

    # ✅ 영문 기업명 사용
    eng_name = company_name_map.get(company, company)

    output_html = template.render(
        company=company,
        opinion=parsed["opinion"],
        markdown=parsed["markdown"],
        image_groups=image_groups
    )

    output_path = base_dir / "output" / f"{eng_name}_report.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(output_html)

# 6. 실행 로직
def main():
    base_dir = Path(__file__).resolve().parent
    md_dir = base_dir / "output"

    for company in companies:
        md_file = md_dir / f"{company}.md"
        if md_file.exists():
            generate_report(md_file, company)
        else:
            print(f"[!] 마크다운 파일 없음: {company}")

if __name__ == "__main__":
    main()
