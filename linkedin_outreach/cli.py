"""
CLI entry point for the LinkedIn outreach system.
"""

import sys
import json
import logging
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
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
    """Run the outreach campaign."""
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
    """Show campaign statistics."""
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
    out_path = Path(cfg.data_dir) / f"{cfg.campaign_name}_export.csv"
    fields = [
        "public_id", "first_name", "last_name", "job_title", "company",
        "industry", "location", "status", "mutual_connections",
        "connection_request_sent_at", "connected_at", "followups_sent",
        "profile_url",
    ]

    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for p in prospects:
            from dataclasses import asdict
            d = asdict(p)
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


def main():
    cli(obj={})


if __name__ == "__main__":
    main()
