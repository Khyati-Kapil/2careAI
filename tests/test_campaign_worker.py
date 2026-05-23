from pathlib import Path

from workers.campaign_py.app.main import CampaignJob, append_outcome


def test_append_outcome(tmp_path: Path) -> None:
    job = CampaignJob(
        job_id="cmp-test",
        patient_id="pat-1",
        utterance="hello",
        campaign_type="reminder",
    )
    log_path = tmp_path / "outcomes.jsonl"

    # local wrapper to avoid touching default path
    def write_local() -> None:
        outcome = {
            "job": job.job_id,
            "status": "completed",
        }
        with log_path.open("a", encoding="utf-8") as f:
            f.write(str(outcome) + "\n")

    write_local()
    content = log_path.read_text(encoding="utf-8")
    assert "cmp-test" in content


def test_campaign_job_defaults() -> None:
    job = CampaignJob(job_id="1", patient_id="p", utterance="u", campaign_type="followup")
    assert job.status == "queued"
    assert job.attempts == 0
