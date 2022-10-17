# -*- coding: utf-8 -*-

import logging

import ckan.plugins.toolkit as tk
import click
import datetime

log = logging.getLogger(__name__)


def get_commands():
    return [datastore_refresh]


@click.group(short_help="Manage datastore-refresh commands")
def datastore_refresh():
    """Manage datastore-refresh commands"""
    pass


@datastore_refresh.command()
@click.argument("frequency")
def dataset(frequency):
    """
    Refresh the datastore for a dataset
    """
    click.echo(f"Starting refresh_dataset_datastore for frequency {frequency}")
    if not frequency:
        tk.error_shout("Please provide frequency")

    site_user = tk.get_action("get_site_user")({"ignore_auth": True}, {})
    context = {"user": site_user.get("name")}
    try:
        datasets = tk.get_action(
            "datastore_refresh_dataset_refresh_list_by_frequency"
        )(context, {"frequency": frequency})
    except tk.ValidationError as e:
        tk.error_shout(e)
        raise click.Abort()

    if not datasets:
        click.secho("No datasets with this criteria", fg="yellow")
        return []

    for dataset in datasets["refresh_dataset_datastore"]:
        pkg_id = dataset["package"]["id"]
        pkg_dict = tk.get_action("package_show")(context, {"id": pkg_id})
        click.echo(
            f'Processing dataset {pkg_dict["name"]} with'
            f' {len(pkg_dict["resources"])} resources'
        )

        for res in pkg_dict["resources"]:
            try:
                _submit_resource(pkg_dict, res, context)
            except Exception as e:
                click.secho(e, fg="red")
                click.secho(f'ERROR submitting resource {res["id"]}', fg="red")
                continue

    click.echo(f"Finished refresh_dataset_datastore for frequency {frequency}")

def _validate_bad_datetime(context,data_dict):
        ''' Validate the datetime wih non ISO format
        '''
        existing_task = tk.get_action('task_status_show')(context, {
            'entity_id': data_dict['resource_id'],
            'task_type': 'xloader',
            'key': 'xloader'
        })
        if existing_task['last_updated']:
            try:
                datetime.datetime.strptime(
                    existing_task['last_updated'], '%Y-%m-%dT%H:%M:%S.%f')
            except ValueError:
                existing_task['last_updated'] = existing_task['last_updated'] + ".000"
                model = context['model']
                existing_task['state'] = 'error'
                tk.get_action('task_status_update')(
                {'session': model.meta.create_local_session(), 'ignore_auth': True},
                existing_task
            )
                return False
        return True

def _submit_resource(dataset, resource, context):
    """resource: resource dictionary"""
    # Copied and modifed from ckan/default/src/ckanext-xloader/ckanext/xloader/cli.py to check for Xloader formats before submitting
    # import here, so that that loggers are setup
    from ckanext.xloader.plugin import XLoaderFormats

    if not XLoaderFormats.is_it_an_xloader_format(resource["format"]):
        click.echo(
            f'Skipping resource {resource["id"]} because format'
            f' "{resource["format"]}" is not configured to be xloadered'
        )
        return
    if resource["url_type"] in ("datapusher", "xloader"):
        click.echo(
            f'Skipping resource {resource["id"]} because url_type'
            f' "{resource["url_type"]}" means resource.url points to the'
            " datastore already, so loading would be circular."
        )
        return

    click.echo(
        f'Submitting /dataset/{dataset["name"]}/resource/{resource["id"]}\n'
        f'url={resource["url"]}\n'
        f'format={resource["format"]}'
    )
    data_dict = {
        "resource_id": resource["id"],
        "ignore_hash": False,
    }

    if _validate_bad_datetime(context,data_dict):
        success = tk.get_action("xloader_submit")(context, data_dict)
    else:
        success = False
    if success:
        click.secho("...ok", fg="green")
    else:
        tk.error_shout("ERROR submitting resource")


@datastore_refresh.command()
def available_choices():
    """Shows available choices"""
    frequency_options = []
    data = tk.h.datastore_refresh_get_frequency_options()

    for row in data:
        if row["value"] != "0":
            frequency_options.append(row["value"])
    click.secho(f"Available choices: {frequency_options}", fg="green")
