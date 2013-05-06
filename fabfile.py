#!/usr/bin/python
# encoding: utf-8
from __future__ import with_statement
import os
import sys
import datetime
from fabric.api import cd, run, prefix, task, env, get, roles
from fabric.colors import yellow, green
from contextlib import contextmanager as _contextmanager

BASEDIR = os.path.realpath(os.path.join(os.path.dirname(__file__), os.path.pardir))
sys.path.append(BASEDIR)
os.environ['DJANGO_SETTINGS_MODULE'] = 'projectname.settings'

# globals
env.project = 'projectname'
env.roledefs = {
    'production':['LIST_OF_PRODUCTION_IPS'],
    'dev': ['LIST_OF_DEV_IPS']
}

env.user = 'youruser'
#env.password = 'password' 
env.key_filename = ['/path/to/your/key']
env.path = '/path/to/your/project/'
env.activate = 'source /path/to/your/virtualenv/bin/activate'
env.colors = True
env.format = True


@_contextmanager
def virtualenv():
    with cd(env.path):
        with prefix(env.activate):
            yield

@task
@roles('production')
def sync_migrate_db():
    "Migrate database"
    with virtualenv():
        print(yellow('Syncing and Migrating database'))
        run('python manage.py syncdb')
        run('python manage.py migrate')
        print(green('Done'))


@task
@roles('production')
def pull():
    "Pull files from git to server"
    with virtualenv():
        print(yellow('Reset Head'))
        run("git checkout -f")
        print(green('Done'))
        print(yellow('Pull files from server'))
        run("git pull origin master")
        print(green('Done'))
        run("git log -n 1")
        print(green('Done'))


@task
@roles('production')
def restart():
    "Restart webserver"
    print(yellow('Restart server'))
    # Supposing you're using supervisor to control your project
    run("supervisorctl restart projectname")
    print(green('Done'))


@task
def uninstall(package):
    "Remove packages from virtualenv"
    with virtualenv():
        run('pip uninstall %s' % package)


@task
def install(package):
    "Install package into virtualenv"
    with virtualenv():
        run('pip install %s' % package)


@task
@roles('production')
def collectstatic():
    "collect static files"
    with virtualenv():
        print(yellow("Collecting Files"))
        run("python manage.py collectstatic --noinput")
        print(green("Collect static complete!"))


@task
@roles('production')
def clear_thumbs():
    """
    If you're using solr-thumbail, a simple task to clear the thumbs
    Clear solr-thumbnail's key stored values in database
    """
    with virtualenv():
        print(yellow("Cleaning thumbs.."))
        run("python manage.py thumbnail clear")
        print(green("Cleaning thumbnails complete!"))


@task
@roles('production')
def makedump():
    """
    If you're using automysqlbackup to control your backups
    a simple command to generate a backup file
    """
    run('/etc/cron.hourly/automysqlbackup')


@task
@roles('production')
def deploy():
    "Send files to server and restart webserver"
    makedump()
    pull()
    sync_migrate_db()
    collectstatic()
    restart()

@task
@roles('production')
def getdump():
    """ Runs mysqldump. download the result to localhost """
    dir = '/tmp/mysqldumps/'
    run('mkdir -p %s' % dir)
    now = datetime.datetime.now().strftime("%Y.%m.%d-%H.%M")

    user = 'db_user'
    database = 'db_name'
    passwd = 'db_password'
    host = 'db_host'

    filename = os.path.join(dir, '%s-%s.sql' % (database, now))

    run('mysqldump --add-drop-table --host=%s -u%s -p%s %s > %s' % (host, user, passwd, database, filename))

    run("gzip {0}".format(filename))

    get("{0}.gz".format(filename), ".")

@task
@roles('production')
def getfile(path):
    """ gets a file from production server """
    get(path, '.')
