from datetime import datetime
from django.core.urlresolvers import reverse
from django.test import Client, TestCase
import drmaa
import json
from runner.models import Command, Job, Pipeline, InputKey
from runner.monitors import SlurmMonitor, decodestatus


class SlurmMonitorTestCase(TestCase):
    def setUp(self):
        self.monitor = SlurmMonitor()
    def test_get_job_reference(self):
        value = self.monitor.get_job_reference(self.SAMPLE_OUTPUT)
        self.assertEqual('663816', value)


    SAMPLE_OUTPUT = """
                    sourcing perl-5.16.2
                    sourcing casava-1.8.2
                    sourcing bcl2fastq-1.8.4
                    sourcing fastqc-0.11.4
                    sourcing texlive-1.2.2013
                    sourcing ImageMagick-6.8.4
                    exporting these variables 
                    TGACTOOLS_RUN_DIR=/tgac/pnp/qc
                    TGACTOOLS_SEQUENCER_DIR=/tgac/pnp/raw
                    TGACTOOLS_CONFIG_DIR=/tgac/software/production/tgac_tools/0.3/x86_64/config
                    TGACTOOLS_RUN_SUFFIX=
                    REFERENCES=/tgac/references/databases/kontaminants/
                    PAP dir : /tgac/pnp/qc/160411_SN790_0064_AHJMMJBCXX
                    Creating Directory: /tgac/pnp/qc/160411_SN790_0064_AHJMMJBCXX/test_new_miso/Scripts
                    getting base-mask
                    obtained base mask: y51,i6n1
                    Basecall directory /tgac/pnp/raw/HiSeq-2/160411_SN790_0064_AHJMMJBCXX/Data/Intensities/BaseCalls
                    running configureBclToFastq now
                    /tgac/software/production/bcl2fastq/1.8.4/x86_64/bin/configureBclToFastq.pl --input-dir /tgac/pnp/raw/HiSeq-2/160411_SN790_0064_AHJMMJBCXX/Data/Intensities/BaseCalls --output-dir test_new_miso --mismatches 1 --use-bases-mask y51,i6n1 --sample-sheet SampleSheet-PAP.csv --force
                    Submitted batch job 663816
    """

class MisoAPITestCase(TestCase):
    def setUp(self):
        self.client = Client()

        ik1 = InputKey(name='{feeb}')
        ik2 = InputKey(name='{ one }')
        ik3 = InputKey(name='{ boiled }')
        ik4 = InputKey(name='{ egg }')

        ik1.save()
        ik2.save()
        ik3.save()
        ik4.save()

        self.test_command_1 = Command(pk=1, name="test name", description="test description")
        self.test_command_2 = Command(pk=2, name="test name 2", description="test description 2")
        self.test_command_1.save()
        self.test_command_2.save()

        self.test_command_1.input_keys.add(ik1)
        self.test_command_1.input_keys.add(ik2)
        self.test_command_1.input_keys.add(ik3)

        self.test_pipeline_1 = Pipeline(pk=1, name="test_name3", description="test description 3")
        self.test_pipeline_1.save()
        self.test_pipeline_1.commands.add(self.test_command_1)
        self.test_pipeline_1.commands.add(self.test_command_2)
        
        self.test_pipeline_2 = Pipeline(pk=2, name="test_name4", description="test description 4")
        self.test_pipeline_2.save()

        self.test_job_0 = Job(name="tjn_0", description="tjd_0", pipeline=self.test_pipeline_2, scheduler_state=decodestatus[drmaa.JobState.FAILED])
        self.test_job_1 = Job(name="tjn_1", description="tjd_1", pipeline=self.test_pipeline_1, scheduler_state=decodestatus[drmaa.JobState.UNDETERMINED])
        self.test_job_2 = Job(name="tjn_2", description="tjd_2", pipeline=self.test_pipeline_2, scheduler_state=decodestatus[drmaa.JobState.QUEUED_ACTIVE])
        self.test_job_3 = Job(name="tjn_3", description="tjd_3", pipeline=self.test_pipeline_2, scheduler_state=decodestatus[drmaa.JobState.SYSTEM_ON_HOLD])
        self.test_job_4 = Job(name="tjn_4", description="tjd_4", pipeline=self.test_pipeline_1, scheduler_state=decodestatus[drmaa.JobState.USER_ON_HOLD])
        self.test_job_5 = Job(name="tjn_5", description="tjd_5", pipeline=self.test_pipeline_2, scheduler_state=decodestatus[drmaa.JobState.USER_SYSTEM_ON_HOLD])
        self.test_job_6 = Job(name="tjn_6", description="tjd_6", pipeline=self.test_pipeline_2, scheduler_state=decodestatus[drmaa.JobState.RUNNING])
        self.test_job_7 = Job(name="tjn_7", description="tjd_7", pipeline=self.test_pipeline_1, scheduler_state=decodestatus[drmaa.JobState.SYSTEM_SUSPENDED])
        self.test_job_8 = Job(name="tjn_8", description="tjd_8", pipeline=self.test_pipeline_2, scheduler_state=decodestatus[drmaa.JobState.USER_SUSPENDED])
        self.test_job_9 = Job(name="tjn_9", description="tjd_9", pipeline=self.test_pipeline_2, scheduler_state=decodestatus[drmaa.JobState.DONE])

        self.test_job_0.save()
        self.test_job_1.save()
        self.test_job_2.save()
        self.test_job_3.save()
        self.test_job_4.save()
        self.test_job_5.save()
        self.test_job_6.save()
        self.test_job_7.save()
        self.test_job_8.save()
        self.test_job_9.save()

# miso API specific tests
    def test_get_completed_jobs(self):
        query = "getCompletedTasks"
        url = reverse("miso")
        response = self.client.post(
            url,
            json.dumps({"query": query}),
            content_type="application/json").json()

        self.assertEqual(1, len(response))

    def test_get_failed_jobs(self):
        query = "getFailedTasks"
        url = reverse("miso")
        response = self.client.post(
            url, 
            json.dumps({"query": query}),
            content_type="application/json").json()

        self.assertEqual(1, len(response))

    def test_get_pending_jobs(self):
        query = "getPendingTasks"
        url = reverse("miso")
        response = self.client.post(
            url, 
            json.dumps({"query": query}),
            content_type="application/json").json()

        self.assertEqual(5, len(response))

    def test_get_jobs(self):
        pass


    def test_get_job(self):
        pass

    def test_get_pipeline(self):
        query = "getPipeline"
        params = { "name": self.test_pipeline_1.name }
        data = { "query": query, "params": params } 
        url = reverse("miso")
        response = self.client.post(url, 
            json.dumps(data),
            content_type="application/json").json()

        self.assertEqual(self.test_pipeline_1.name, response.get('name'))

    def test_get_pipelines(self):
        query = "getPipelines"
        url = reverse("miso")
        response = self.client.post(
            url,
            json.dumps({"query": query}),
            content_type="application/json"
            ).json()

        self.assertEqual(2, len(response))

    def test_submit_job(self):
        pipeline = self.test_pipeline_1.name
        params = { "run": False }
        url = reverse("miso")

        response = self.client.post(url, 
            json.dumps({ "submitTask": {"pipeline": pipeline, "params": params }}),
            content_type="application/json"
            ).json()

        self.assertEqual(2, len(response))
        self.assertTrue('id' in response)
        self.assertTrue(response.get('success'))
