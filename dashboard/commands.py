@main_cmd.group()
def server():
    pass


@server.command()
@click.argument('execute_arg', type=click.Choice(["shutdown", "restart", "flush_db"], case_sensitive=False))
@click.pass_context
def execute(ctx, execute_arg):
    print(f"op: {execute_arg}")


@main_cmd.command()
def plugins():
    pass






