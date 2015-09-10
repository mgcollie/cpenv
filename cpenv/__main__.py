# -*- coding: utf-8 -*-
from .vendor import yaml, click
from . import api
from .shell import ShellScript
from .utils import unipath
import shutil
import logging

logger = logging.getLogger('cpenv')
# Couple aliases to clarify what's going on
echo = logger.debug
write = click.echo


def is_path(input_str):
    return '\\' in input_str or '/' in input_str


def get_environments(name_or_path):
    if is_path(name_or_path):
        return api.get_environments(root=name_or_path)
    else:
        return api.get_environments(name=name_or_path)


def list_envs():
    '''List available environments'''

    envs = api.get_environments()
    if not envs:
        echo('No available environments...use create to make one:')
        echo('    cpenv create <name_or_path>')
    else:
        echo('Available Environments:')
        echo('')
        for env in envs:
            echo('    [{}] {}'.format(env.name, env.root))
        echo('')
        echo('cpenv activate <name_or_path>')


def list_apps():
    '''List available application modules.'''

    active_env = api.get_active_env()
    if not active_env:
        echo('You must activate an environment first...')
        return

    echo('Available Application Modules:')
    echo('')
    for app in active_env.get_application_modules():
        echo('    [{}] {}'.format(app.name, app.command))
    echo('')
    echo('cpenv launch <module_name>')


@click.group()
def cli():
    '''Python Environment Management'''


@cli.command()
@click.argument('name_or_path', required=True)
@click.argument('module_repo', required=False)
@click.option('--module', required=False, is_flag=True, default=False)
@click.option('--config', required=False, type=click.Path(exists=True))
@click.pass_context
def create(ctx, name_or_path, module_repo, module, config):
    '''Create a new virtual environment.'''

    if module:

        if not module_repo:
            echo('Pass the path to a repo when creating an app module')
            echo('cpenv create --module maya2016 /local_repo/maya_module')

        active_env = api.get_active_env()
        if not active_env:
            echo('No active environment...')
            return

        active_env.add_application_module(module_repo, name_or_path)
        return

    echo('Creating new environment ' + name_or_path)
    if config:
        config = unipath(config)
        echo('Using configuration ' + config)

    if is_path(name_or_path):
        env = api.create_environment(root=name_or_path, config=config)
    else:
        env = api.create_environment(name=name_or_path, config=config)

    write(env.activate_script().as_string())


@cli.command()
@click.argument('name_or_path')
@click.option('--module', required=False, is_flag=True, default=False)
def remove(name_or_path, module):
    '''Remove a virtual environment.'''


    if module:

        active_env = api.get_active_env()
        if not active_env:
            echo('No active environment...')
            return

        active_env.rem_application_module(name_or_path)
        return


    envs = get_environments(name_or_path)

    if len(envs) > 1:
        echo('More then one environment matches {}...'.format(envs[0].name))
        list_envs()
        return

    env = envs[0]
    echo('Delete {}? (y/n)'.format(env.root))
    do_delete = True if raw_input() == 'y' else False
    if not do_delete:
        return

    echo('Removing environment ' + env.root)
    env.remove()


@cli.command()
@click.argument('name_or_path', required=False)
@click.option('--module', required=False, is_flag=True, default=False)
@click.pass_context
def activate(ctx, name_or_path, module):
    '''Activate a virtual environment.'''

    if module:

        if not name_or_path:
            list_apps()
            return

        active_env = api.get_active_env()
        if not active_env:
            echo('No active environment...')
            return

        mod = active_env.get_application_module(name_or_path)
        write(mod.activate_script().as_string())
        return

    if not name_or_path:
        list_envs()
        return

    envs = get_environments(name_or_path)

    if len(envs) > 1:
        echo('More then one environment matches {}...'.format(envs[0].name))
        list_envs()
        return

    env = envs[0]
    echo('Activating ' + env.name)
    write(env.activate_script().as_string())


@cli.command()
def deactivate():
    '''Deactivate the current environment.'''

    active_env = api.get_active_env()
    if not active_env:
        echo('No active environment...')
        return

    write(api.deactivate_script().as_string())


@cli.command()
@click.argument('module_name', required=False)
def launch(module_name):
    '''Launch an application module'''

    if not module_name:
        list_apps()
        return

    active_env = api.get_active_env()
    if not active_env:
        echo('You must activate an environment first...')
        return

    modules = active_env.get_application_modules()
    for mod in modules:
        if mod.name == module_name:
            mod.launch()
            return

    echo('Application module named {} does not exist...'.format(module_name))
    list_apps()


if __name__ == "__main__":
    cli()
