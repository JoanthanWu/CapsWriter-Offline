import argparse
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path

import tomlkit
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)
from rich.prompt import Confirm, Prompt
from rich.table import Table


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="更新 Python 包到最新版本。")
    parser.add_argument(
        "--all",
        action="store_true",
        help="自动更新所有可更新的包（非交互模式）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只显示将要更新的包，不执行实际更新",
    )
    parser.add_argument(
        "--update-project",
        action="store_true",
        help="更新后自动运行 freeze_versions.py 更新 pyproject.toml",
    )
    parser.add_argument(
        "--exclude",
        nargs="*",
        help="要排除的包名列表",
    )
    return parser.parse_args()


def get_outdated_packages(console):
    """获取过时的包信息，并显示进度"""
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("🔍 检查可更新的包...", total=None)

            result = subprocess.run(
                ["uv", "pip", "list", "--outdated", "--format=columns"],
                capture_output=True,
                text=True,
                check=True,
            )

            progress.update(task, description="✅ 检查完成")
    except (subprocess.CalledProcessError, FileNotFoundError):
        console.print(
            "[red]❌ 无法执行 'uv pip list --outdated'。请确保 uv 已安装并在 PATH 中。[/red]"
        )
        return []

    outdated_packages = []
    lines = result.stdout.strip().split("\n")

    for line in lines[2:]:
        if line.strip():
            parts = re.split(r"\s{2,}", line.strip())
            if len(parts) >= 4:
                package_name = parts[0]
                current_version = parts[1]
                latest_version = parts[2]
                package_type = parts[3]

                if not re.match(r"^\d", latest_version):
                    console.print(
                        f"[yellow]⚠️  跳过包 '{package_name}'，其最新版本 '{latest_version}' 无效。[/yellow]"
                    )
                    continue

                outdated_packages.append(
                    {
                        "name": package_name,
                        "type": package_type,
                        "current": current_version,
                        "latest": latest_version,
                    }
                )

    return outdated_packages


def get_project_dependencies(console):
    """获取项目依赖列表"""
    project_deps = set()
    toml_path = Path("pyproject.toml")

    if not toml_path.exists():
        return project_deps

    with open(toml_path, "r", encoding="utf-8") as f:
        doc = tomlkit.parse(f.read())

    if "project" in doc and "dependencies" in doc["project"]:
        for dep in doc["project"]["dependencies"]:
            if isinstance(dep, str):
                pkg_name = (
                    dep.split(">=")[0]
                    .split("==")[0]
                    .split("~=")[0]
                    .split("[")[0]
                    .strip()
                )
                project_deps.add(pkg_name.lower())

    if "dependency-groups" in doc:
        for group_deps in doc["dependency-groups"].values():
            for dep in group_deps:
                if isinstance(dep, str):
                    pkg_name = (
                        dep.split(">=")[0]
                        .split("==")[0]
                        .split("~=")[0]
                        .split("[")[0]
                        .strip()
                    )
                    project_deps.add(pkg_name.lower())

    return project_deps


def display_packages_table(packages, console):
    """使用 Rich 显示可更新的包列表"""
    if not packages:
        console.print(
            Panel("✅ 所有包都是最新的！", title="检查结果", border_style="green")
        )
        return

    table = Table(title="🔄 可更新的包", show_header=True, header_style="bold magenta")
    table.add_column("序号", style="cyan", no_wrap=True, width=5)
    table.add_column("包名", style="blue", no_wrap=True, width=25)
    table.add_column("当前版本", style="yellow", width=15)
    table.add_column("最新版本", style="green", width=15)
    table.add_column("项目依赖", style="red", width=8)

    for i, pkg in enumerate(packages, 1):
        is_project = "[green]✅[/green]" if pkg["is_project"] else "[red]❌[/red]"
        table.add_row(str(i), pkg["name"], pkg["current"], pkg["latest"], is_project)

    console.print(table)


def interactive_select(packages, console):
    """交互式选择要更新的包"""
    console.print("\n[bold cyan]请选择要更新的包:[/bold cyan]")
    console.print("  - 输入序号，多个用空格分隔 (例如: [green]1 3 5[/green])")
    console.print("  - 输入 '[green]all[/green]' 更新所有包")
    console.print("  - 输入 '[green]project[/green]' 只更新项目依赖")
    console.print("  - 输入 '[green]none[/green]' 或直接回车跳过更新")

    while True:
        choice = Prompt.ask("\n您的选择", default="none").strip().lower()

        if not choice or choice == "none":
            return []
        elif choice == "all":
            return packages
        elif choice == "project":
            return [pkg for pkg in packages if pkg["is_project"]]
        else:
            try:
                indices = [int(x.strip()) - 1 for x in choice.split()]
                selected = []
                valid = True
                for idx in indices:
                    if 0 <= idx < len(packages):
                        selected.append(packages[idx])
                    else:
                        valid = False
                        break
                if valid:
                    return selected
                else:
                    console.print("[red]❌ 序号超出范围，请重新输入[/red]")
            except ValueError:
                console.print("[red]❌ 输入格式错误，请重新输入[/red]")


def update_packages(packages, dry_run=False, console=None):
    """执行包更新，并显示进度"""
    if not packages:
        console.print("⏭️  没有包需要更新")
        return True, []

    console.print(f"\n🚀 开始更新 [bold cyan]{len(packages)}[/bold cyan] 个包...")
    if dry_run:
        console.print("🔍 这是试运行模式，不会实际更新包")

    success_packages = []
    failed_packages = []

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        for pkg in packages:
            task = progress.add_task(f"更新 {pkg['name']}", total=1)

            package_spec = f"{pkg['name']}=={pkg['latest']}"

            if dry_run:
                progress.update(task, advance=1)
                success_packages.append(pkg)
                continue

            try:
                subprocess.run(
                    ["uv", "pip", "install", package_spec],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                progress.update(
                    task, description=f"✅ {pkg['name']} 更新成功", advance=1
                )
                success_packages.append(pkg)
            except subprocess.CalledProcessError:
                progress.update(
                    task, description=f"❌ {pkg['name']} 更新失败", advance=1
                )
                failed_packages.append(pkg)

    return len(failed_packages) == 0, success_packages


def update_project_toml(console):
    """更新 pyproject.toml"""
    console.print("\n📝 更新 pyproject.toml...")
    try:
        result = subprocess.run(
            ["uv", "run", "freeze_versions.py", "--mode", "min"],
            capture_output=True,
            text=True,
            check=True,
        )
        console.print("✅ pyproject.toml 更新成功")
        console.print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        console.print(f"[red]❌ pyproject.toml 更新失败[/red]\n{e.stderr}")
        return False


def generate_report(updated_packages, failed_packages, console):
    """生成更新报告"""
    report = {
        "timestamp": datetime.now().isoformat(),
        "updated": [pkg["name"] for pkg in updated_packages],
        "failed": [pkg["name"] for pkg in failed_packages],
        "total_updated": len(updated_packages),
        "total_failed": len(failed_packages),
    }

    report_path = Path("update_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    console.print(f"\n📊 更新报告已保存到: [cyan]{report_path}[/cyan]")
    return report


def main():
    """主函数"""
    args = parse_args()
    console = Console()  # 初始化 Rich Console

    console.print(
        Panel("🔍 检查可更新的包...", title="包更新工具", border_style="cyan")
    )

    outdated_packages = get_outdated_packages(console)
    project_deps = get_project_dependencies(console)

    for pkg in outdated_packages:
        pkg["is_project"] = pkg["name"].lower() in project_deps

    if args.exclude:
        exclude_set = set(name.lower() for name in args.exclude)
        outdated_packages = [
            pkg for pkg in outdated_packages if pkg["name"].lower() not in exclude_set
        ]
        if args.exclude:
            console.print(f"🚫 已排除包: [red]{', '.join(args.exclude)}[/red]")

    if not outdated_packages:
        console.print(
            Panel("🎉 所有包都是最新的！", title="检查结果", border_style="green")
        )
        return

    display_packages_table(outdated_packages, console)

    if args.all:
        selected_packages = outdated_packages
        console.print(
            f"\n🤖 自动模式：将更新所有 [bold cyan]{len(selected_packages)}[/bold cyan] 个包"
        )
    else:
        selected_packages = interactive_select(outdated_packages, console)

    if not selected_packages:
        console.print("⏭️  已取消更新")
        return

    if not args.dry_run:
        if not Confirm.ask(
            f"\n⚠️  即将更新 [bold cyan]{len(selected_packages)}[/bold cyan] 个包，这可能会影响项目兼容性\n确认继续？",
            default=False,
        ):
            console.print("⏭️  已取消更新")
            return

    success, updated_packages = update_packages(
        selected_packages, args.dry_run, console
    )
    failed_packages = [pkg for pkg in selected_packages if pkg not in updated_packages]

    report = generate_report(updated_packages, failed_packages, console)

    if success and args.update_project and not args.dry_run:
        update_project_toml(console)

    # 显示总结
    summary_text = f"✅ 成功更新: [green]{report['total_updated']}[/green] 个\n"
    summary_text += f"❌ 更新失败: [red]{report['total_failed']}[/red] 个"

    console.print(Panel(summary_text, title="📋 更新总结", border_style="blue"))

    if report["total_updated"] > 0:
        console.print("\n💡 建议后续操作:")
        console.print("  1. 运行测试确保项目正常")
        console.print(
            "  2. 更新 pyproject.toml ，注意：不要使用 [red]uv run[/red] ！\t而是使用 [cyan].venv\\Scripts\\python.exe dev\\update_pyproject_toml.py[/cyan]"
        )

    if not args.dry_run and report["total_failed"] > 0:
        console.print("\n⚠️  部分包更新失败，请检查错误信息并手动更新")


if __name__ == "__main__":
    main()
