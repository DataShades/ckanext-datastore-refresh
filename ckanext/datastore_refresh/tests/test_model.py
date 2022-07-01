
import ckan.tests.helpers as helpers
import pytest

from ckanext.datastore_refresh.model import RefreshDatasetDatastore as rdd


@pytest.mark.usefixtures("with_plugins", "clean_db")
class TestRefreshDatasetDatastore:

    def test_create(self, package, sysadmin):
        results = rdd(
            dataset_id=package["id"],
            frequency="10",
            created_user_id=sysadmin["id"],
        )
        results.save()
        obj = rdd.get(results.id)

        assert obj.id is not None
        assert obj.dataset_id == package["id"]
        assert obj.frequency == "10"
        assert obj.created_user_id == sysadmin["id"]
        assert obj.datastore_last_refreshed is None


    @pytest.mark.freez_time
    def test_update(self, freezer, package, sysadmin, faker):

        results = rdd(
            dataset_id=package["id"],
            frequency="10",
            created_user_id=sysadmin["id"],
        )
        results.save()
        obj = rdd.get(results.id)

        assert obj.datastore_last_refreshed is None

        moment = faker.date_time()
        freezer.move_to(moment)

        helpers.call_action(
            "refresh_datastore_dataset_update",
            context={"auth_user_obj": sysadmin},
            package_id=obj.dataset_id,
        )
        assert obj.datastore_last_refreshed == moment



    def test_delete(self, package, sysadmin):
        results = rdd(
            dataset_id=package["id"],
            frequency="10",
            created_user_id=sysadmin["id"],
        )
        results.save()
        obj = rdd.get(results.id)

        assert obj
        rdd.delete(obj.id)
        assert rdd.get(obj.id) is None
