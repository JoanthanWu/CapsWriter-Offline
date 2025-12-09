import argparse
import re
import subprocess
from datetime import datetime
from pathlib import Path

import tomlkit
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="检查 Python 包的更新情况。")
    parser.add_argument(
        "--format",
        choices=["table", "json", "simple"],
        default="table",
        help="输出格式: table (表格), json (JSON), simple (简单列表)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="显示所有包，包括没有更新的包",
    )
    return parser.parse_args()


def get_outdated_packages():
    """获取过时的包信息"""
    try:
        # 使用 rich 的进度条显示加载状态
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=Console(stderr=True),
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
        rprint(
            "[red]❌ 无法执行 'uv pip list --outdated'。请确保 uv 已安装并在 PATH 中。[/red]"
        )
        return []

    outdated_packages = []
    lines = result.stdout.strip().split("\n")

    # 跳过标题行和分隔线
    for line in lines[2:]:
        if line.strip():
            # 实际格式: Package | Version | Latest | Type
            parts = re.split(r"\s{2,}", line.strip())
            if len(parts) >= 4:
                package_name = parts[0]
                current_version = parts[1]
                latest_version = parts[2]
                package_type = parts[3]

                # 增加版本号验证，防止解析错误
                if not re.match(r"^\d", latest_version):
                    rprint(
                        f"[yellow]⚠️  跳过包 '{package_name}'，其最新版本 '{latest_version}' 无效。[/yellow]"
                    )
                    continue

                outdated_packages.append(
                    {
                        "name": package_name,
                        "type": package_type,
                        "current": current_version,
                        "latest": latest_version,
                        "status": "outdated",
                    }
                )

    return outdated_packages


def get_all_packages():
    """获取所有已安装的包"""
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=Console(stderr=True),
        ) as progress:
            task = progress.add_task("📦 获取所有已安装包...", total=None)

            result = subprocess.run(
                ["uv", "pip", "list", "--format=freeze"],
                capture_output=True,
                text=True,
                check=True,
            )

            progress.update(task, description="✅ 获取完成")
    except (subprocess.CalledProcessError, FileNotFoundError):
        rprint("[red]❌ 无法执行 'uv pip list'。请确保 uv 已安装并在 PATH 中。[/red]")
        return []

    packages = []
    for line in result.stdout.strip().split("\n"):
        if "==" in line:
            pkg, ver = line.split("==", 1)
            packages.append(
                {"name": pkg, "current": ver, "latest": ver, "status": "up-to-date"}
            )

    return packages


def format_rich_table_output(outdated_packages, all_packages=None, show_all=False):
    """使用 rich 格式化为表格输出"""
    console = Console()

    if show_all and all_packages:
        packages = all_packages
        title = "📋 所有已安装包的状态"
    else:
        packages = outdated_packages
        title = "🔄 可更新的包"

    if not packages:
        console.print(
            Panel("✅ 所有包都是最新的！", title="检查结果", border_style="green")
        )
        return

    # 创建表格
    table = Table(title=title, show_header=True, header_style="bold magenta")

    if show_all:
        table.add_column("包名", style="cyan", no_wrap=True, width=25)
        table.add_column("当前版本", style="blue", width=15)
        table.add_column("最新版本", style="green", width=15)
        table.add_column("状态", style="yellow", width=10)
        table.add_column("项目依赖", style="red", width=8)

        for pkg in packages:
            if pkg["status"] == "up-to-date":
                status = "[green]✅ 最新[/green]"
            else:
                status = "[yellow]🔄 可更新[/yellow]"

            is_project = (
                "[green]✅[/green]" if pkg.get("in_project") else "[red]❌[/red]"
            )

            table.add_row(
                pkg["name"], pkg["current"], pkg["latest"], status, is_project
            )
    else:
        table.add_column("包名", style="cyan", no_wrap=True, width=25)
        table.add_column("当前版本", style="blue", width=15)
        table.add_column("最新版本", style="green", width=15)
        table.add_column("类型", style="yellow", width=10)
        table.add_column("项目依赖", style="red", width=8)

        for pkg in packages:
            is_project = (
                "[green]✅[/green]" if pkg.get("in_project") else "[red]❌[/red]"
            )

            table.add_row(
                pkg["name"],
                pkg["current"],
                pkg["latest"],
                pkg.get("type", "N/A"),
                is_project,
            )

    console.print(table)


def format_table_output(outdated_packages, all_packages=None, show_all=False):
    """格式化为表格输出（使用 rich）"""
    format_rich_table_output(outdated_packages, all_packages, show_all)


def format_json_output(outdated_packages, all_packages=None, show_all=False):
    """格式化为 JSON 输出"""

    if show_all and all_packages:
        packages = all_packages
    else:
        packages = outdated_packages

    output = {
        "timestamp": datetime.now().isoformat(),
        "total_packages": len(packages),
        "packages": packages,
    }

    if not show_all:
        output["outdated_count"] = len(packages)

    console = Console()
    console.print_json(data=output)


def format_simple_output(outdated_packages, all_packages=None, show_all=False):
    """格式化为简单列表输出（使用 rich）"""
    console = Console()

    if show_all and all_packages:
        packages = all_packages
        title = "📋 所有包状态:"
    else:
        packages = outdated_packages
        title = "🔄 可更新的包:"

    if not packages:
        console.print(
            Panel("✅ 所有包都是最新的！", title="检查结果", border_style="green")
        )
        return

    console.print(f"\n[bold]{title}[/bold]")
    console.print("─" * 50)

    for pkg in packages:
        if show_all:
            if pkg["status"] == "up-to-date":
                status = "[green]✅[/green]"
            else:
                status = "[yellow]🔄[/yellow]"

            is_project = " [dim](项目依赖)[/dim]" if pkg.get("in_project") else ""
            console.print(
                f"{status} [cyan]{pkg['name']}[/cyan]: [blue]{pkg['current']}[/blue] → [green]{pkg['latest']}[/green]{is_project}"
            )
        else:
            is_project = " [dim](项目依赖)[/dim]" if pkg.get("in_project") else ""
            console.print(
                f"[yellow]🔄[/yellow] [cyan]{pkg['name']}[/cyan]: [blue]{pkg['current']}[/blue] → [green]{pkg['latest']}[/green]{is_project}"
            )


def check_pyproject_updates():
    """检查 pyproject.toml 中定义的依赖是否有更新"""
    toml_path = Path("pyproject.toml")

    if not toml_path.exists():
        return None

    with open(toml_path, "r", encoding="utf-8") as f:
        doc = tomlkit.parse(f.read())
    project_deps = []

    # 收集 project.dependencies
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
                project_deps.append(pkg_name.lower())

    # 收集 dependency-groups
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
                    project_deps.append(pkg_name.lower())

    return project_deps


def display_statistics(
    outdated_packages, all_packages=None, show_all=False, project_deps=None
):
    """显示统计信息（使用 rich）"""
    console = Console()

    if not show_all:
        outdated_count = len(outdated_packages)
        if outdated_count > 0:
            # 创建统计面板
            stats_text = f"[bold green]{outdated_count}[/bold green] 个包可以更新"

            if project_deps:
                project_outdated = [
                    p for p in outdated_packages if p["name"].lower() in project_deps
                ]
                if project_outdated:
                    stats_text += f"\n其中 [bold blue]{len(project_outdated)}[/bold blue] 个是项目依赖"
                    stats_text += "\n\n💡 运行 '[cyan]uv run dev\\update_site_packages.py[/cyan]' 来更新 pyproject.toml"

            console.print(Panel(stats_text, title="📊 统计信息", border_style="blue"))
        else:
            console.print(
                Panel("🎉 所有包都是最新的！", title="检查结果", border_style="green")
            )
    else:
        total_count = len(all_packages) if all_packages else 0
        outdated_count = (
            len([p for p in all_packages if p["status"] == "outdated"])
            if all_packages
            else 0
        )
        up_to_date_count = total_count - outdated_count

        stats_text = f"总共: [bold]{total_count}[/bold] 个包\n"
        stats_text += f"可更新: [bold yellow]{outdated_count}[/bold yellow] 个包\n"
        stats_text += f"最新: [bold green]{up_to_date_count}[/bold green] 个包"

        console.print(Panel(stats_text, title="📊 统计信息", border_style="blue"))


def main():
    """主函数"""
    args = parse_args()
    console = Console()

    # 显示开始信息
    console.print(
        Panel("🔍 检查包更新情况...", title="包更新检查器", border_style="cyan")
    )

    # 获取过时的包
    outdated_packages = get_outdated_packages()

    # 如果需要显示所有包，获取所有已安装包
    all_packages = None
    if args.all:
        all_packages = get_all_packages()
        # 合并信息
        for pkg in all_packages:
            for outdated in outdated_packages:
                if pkg["name"].lower() == outdated["name"].lower():
                    pkg["latest"] = outdated["latest"]
                    pkg["status"] = "outdated"
                    break

    # 检查 pyproject.toml 中的依赖
    project_deps = check_pyproject_updates()
    if project_deps:
        console.print(
            f"\n📋 发现 [bold blue]{len(project_deps)}[/bold blue] 个 pyproject.toml 中定义的依赖"
        )

        # 标记项目依赖
        if args.all and all_packages:
            for pkg in all_packages:
                if pkg["name"].lower() in project_deps:
                    pkg["in_project"] = True
        else:
            for pkg in outdated_packages:
                if pkg["name"].lower() in project_deps:
                    pkg["in_project"] = True

    # 根据格式输出
    if args.format == "table":
        format_table_output(outdated_packages, all_packages, args.all)
    elif args.format == "json":
        format_json_output(outdated_packages, all_packages, args.all)
    else:  # simple
        format_simple_output(outdated_packages, all_packages, args.all)

    # 显示统计信息
    display_statistics(outdated_packages, all_packages, args.all, project_deps)


if __name__ == "__main__":
    main()
