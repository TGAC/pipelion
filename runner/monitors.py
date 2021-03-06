import re
import drmaa
import thread
import time
import threading

decodestatus = {drmaa.JobState.UNDETERMINED: 'process status cannot be determined',
                drmaa.JobState.QUEUED_ACTIVE: 'job is queued and active',
                drmaa.JobState.SYSTEM_ON_HOLD: 'job is queued and in system hold',
                drmaa.JobState.USER_ON_HOLD: 'job is queued and in user hold',
                drmaa.JobState.USER_SYSTEM_ON_HOLD: 'job is queued and in user and system hold',
                drmaa.JobState.RUNNING: 'job is running',
                drmaa.JobState.SYSTEM_SUSPENDED: 'job is system suspended',
                drmaa.JobState.USER_SUSPENDED: 'job is user suspended',
                drmaa.JobState.DONE: 'job finished normally',
                drmaa.JobState.FAILED: 'job finished, but failed'}


class SlurmMonitor():
    POLL_DELAY = 10  # Seconds
    lock = threading.RLock()
    def monitor(self, job, std_out):
        def start_polling(ref, job):
            complete = False
            status = ""
            while not complete:
                status = self.get_job_status(ref)
                job.scheduler_state = status
                job.save()
                time.sleep(self.POLL_DELAY)
                complete = self.is_job_complete(status)
            if status is decodestatus.get(drmaa.JobState.FAILED):
                return False
            elif status is decodestatus.get(drmaa.JobState.DONE):
                return True
            else:
                raise Exception("Invalid Job State! {}".format(status))
        ref = self.get_job_reference(std_out)
        if ref:
            return start_polling(ref, job)


    def get_job_reference(self, input):
        job_ref = self._get_value_by_key(input, 'Submitted batch job ' , '[0-9]+')
        return job_ref

    def get_job_status(self, reference):
        with self.lock:
            with drmaa.Session() as s:
                return decodestatus.get(s.jobStatus(reference))

    def is_job_complete(self, status):
        if status in [decodestatus[drmaa.JobState.DONE], decodestatus[drmaa.JobState.FAILED]]:
            return True
        else: 
            return False

    def _get_value_by_key(self, input, key, regex):
        # pattern = re.compile(key + regex)
        arr = input.splitlines()

        for str in arr:
            result = re.search(key + regex, str)
            if result:
                return str.strip()[len(key):]
        return None

monitors = { 1: SlurmMonitor }
