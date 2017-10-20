import sys
sys.path.append("./yum-utils")
sys.path.append("/usr/lib/python2.7/site-packages")
sys.path.append("/usr/lib64/python2.7/site-packages")

from flask import Flask, jsonify, request
from repodiff import DiffYum
import yum

app = Flask(__name__)

@app.route('/')
def diff():
    old_repo = request.args.get('old')
    new_repo = request.args.get('new')

    if (not old_repo or not new_repo):
        return jsonify({'error': 'old and new params are required'}), 400

    my = DiffYum()
    my.conf.disable_excludes = ['all']
    my.dy_shutdown_all_other_repos()
    my.dy_archlist = ['src']
    
    try:
        my.dy_setup_repo('old', old_repo)
    except yum.Errors.RepoError as e:
        return jsonify({'error': "Could not setup repo at url  %s: %s" % (old_repo, e)}), 500
    try:
        my.dy_setup_repo('new', new_repo)
    except yum.Errors.RepoError as e:
        return jsonify({'error': "Could not setup repo at url  %s: %s" % (new_repo, e)}), 500

    ygh = my.dy_diff(False)

    result = {'add': [], 'remove': [], 'update': [], 'downgrade': []}

    if ygh.add:
        for pkg in sorted(ygh.add):
            result['add'].append({'name': pkg.name, 'version': pkg.ver, 'release': pkg.rel})

    if ygh.remove:
        for pkg in sorted(ygh.remove):
            result['remove'].append({'name': pkg.name, 'version': pkg.ver, 'release': pkg.rel, 'obsoleted': pkg in ygh.obsoleted})

    if ygh.modified:
        for (pkg, oldpkg) in sorted(ygh.modified):
            if pkg.verGT(oldpkg):
                result['update'].append({'name': pkg.name, 'version': pkg.ver, 'release': pkg.rel, 'old_version': oldpkg.ver, 'old_release': oldpkg.rel})
            else:
                result['downgrade'].append({'name': pkg.name, 'version': pkg.ver, 'release': pkg.rel, 'old_version': oldpkg.ver, 'old_release': oldpkg.rel})

    return jsonify(result)
