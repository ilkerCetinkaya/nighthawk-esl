import asyncio
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
os.environ["KPROFILE"] = "builder"
os.environ["KMODE"] = "experimental"
TEST = sys.argv[1]
os.environ["KPROJ"] = f"{HERE}/sandbox/test{TEST.upper()}"
from mcp_client import Session
from fr_client import FR

D = os.environ["KPROJ"]
DSN = f"{D}/output/routing/subset.dsn"
RES = f"{HERE}/results"


def show(tag, obj, n=700):
    text = obj if isinstance(obj, str) else json.dumps(obj, default=str)
    print(f"[{tag}] {text[:n]}", flush=True)
    return obj


async def kcall(k, tool, args, tries=8):
    for attempt in range(tries):
        r = await k.call(tool, args)
        if "registration has not finished" not in str(r):
            return r
        print(f"[kicad registration pending, retry {attempt}]", flush=True)
        await asyncio.sleep(30)
    return r


async def export_dsn():
    async with Session("kicad") as k:
        show("kicad route_export_dsn", await kcall(k, "route_export_dsn", {"output_path": "output/routing/subset.dsn"}), 300)


def test_a():
    out = {}
    fr = FR()
    try:
        show("fr status", fr.call("get_system_status"))
        t0 = time.time()
        try:
            one = fr.call("autoroute_board", {"body": {"filePath": DSN, "outputFormats": ["SES", "DRC_SUMMARY"], "timeoutSeconds": 300, "routerSettings": {"autorouter": {"maxPasses": 20}, "optimizer": {"enabled": False}}}}, timeout=420)
        except TimeoutError:
            one = "TIMEOUT 420s"
        out["single_turn_seconds"] = round(time.time() - t0, 1)
        show("fr autoroute_board", one, 1500)
        sess = fr.call("create_session")
        sid = sess["body"]["id"]
        job = fr.call("enqueue_job", {"body": {"session_id": sid, "name": "subset", "priority": "NORMAL"}})
        jid = job["body"]["id"]
        show("upload", fr.call("upload_job_input_from_local_file", {"jobId": jid, "filePath": DSN}), 300)
        show("settings", fr.call("update_job_settings", {"path": {"jobId": jid}, "body": {"autorouter": {"maxPasses": 20}, "optimizer": {"enabled": False}}}), 300)
        t0 = time.time()
        show("start", fr.call("start_job", {"path": {"jobId": jid}}), 300)
        b = {}
        for i in range(180):
            time.sleep(5)
            dd = fr.call("get_job_details", {"path": {"jobId": jid}, "query": {"compact": True}})
            b = dd.get("body", dd) if isinstance(dd, dict) else {}
            st = b.get("state") if isinstance(b, dict) else None
            print("poll", i, st, b.get("stage") if isinstance(b, dict) else "", flush=True)
            if st in ("COMPLETED", "CANCELLED", "TERMINATED", "FAILED"):
                break
        out["multi_turn_seconds"] = round(time.time() - t0, 1)
        show("job", b, 1200)
        show("drc summary", fr.call("get_job_drc_summary", {"path": {"jobId": jid}}), 1200)
        ses = f"{D}/output/routing/subset_fr_mcp.ses"
        show("download", fr.call("download_job_output_to_local_file", {"jobId": jid, "filePath": ses}), 300)
        out["ses_exists"] = os.path.exists(ses)
    finally:
        fr.close()
    json.dump(out, open(f"{RES}/test{TEST.upper()}_raw.json", "w"), indent=1, default=str)


async def test_b():
    async with Session("kicad") as k:
        t0 = time.time()
        r = await kcall(k, "route_autoroute_freerouting", {"dsn_path": "output/routing/subset.dsn", "ses_path": "output/routing/subset_kmp.ses", "use_docker": False, "freerouting_jar_path": f"{HERE}/freerouting-2.5.0.jar", "max_passes": 20, "thread_count": 4}, tries=14)
        show("kicad route_autoroute_freerouting", r, 2500)
        print("seconds", round(time.time() - t0, 1))


if __name__ == "__main__":
    step = sys.argv[2]
    if step == "export":
        asyncio.run(export_dsn())
    elif step == "route" and TEST == "a":
        test_a()
    elif step == "route" and TEST == "b":
        asyncio.run(test_b())
