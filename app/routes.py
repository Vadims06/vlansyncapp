from flask import Flask, render_template, jsonify, request, redirect, url_for, flash  # Import the Flask class
from mongoengine import Document, QuerySet, IntField, StringField, URLField
from mongoengine.errors import NotUniqueError
from pymongo.errors import NotMasterError
from flask_mongoengine import MongoEngine
from datetime import datetime, timedelta
import json
from redis import Redis
import rq
from worker import runTask
from rq.registry import ScheduledJobRegistry
from config import DB

app = Flask(__name__)    # Create an instance of the class for our use
app.config['SECRET_KEY'] = 'A random secret key'
app.config["MONGODB_HOST"] = DB.MONGO_HOST
app.config["MONGODB_PORT"] = DB.MONGO_PORT
app.config["MONGODB_DB"] = DB.MONGO_DB
db = MongoEngine(app)

class GetDBVlanQuerySet(QuerySet):

    def get_db_vlan_dd_ll(self):
        """
        return DB results without MongoDB _id
        """
        all_vlan_dd_ll = self.all().as_pymongo()
        for vlan_dd in all_vlan_dd_ll:
            del vlan_dd['_id']
        return list(all_vlan_dd_ll)

class Vlans(db.Document):
    
    vlan_id = IntField(required=True, unique=True)
    name = StringField(max_length=70)
    description = StringField(max_length=120)

    meta = {'queryset_class': GetDBVlanQuerySet}
    def __repr__(self):
        return {vlan_id: self.vlan_id, name: self.name, description: self.description}

app_redis = Redis.from_url('redis://redis:6379')
retrieve_vlans_queue = rq.Queue('device-query', connection=app_redis)
postpone_queue = ScheduledJobRegistry(queue=retrieve_vlans_queue)


@app.route("/", methods=['GET', 'POST'])
def vlans():
    vlans_attr_dd = Vlans.objects.all().as_pymongo() # return not BaseQueryList, but a list of dict
    vlans_attr_dd = sorted(vlans_attr_dd, key= lambda dd: dd.get('vlan_id', -1)) #{'_id': ObjectId('607ff46d7e2'),'vlan_id': 1,'name': 'TEST','description': ''}
    return render_template("vlans.html", vlans_attr_dd=vlans_attr_dd)

@app.route("/vlan-add", methods=['GET', 'POST'])
def vlan_add():
    _submit_add_vlan = request.form.get("_submit_add_vlan")
    _vlan_id = int(request.form.get("_vlan_id", -1))
    _vlan_name = request.form.get("_vlan_name")
    _vlan_description = request.form.get("_vlan_description")
    if _submit_add_vlan and _vlan_id > 0:
        vlan = Vlans(vlan_id = _vlan_id, name = _vlan_name, description = _vlan_description)
        try:
            vlan.save()
        except NotUniqueError as e: # we do not allow to create vlans with the same ID
            flash(e)
        else:
            return redirect(url_for('vlans'))
    return render_template("vlans-add.html")

@app.route('/delete_selected_vlans', methods=['POST'])
def delete_selected_vlans():
    """
    A method runs from JS script, when Delete buttons pressed and multiple vlans are selected for deletion
    """
    selected_vlans_ll_json = request.form.get("selected_vlans_ll_json", '')
    selected_vlans_ll = json.loads(selected_vlans_ll_json) if selected_vlans_ll_json else []
    for vlan_id in selected_vlans_ll:
        print(f"deleting vlan: {vlan_id}")
        vlan = Vlans.objects.get(vlan_id = vlan_id )
        vlan.delete()
    return redirect(url_for('vlans'))

@app.route("/editVlan/<vlan_id>", methods=['GET', 'POST'])
def vlan_edit(vlan_id = None):
    _submit_save_vlan = request.form.get("_submit_save_vlan")
    _submit_cancel = request.form.get("_submit_cancel")
    _vlan_name = request.form.get("_vlan_name")
    _vlan_description = request.form.get("_vlan_description")
    if vlan_id:
        vlan = Vlans.objects.get(vlan_id = vlan_id )
        if _submit_save_vlan:
            try:
                vlan.name = _vlan_name
                vlan.description = _vlan_description
                vlan.save()
            except NotMasterError:
                flash('cluster is not gathered')
            return redirect(url_for('vlans'))
        elif _submit_cancel:
            return redirect(url_for('vlans')) # a href doesn't work from web form
        return render_template("vlan-edit.html", vlan_attr_dd=vlan)
    else:
        return redirect(url_for('vlans'))


@app.route("/addVlan/")
@app.route("/addVlan/<vlan_id>")
def redis(vlan_id = None):
    """
 This is a part of a code for further improvement, when we received an SNMP ConfigChanged trap, it's better to put a task (retrieving Vlan database from a device) into a query. Anti-DDoS method if someone executes copy run start multiple times
    """
    job_id = ''
    if vlan_id:
        job = retrieve_vlans_queue.enqueue_in(timedelta(seconds=5), runTask, vlan_id=vlan_id, job_id=str(vlan_id))
        job_id = job.id

    postpone_jobs_id = ', '.join(postpone_queue.get_job_ids())
    tasks_in_query = ', '.join(retrieve_vlans_queue.get_job_ids())
    running_job_id = ', '.join(retrieve_vlans_queue.started_job_registry.get_job_ids())
    return {'created_job_id': job_id,
            'postpone_jobs_id': postpone_jobs_id,
            'tasks_in_query': tasks_in_query,
            'running_job_id': running_job_id}



if __name__ == '__main__':
    app.run(host='0.0.0.0')