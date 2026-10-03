from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

CommandFn = Callable[[list[str], object], int]

CATEGORY_ORDER = (
    "Shell",
    "Directory",
    "File",
    "System",
    "Network",
    "Servers",
    "Monitoring",
    "Logs",
    "Permissions",
    "Integration",
)


@dataclass(slots=True)
class CommandSpec:
    name: str
    handler: CommandFn
    help: str
    category: str = "Shell"
    usage: str = ""
    aliases: tuple[str, ...] = ()


class CommandRegistry:
    def __init__(self) -> None:
        self._commands: dict[str, CommandSpec] = {}

    def add(
        self,
        name: str,
        handler: CommandFn,
        help: str,
        category: str = "Shell",
        usage: str = "",
        aliases: tuple[str, ...] = (),
    ) -> None:
        spec = CommandSpec(
            name=name,
            handler=handler,
            help=help,
            category=category,
            usage=usage or name,
            aliases=aliases,
        )
        self._commands[name] = spec
        for alias in aliases:
            self._commands[alias] = spec

    def get(self, name: str) -> CommandSpec | None:
        return self._commands.get(name)

    def names(self) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for spec in self._commands.values():
            if spec.name not in seen:
                seen.add(spec.name)
                result.append(spec.name)
        return sorted(result)

    def by_category(self) -> dict[str, list[CommandSpec]]:
        grouped: dict[str, list[CommandSpec]] = {}
        seen: set[str] = set()
        for spec in self._commands.values():
            if spec.name in seen:
                continue
            seen.add(spec.name)
            grouped.setdefault(spec.category, []).append(spec)
        for specs in grouped.values():
            specs.sort(key=lambda item: item.name)
        return grouped

    def help_text(self, topic: str | None = None) -> str:
        if topic:
            return self._topic_help(topic)
        lines = [
            "dev_shell commands by category",
            "Type 'help <command>' for usage, 'help <category>' for one group.",
            "Type 'last' to show the previous command, 'history' for recent commands.",
            "",
        ]
        grouped = self.by_category()
        for category in CATEGORY_ORDER:
            specs = grouped.get(category)
            if not specs:
                continue
            lines.append(f"{category}")
            for spec in specs:
                alias = f"  ({', '.join(spec.aliases)})" if spec.aliases else ""
                lines.append(f"  {spec.name:<22} {spec.help}{alias}")
            lines.append("")
        leftover = [name for name in grouped if name not in CATEGORY_ORDER]
        for category in leftover:
            lines.append(f"{category}")
            for spec in grouped[category]:
                lines.append(f"  {spec.name:<22} {spec.help}")
            lines.append("")
        return "\n".join(lines).rstrip()

    def _topic_help(self, topic: str) -> str:
        key = topic.lower()
        spec = self.get(key)
        if spec is not None:
            aliases = f"\nAliases: {', '.join(spec.aliases)}" if spec.aliases else ""
            return (
                f"{spec.name}  [{spec.category}]\n"
                f"{spec.help}\n"
                f"Usage: {spec.usage}{aliases}"
            )
        grouped = self.by_category()
        for category, specs in grouped.items():
            if category.lower() == key or category.lower().startswith(key):
                lines = [f"{category}", ""]
                for item in specs:
                    lines.append(f"  {item.name:<22} {item.help}")
                    lines.append(f"    {item.usage}")
                return "\n".join(lines)
        return f"unknown help topic: {topic}. Type 'help' for categories."
