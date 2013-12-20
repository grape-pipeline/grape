#!/usr/bin/env python
#
# test cli utils
#
import jip
import os
import grape.tools

def test_check_dependencies(tmpdir):
    from grape.cli.utils import jip_prepare
    from grape.grape import Project
    import argparse
    os.environ['GRAPE_HOME'] = './home'
    pj = Project('project')
    parser = argparse.ArgumentParser()
    parser.add_argument("datasets", default=["all"], nargs="*")
    args = parser.parse_args(['setup'])
    jobs = jip_prepare(args, submit=True, project=pj, datasets=['setup'])
    jip.db.init(os.path.join(str(tmpdir), "test.db"))
    jip.db.save(jobs)
    args = parser.parse_args([])
    jobs = jip_prepare(args, submit=False, project=pj, datasets=pj.get_datasets())
    assert len(jobs) == 6
    jobs = jip_prepare(args, submit=True, project=pj, datasets=pj.get_datasets())
    assert len(jobs) == 4
    for job in jobs:
        assert str(job._tool) != 'grape_gem_index'
        assert str(job._tool) != 'grape_gem_t_index'





