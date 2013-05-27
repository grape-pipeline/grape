"""The grape job store module
"""
import os
import grape.jobs


class StoreException(Exception):
    """Exception raised by the job store"""
    pass


class PipelineStore(object):
    """Simple file based store that persists
    all the jobs in a pipeline
    """

    def __init__(self, project, name):
        self.project = project
        self.name = name

        # make the name nicer for filesystem and replace
        # all the special characters
        self.file_name = name.replace(" ", "_")
        self.storage = os.path.join(os.path.join(self.project,
                                              ".grape/jobs"), self.file_name)
        self._lock = None

    def set(self, id, job):
        """Add a submitted feature to the list of jobs
        """
        data = self.get()
        data[id] = job
        # save and release
        self.save(data)

    def get(self):
        import json
        if not os.path.exists(self.storage):
            return {"name": self.name}
        else:
            with open(self.storage) as f:
                return json.load(f)

    def save(self, data):
        import json
        with open(self.storage, "w") as f:
            return json.dump(data, f, indent=2)

    def lock(self):
        """Lock the store"""
        if self._lock is not None:
            return False

        from lockfile import LockFile

        base = os.path.dirname(self.storage)
        if not os.path.exists(base):
            os.makedirs(base)

        self._lock = LockFile(self.storage)
        try:
            self._lock.acquire()
            return True
        except Exception, e:
            raise StoreException("Locking storage file failed: %s" % str(e))

    def release(self):
        if self._lock is None:
            return False
        self._lock.release()
        self._lock = None
        return True


class _OnStartListener(object):
    def __init__(self, project, name):
        self.project = project
        self.name = name

    def __call__(self, tool, args):
        store = PipelineStore(self.project, self.name)
        try:
            store.lock()
            data = store.get()
            job_data = data[tool.name]
            job_data["state"] = grape.jobs.STATE_RUNNING
            data[tool.name] = job_data
            store.save(data)
        finally:
            store.release()


class _OnSuccessListener(object):
    def __init__(self, project, name):
        self.project = project
        self.name = name

    def __call__(self, tool, args):
        store = PipelineStore(self.project, self.name)
        try:
            store.lock()
            data = store.get()
            job_data = data[tool.name]
            job_data["state"] = grape.jobs.STATE_DONE
            data[tool.name] = job_data
            store.save(data)
        finally:
            store.release()


class _OnFailListener(object):
    def __init__(self, project, name):
        self.project = project
        self.name = name

    def __call__(self, tool, args):
        store = PipelineStore(self.project, self.name)
        try:
            store.lock()
            data = store.get()
            job_data = data[tool.name]
            job_data["state"] = grape.jobs.STATE_FAILED
            data[tool.name] = job_data
            store.save(data)
        finally:
            store.release()


def prepare_tool(tool, project, name):
    """Add listeners to the tool to ensure that it updates the job store
    during execution.

    :param tool: the tool instance
    :type tool: jip.tools.Tool
    :param project: the project
    :type project: grape.Project
    :param name: the run name used to identify the job store
    :type name: string
    """
    tool.on_start.append(_OnStartListener(project, name))
    tool.on_success.append(_OnSuccessListener(project, name))
    tool.on_fail.append(_OnFailListener(project, name))


def list(project):
    """Yield all active jobs stores for the given project"""
    jobs_dir = os.path.join(project, ".grape/jobs")
    for store_file in os.listdir(jobs_dir):
        yield PipelineStore(project, store_file)
