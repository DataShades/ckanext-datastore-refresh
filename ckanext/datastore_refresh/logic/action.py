import logging

import ckan.plugins.toolkit as tk
from ckan.logic import validate

from ckanext.toolbelt.decorators import Collector

from ckanext.datastore_refresh.model import DatasetRefresh
from . import schema

action, get_actions = Collector("datastore_refresh").split()

log = logging.getLogger(__name__)
ValidationError = tk.ValidationError


@action
@validate(schema.dataset_refresh_create)
def dataset_refresh_create(context, data_dict):
    """Create a new dataset refresh schedule.

    :param package_id: id of the dataset
    :type package_id: string
    :param frequency: frequency of the refresh
    :type frequency: string

    :returns: the newly created refresh_dataset_datastore

    """
    tk.check_access(
        "datastore_refresh_dataset_refresh_create", context, data_dict
    )

    session = context["session"]
    user = context["auth_user_obj"]
    dataset = tk.get_action("package_show")(
        context, {"id": data_dict["package_id"]}
    )

    rdd_obj = DatasetRefresh(
        dataset_id=dataset["id"],
        frequency=data_dict["frequency"],
        created_user_id=user.id,
    )

    try:
        rdd_obj.save()
    except Exception as e:
        session.rollback()
        log.error("Error creating refresh_dataset_datastore: %s", e)
        raise ValidationError(
            {"package_id": ["Error while creating refresh_dataset_datastore"]}
        )

    return rdd_obj.dictize(context)


@action
@validate(schema.dataset_refresh_update)
def dataset_refresh_update(context, data_dict):
    """Update a dataset refresh schedule.

    :param package_id: id of the dataset
    :type package_id: string

    :returns: none
    """
    tk.check_access("datastore_refresh_dataset_refresh_update", context)

    log.info("Check Datastore Refresh for the Dataset")
    rdd_obj = DatasetRefresh.get_by_package_id(data_dict["package_id"])
    if not rdd_obj:
        log.error(
            "Refresh_dataset_datastore not found: %s", data_dict["package_id"]
        )
        raise tk.ObjectNotFound()

    log.info("Updating refresh_dataset_datastore: %s", rdd_obj)
    rdd_obj.touch()
    rdd_obj.save()

    log.info("Updated refresh_dataset_datastore.")

    return rdd_obj.dictize(context)


@action
@tk.side_effect_free
def dataset_refresh_list(context, data_dict):
    """List all dataset refresh schedules.

    :returns: a list of all refresh_dataset_datastores
    """
    tk.check_access("datastore_refresh_dataset_refresh_list", context)
    results = results = DatasetRefresh.get_all()

    return {
        "refresh_dataset_datastore": DatasetRefresh.dictize_collection(
            results, dict(context, dataset_refresh_include_package=True)
        )
    }


@action
@validate(schema.dataset_refresh_list_by_frequency)
def dataset_refresh_list_by_frequency(context, data_dict):
    """List all dataset refresh schedules by frequency.

    :param frequency: frequency of the refresh
    :type frequency: string

    :returns: a list of all refresh_dataset_datastores by frequency

    """
    tk.check_access(
        "datastore_refresh_dataset_refresh_list_by_frequency", context
    )

    results = DatasetRefresh.get_by_frequency(data_dict.get("frequency"))

    return {
        "refresh_dataset_datastore": DatasetRefresh.dictize_collection(
            results, dict(context, dataset_refresh_include_package=True)
        )
    }


@action
@validate(schema.dataset_refresh_delete)
def dataset_refresh_delete(context, data_dict):
    """Delete a dataset refresh schedule.

    :param id: id of the refresh_dataset_datastore
    :type id: string

    :returns: the deleted refresh_dataset_datastore

    """
    tk.check_access("datastore_refresh_dataset_refresh_delete", context)

    rdd_id = data_dict["id"]
    log.info("Deleting refresh_dataset_datastore: %s", rdd_id)
    rdd_obj = DatasetRefresh.get(rdd_id)

    if not rdd_obj:
        log.error("Refresh_dataset_datastore not found: %s", rdd_id)
        raise ValidationError("Not found")

    DatasetRefresh.delete(rdd_id)
