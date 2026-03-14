import argparse
import json
import mimetypes
import threading
import uuid
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from pfc_tool import bruteforce_search_pfc_inductors, build_catalog, evaluate_candidate_details, evaluate_pfc_inductor, search_pfc_inductors


ROOT = Path(__file__).resolve().parent
WEB_ROOT = ROOT / "web"
ARTIFACT_ROOT = ROOT / "gorsellestirme"
CATALOG = build_catalog()
JOBS = {}
JOBS_LOCK = threading.Lock()


class PfcAppHandler(BaseHTTPRequestHandler):
    server_version = "PFCInductorDesigner/0.3"

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/catalog":
            return self._send_json(CATALOG)
        if parsed.path == "/health":
            return self._send_json({"status": "ok"})
        if parsed.path == "/api/visualize":
            return self._handle_visualize(parsed)
        if parsed.path == "/api/search/status":
            return self._handle_search_status(parsed)
        if parsed.path.startswith("/artifacts/"):
            return self._serve_artifact(parsed.path)
        return self._serve_static(parsed.path)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path not in {"/api/design", "/api/search", "/api/search/start", "/api/candidate-detail"}:
            return self.send_error(HTTPStatus.NOT_FOUND, "Unknown endpoint")

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(content_length)
            payload = json.loads(raw.decode("utf-8"))
            if parsed.path == "/api/design":
                result = evaluate_pfc_inductor(payload)
                return self._send_json(result)
            if parsed.path == "/api/search":
                result = search_pfc_inductors(payload)
                return self._send_json(result)
            if parsed.path == "/api/candidate-detail":
                result = evaluate_candidate_details(payload)
                return self._send_json(result)
            return self._start_search_job(payload)
        except ValueError as exc:
            return self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as exc:
            return self._send_json({"error": f"Unexpected server error: {exc}"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def log_message(self, format, *args):
        return

    def _start_search_job(self, payload):
        job_id = uuid.uuid4().hex
        with JOBS_LOCK:
            JOBS[job_id] = {
                "status": "queued",
                "progress_pct": 0.0,
                "current_core": "",
                "processed_cores": 0,
                "total_cores": 0,
                "valid_found": 0,
                "result": None,
                "error": None,
            }

        def progress_callback(done, total, core_name, core_valid_count):
            with JOBS_LOCK:
                if job_id not in JOBS:
                    return
                JOBS[job_id]["status"] = "running"
                JOBS[job_id]["progress_pct"] = 100.0 * done / max(total, 1)
                JOBS[job_id]["current_core"] = core_name
                JOBS[job_id]["processed_cores"] = done
                JOBS[job_id]["total_cores"] = total
                JOBS[job_id]["valid_found"] += core_valid_count

        def worker():
            try:
                result = bruteforce_search_pfc_inductors(payload, progress_callback=progress_callback)
                with JOBS_LOCK:
                    JOBS[job_id]["status"] = "completed"
                    JOBS[job_id]["progress_pct"] = 100.0
                    JOBS[job_id]["result"] = result
            except Exception as exc:
                with JOBS_LOCK:
                    JOBS[job_id]["status"] = "failed"
                    JOBS[job_id]["error"] = str(exc)

        threading.Thread(target=worker, daemon=True).start()
        return self._send_json({"job_id": job_id, "status": "queued"})

    def _handle_search_status(self, parsed):
        params = parse_qs(parsed.query)
        job_id = params.get("id", [""])[0]
        with JOBS_LOCK:
            job = JOBS.get(job_id)
        if not job:
            return self._send_json({"error": "Job not found"}, status=HTTPStatus.NOT_FOUND)
        return self._send_json(job)

    def _handle_visualize(self, parsed):
        try:
            from pfc_tool.visuals import build_candidate_visuals
            params = parse_qs(parsed.query)
            core_id = params.get("core_id", [""])[0]
            wire_id = params.get("wire_id", [""])[0]
            turns = int(params.get("turns", ["0"])[0])
            result = build_candidate_visuals(core_id, wire_id, turns)
        except ValueError as exc:
            return self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as exc:
            return self._send_json({"error": f"Visualization failed: {exc}"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
        return self._send_json(result)

    def _send_json(self, payload, status=HTTPStatus.OK):
        body = json.dumps(payload, ensure_ascii=True, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_artifact(self, path: str):
        file_path = (ARTIFACT_ROOT / path.replace("/artifacts/", "")).resolve()
        if ARTIFACT_ROOT.resolve() not in file_path.parents:
            return self.send_error(HTTPStatus.FORBIDDEN, "Forbidden")
        if not file_path.exists() or not file_path.is_file():
            return self.send_error(HTTPStatus.NOT_FOUND, "Artifact not found")
        return self._send_file(file_path)

    def _serve_static(self, path: str):
        target = "index.html" if path in ("", "/") else path.lstrip("/")
        file_path = (WEB_ROOT / target).resolve()
        if WEB_ROOT.resolve() not in file_path.parents and file_path != (WEB_ROOT / "index.html").resolve():
            return self.send_error(HTTPStatus.FORBIDDEN, "Forbidden")
        if not file_path.exists() or not file_path.is_file():
            return self.send_error(HTTPStatus.NOT_FOUND, "File not found")
        return self._send_file(file_path)

    def _send_file(self, file_path: Path):
        content_type, _ = mimetypes.guess_type(str(file_path))
        content_type = content_type or "application/octet-stream"
        data = file_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        if content_type.startswith("text/") or content_type in {"application/javascript", "application/json"}:
            content_type = f"{content_type}; charset=utf-8"
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main():
    parser = argparse.ArgumentParser(description="PFC inductor designer web app")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8010)
    args = parser.parse_args()

    with ThreadingHTTPServer((args.host, args.port), PfcAppHandler) as server:
        print(f"PFC inductor designer running at http://{args.host}:{args.port}")
        server.serve_forever()


if __name__ == "__main__":
    main()
