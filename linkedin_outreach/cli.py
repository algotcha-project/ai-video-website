"""
CLI entry point for the LinkedIn outreach system.
Supports both single-account and multi-account modes.
"""

import sys
import json
import logging
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.logging import RichHandler

from .config import load_config
from .campaign import Campaign

console = Console()


def setup_logging(log_dir: str, campaign_name: str, verbose: bool = False) -> None:
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    level = logging.DEBUG if verbose else logging.INFO

    file_handler = logging.FileHandler(log_path / f"{campaign_name}.log")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s | %(name)s | %(levelname)s | %(message)s")
    )

    rich_handler = RichHandler(console=console, rich_tracebacks=True, show_path=False)
    rich_handler.setLevel(level)

    logging.basicConfig(level=logging.DEBUG, handlers=[file_handler, rich_handler])


@click.group()
@click.option("--config", "-c", default=None, help="Path to campaign_config.yaml")
@click.option("--verbose", "-v", is_flag=True, help="Enable debug logging")
@click.pass_context
def cli(ctx, config, verbose):
    """LinkedIn Buyer Outreach System"""
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = config
    ctx.obj["verbose"] = verbose


@cli.command()
@click.option("--cycles", default=1, help="Number of outreach cycles (0=infinite)")
@click.pass_context
def run(ctx, cycles):
    """Run the outreach campaign (single-account mode)."""
    cfg = load_config(ctx.obj["config_path"])
    setup_logging(cfg.log_dir, cfg.campaign_name, ctx.obj["verbose"])

    console.print(f"\n[bold green]Starting campaign:[/bold green] {cfg.campaign_name}\n")

    campaign = Campaign(cfg)
    campaign.start()

    if cycles == 1:
        summary = campaign.run_cycle()
        _print_summary(summary)
    else:
        campaign.run_continuous(cycles=cycles)


@cli.command(name="multi-run")
@click.option("--cycles", default=1, help="Number of outreach cycles (0=infinite)")
@click.pass_context
def multi_run(ctx, cycles):
    """Run outreach across all configured accounts (multi-account mode)."""
    cfg = load_config(ctx.obj["config_path"])
    setup_logging(cfg.log_dir, cfg.campaign_name, ctx.obj["verbose"])

    if not cfg.accounts:
        console.print(
            "[red]No accounts configured.[/red] Add an 'accounts' section to your "
            "campaign_config.yaml. See campaign_config.example.yaml for the format."
        )
        return

    from .multi_account import MultiAccountManager

    console.print(
        f"\n[bold green]Starting multi-account campaign:[/bold green] "
        f"{cfg.campaign_name} ({len(cfg.accounts)} accounts)\n"
    )

    manager = MultiAccountManager(cfg)

    console.print("[bold]Connecting accounts...[/bold]\n")
    results = manager.connect_all()
    for name, ok in results.items():
        status = "[green]OK[/green]" if ok else "[red]FAILED[/red]"
        console.print(f"  {name}: {status}")
    console.print()

    connected = sum(1 for v in results.values() if v)
    if connected == 0:
        console.print("[red]No accounts connected. Aborting.[/red]")
        return

    console.print(f"[bold]{connected}/{len(results)} accounts connected. Starting outreach...[/bold]\n")

    if cycles == 1:
        summaries = manager.run_cycle()
        _print_multi_summary(summaries)
    else:
        manager.run_continuous(cycles=cycles)


@cli.command(name="multi-stats")
@click.pass_context
def multi_stats(ctx):
    """Show statistics for multi-account campaign."""
    cfg = load_config(ctx.obj["config_path"])
    setup_logging(cfg.log_dir, cfg.campaign_name, ctx.obj["verbose"])

    if not cfg.accounts:
        console.print("[yellow]No accounts configured.[/yellow]")
        return

    from .multi_account import MultiAccountManager

    manager = MultiAccountManager(cfg)
    s = manager.get_stats()

    console.print(
        f"\n[bold]Campaign: {s['campaign']}[/bold] "
        f"({s['total_accounts']} accounts)\n"
    )

    table = Table(title="Prospect Pipeline", show_header=True, header_style="bold cyan")
    table.add_column("Status", min_width=25)
    table.add_column("Count", justify="right")
    for status, count in s["prospects"].items():
        table.add_row(status, str(count))
    console.print(table)

    console.print()
    for acct_name, acct_data in s["accounts"].items():
        table2 = Table(
            title=f"Account: {acct_name}",
            show_header=True,
            header_style="bold yellow",
        )
        table2.add_column("Metric", min_width=25)
        table2.add_column("Value", justify="right")
        table2.add_row("Segment", acct_data.get("segment", "-"))
        table2.add_row("Time Window", acct_data["time_window"])
        table2.add_row("Proxy", acct_data["proxy"])
        for metric, value in acct_data.get("today", {}).items():
            table2.add_row(metric, str(value))
        console.print(table2)
        console.print()


@cli.command()
@click.pass_context
def search(ctx):
    """Search for new prospects only (no outreach)."""
    cfg = load_config(ctx.obj["config_path"])
    setup_logging(cfg.log_dir, cfg.campaign_name, ctx.obj["verbose"])

    campaign = Campaign(cfg)
    campaign.start()

    prospects = campaign.finder.search_and_store(limit=50)
    console.print(f"\n[bold]Found {len(prospects)} new prospects:[/bold]\n")

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Name", min_width=20)
    table.add_column("Title", min_width=25)
    table.add_column("Company", min_width=20)
    table.add_column("Location", min_width=15)
    table.add_column("Mutual", justify="right")

    for p in prospects[:30]:
        table.add_row(
            p.full_name,
            p.job_title[:40],
            p.company[:25],
            p.location[:20],
            str(p.mutual_connections),
        )

    console.print(table)


@cli.command()
@click.pass_context
def stats(ctx):
    """Show campaign statistics (single-account mode)."""
    cfg = load_config(ctx.obj["config_path"])
    setup_logging(cfg.log_dir, cfg.campaign_name, ctx.obj["verbose"])

    campaign = Campaign(cfg)
    s = campaign.print_stats()

    console.print(f"\n[bold]Campaign: {s['campaign']}[/bold]\n")

    table = Table(title="Prospect Pipeline", show_header=True, header_style="bold cyan")
    table.add_column("Status", min_width=25)
    table.add_column("Count", justify="right")
    for status, count in s["prospects"].items():
        table.add_row(status, str(count))
    console.print(table)

    console.print()
    table2 = Table(title="Today's Usage", show_header=True, header_style="bold yellow")
    table2.add_column("Metric", min_width=25)
    table2.add_column("Value", justify="right")
    for metric, value in s["today_usage"].items():
        table2.add_row(metric, str(value))
    console.print(table2)


@cli.command()
@click.pass_context
def preview(ctx):
    """Preview messages that would be sent (dry run)."""
    cfg = load_config(ctx.obj["config_path"])
    setup_logging(cfg.log_dir, cfg.campaign_name, ctx.obj["verbose"])

    from .message_engine import MessageEngine
    from .prospect_store import Prospect

    engine = MessageEngine(cfg.messages)

    sample = Prospect(
        public_id="john-doe-123",
        first_name="John",
        last_name="Doe",
        headline="VP of Engineering at TechCorp",
        job_title="VP of Engineering",
        company="TechCorp",
        industry="Software Development",
        location="San Francisco, CA",
        mutual_connections=5,
    )

    console.print("\n[bold]Connection Note Previews[/bold] (3 random renders):\n")
    for i in range(3):
        note = engine.render_connection_note(sample)
        console.print(f"[dim]--- Variant {i + 1} ({len(note)} chars) ---[/dim]")
        console.print(note)
        console.print()

    console.print("[bold]Follow-up Message Previews:[/bold]\n")
    for i in range(cfg.messages.max_followups):
        msg = engine.render_followup(sample, i)
        if msg:
            console.print(f"[dim]--- Follow-up {i + 1} ---[/dim]")
            console.print(msg)
            console.print()

    if cfg.accounts:
        console.print(Panel(
            f"[bold]{len(cfg.accounts)} accounts configured[/bold]\n"
            + "\n".join(
                f"  {a.name}: {a.segment or 'no segment'} "
                f"({a.start_hour}:00-{a.end_hour}:00)"
                for a in cfg.accounts
            ),
            title="Multi-Account Setup",
        ))


@cli.command()
@click.pass_context
def export(ctx):
    """Export prospects to CSV."""
    cfg = load_config(ctx.obj["config_path"])
    from .prospect_store import ProspectStore

    store = ProspectStore(cfg.data_dir, cfg.campaign_name)
    prospects = store.all_prospects

    if not prospects:
        console.print("[yellow]No prospects to export.[/yellow]")
        return

    import csv
    from dataclasses import asdict

    out_path = Path(cfg.data_dir) / f"{cfg.campaign_name}_export.csv"
    fields = [
        "public_id", "first_name", "last_name", "job_title", "company",
        "industry", "location", "status", "mutual_connections",
        "connection_request_sent_at", "connected_at", "followups_sent",
        "profile_url", "tags",
    ]

    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for p in prospects:
            d = asdict(p)
            d["tags"] = ", ".join(d.get("tags", []))
            writer.writerow({k: d.get(k, "") for k in fields})

    console.print(f"[green]Exported {len(prospects)} prospects to {out_path}[/green]")


def _print_summary(summary: dict) -> None:
    console.print("\n[bold]Cycle Summary:[/bold]")
    table = Table(show_header=True, header_style="bold green")
    table.add_column("Metric")
    table.add_column("Count", justify="right")
    for k, v in summary.items():
        table.add_row(k.replace("_", " ").title(), str(v))
    console.print(table)


def _print_multi_summary(summaries: list[dict]) -> None:
    console.print("\n[bold]Multi-Account Cycle Summary:[/bold]\n")

    totals = {
        "prospects_found": 0,
        "connection_requests_sent": 0,
        "connections_accepted": 0,
        "followups_sent": 0,
        "errors": 0,
    }

    for s in summaries:
        name = s.get("account", "?")
        skipped = s.get("skipped", False)

        table = Table(title=f"Account: {name}", show_header=True, header_style="bold green")
        table.add_column("Metric")
        table.add_column("Count", justify="right")

        if skipped:
            table.add_row("Status", "[yellow]Skipped[/yellow]")
        else:
            for k in totals:
                val = s.get(k, 0)
                table.add_row(k.replace("_", " ").title(), str(val))
                totals[k] += val

        console.print(table)
        console.print()

    console.print("[bold]Combined Totals:[/bold]")
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Metric")
    table.add_column("Count", justify="right")
    for k, v in totals.items():
        table.add_row(k.replace("_", " ").title(), str(v))
    console.print(table)


def main():
    cli(obj={})


if __name__ == "__main__":
    main()
