from typer.testing import CliRunner

from trading_bot import cli


def test_cli_help() -> None:
    runner = CliRunner()
    result = runner.invoke(cli.app, ["--help"])
    assert result.exit_code == 0
    assert "Trading bot CLI" in result.output
