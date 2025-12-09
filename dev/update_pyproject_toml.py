import argparse
import re
import subprocess
from pathlib import Path

import tomlkit
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from tomlkit import items


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="更新 pyproject.toml 中的依赖版本约束，同时保留注释和格式。"
    )
    parser.add_argument(
        "--mode",
        choices=["min", "exact", "compatible"],
        default="min",
        help=(
            "依赖冻结模式:\n"
            "  min:        使用 '>=' 约束 (默认)。\n"
            "  exact:      使用 '==' 约束，锁定到精确版本。\n"
            "  compatible: 使用 '~=' 约束，允许补丁更新。"
        ),
    )
    return parser.parse_args()


def get_installed_versions(console: Console):
    """获取当前环境中已安装包的版本，并显示进度"""
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("📊 获取已安装包版本...", total=None)

            result = subprocess.run(
                ["uv", "pip", "list", "--format", "freeze"],
                capture_output=True,
                text=True,
                check=True,
            )

            progress.update(task, description="✅ 版本获取完成")

    except (subprocess.CalledProcessError, FileNotFoundError):
        rprint("[red]❌ 无法执行 'uv pip list'。请确保 uv 已安装并在 PATH 中。[/red]")
        return {}

    versions = {}
    for line in result.stdout.strip().split("\n"):
        if "==" in line:
            pkg, ver = line.split("==", 1)
            versions[pkg.lower()] = ver

    rprint(f"  找到 [bold cyan]{len(versions)}[/bold cyan] 个已安装包")
    return versions


def parse_dependency_spec(dep):
    """解析依赖字符串，分离出包名、版本约束和环境标记"""
    dep = dep.strip()
    if ";" in dep:
        pkg_part, marker = dep.split(";", 1)
        pkg_part = pkg_part.strip()
        marker = ";" + marker.strip()
    else:
        pkg_part = dep
        marker = ""

    if "[" in pkg_part:
        match = re.match(r"^([a-zA-Z0-9_.-]+\[[^\]]+\])\s*([<=>!~].*)?$", pkg_part)
    else:
        match = re.match(r"^([a-zA-Z0-9_.-]+)\s*([<=>!~].*)?$", pkg_part)

    if match:
        pkg_name = match.group(1)
        constraint = match.group(2) or ""
        return pkg_name, constraint, marker

    return dep, "", ""


def update_dependencies_in_document(doc, versions, mode: str, console: Console):
    """在 tomlkit 文档对象中更新依赖版本，并返回更新结果"""
    updated_results = []

    def update_dep_list(dep_list, list_name=""):
        for i in range(len(dep_list)):
            dep_item = dep_list[i]
            if isinstance(dep_item, items.String):
                original_string = dep_item.value
                pkg_name, constraint, marker = parse_dependency_spec(original_string)
                base_pkg = pkg_name.split("[")[0].lower()

                if base_pkg in versions:
                    installed_version = versions[base_pkg]

                    if mode == "exact":
                        new_constraint = f"=={installed_version}"
                    elif mode == "compatible":
                        version_parts = installed_version.split(".")
                        if len(version_parts) >= 2:
                            compatible_base = ".".join(version_parts[:2])
                            new_constraint = f"~={compatible_base}"
                        else:
                            new_constraint = f"~={installed_version}"
                    else:  # 默认为 "min"
                        new_constraint = f">={installed_version}"

                    new_dep_string = f"{pkg_name}{new_constraint}{marker}"

                    if new_dep_string != original_string:
                        dep_list[i] = new_dep_string
                        updated_results.append(
                            {
                                "name": pkg_name,
                                "list": list_name,
                                "old": constraint or "(无约束)",
                                "new": new_constraint,
                                "status": "updated",
                            }
                        )
                    else:
                        updated_results.append(
                            {
                                "name": pkg_name,
                                "list": list_name,
                                "old": constraint,
                                "new": constraint,
                                "status": "unchanged",
                            }
                        )
                else:
                    updated_results.append(
                        {
                            "name": pkg_name,
                            "list": list_name,
                            "old": constraint,
                            "new": "N/A",
                            "status": "not_found",
                        }
                    )

    # --- 更新各个部分的依赖列表 ---
    if "project" in doc:
        project = doc["project"]
        if "dependencies" in project and isinstance(
            project["dependencies"], items.Array
        ):
            update_dep_list(project["dependencies"], "project.dependencies")

        if "optional-dependencies" in project and isinstance(
            project["optional-dependencies"], items.Table
        ):
            for group_name, deps in project["optional-dependencies"].items():
                if isinstance(deps, items.Array):
                    update_dep_list(deps, f"project.optional-dependencies.{group_name}")

    if "dependency-groups" in doc and isinstance(doc["dependency-groups"], items.Table):
        for group_name, deps in doc["dependency-groups"].items():
            if isinstance(deps, items.Array):
                update_dep_list(deps, f"dependency-groups.{group_name}")

    if "tool" in doc and isinstance(doc["tool"], items.Table) and "uv" in doc["tool"]:
        uv_config = doc["tool"]["uv"]
        if isinstance(uv_config, items.Table):
            for key in ["dev-dependencies", "test-dependencies", "docs-dependencies"]:
                if key in uv_config and isinstance(uv_config[key], items.Array):
                    update_dep_list(uv_config[key], f"tool.uv.{key}")

    return updated_results


def display_summary_table(results: list, console: Console):
    """使用 Rich 显示更新结果的汇总表格"""
    # 只显示已更新的项
    updated_items = [r for r in results if r["status"] == "updated"]

    if not updated_items:
        console.print(
            Panel("✅ 没有需要更新的依赖。", title="更新结果", border_style="green")
        )
        return

    table = Table(
        title="🔄 依赖更新摘要", show_header=True, header_style="bold magenta"
    )
    table.add_column("包名", style="cyan", no_wrap=True)
    table.add_column("所属列表", style="blue")
    table.add_column("旧约束", style="yellow")
    table.add_column("新约束", style="green")

    for item in updated_items:
        table.add_row(item["name"], item["list"], item["old"], item["new"])

    console.print(table)


def main():
    """主函数"""
    args = parse_args()
    console = Console()

    toml_path = Path("pyproject.toml")

    if not toml_path.exists():
        console.print(f"[red]❌ 找不到 {toml_path}[/red]")
        return

    console.print(
        Panel(
            f"🔄 开始分析和更新 pyproject.toml (模式: [bold cyan]{args.mode}[/bold cyan])...",
            title="依赖冻结工具",
            border_style="cyan",
        )
    )

    versions = get_installed_versions(console)
    if not versions:
        console.print("[red]无法获取已安装包版本，脚本退出。[/red]")
        return

    with open(toml_path, "r", encoding="utf-8") as f:
        content = f.read()
        doc = tomlkit.parse(content)

    update_results = update_dependencies_in_document(doc, versions, args.mode, console)

    # 显示汇总表格
    display_summary_table(update_results, console)

    updated_count = len([r for r in update_results if r["status"] == "updated"])

    if updated_count > 0:
        with open(toml_path, "w", encoding="utf-8") as f:
            f.write(tomlkit.dumps(doc))

        next_steps = (
            "[bold]1. 重新生成锁文件:[/bold] [cyan]uv lock[/cyan]\n"
            "[bold]2. 同步所有依赖组:[/bold] [cyan]uv sync --all-groups[/cyan]\n"
            "[bold]3. 验证更新:[/bold]       [cyan]uv pip list[/cyan]"
        )
        console.print(
            Panel(
                next_steps,
                title=f"✅ 成功更新 {updated_count} 个依赖",
                border_style="green",
            )
        )
    else:
        console.print(
            Panel(
                "ℹ️  没有需要更新的依赖。\n请查看上方的详细日志以了解每个依赖的处理情况。",
                title="更新完成",
                border_style="blue",
            )
        )


if __name__ == "__main__":
    main()
