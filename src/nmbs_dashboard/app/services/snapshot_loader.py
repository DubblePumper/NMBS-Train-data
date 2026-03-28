"""Snapshot repository loading and endpoint browsing utilities."""

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def _parse_snapshot_datetime(snapshot_id: str, exported_at: Optional[str]) -> datetime:
    if exported_at:
        try:
            return datetime.fromisoformat(exported_at.replace("Z", "+00:00"))
        except ValueError:
            pass

    for fmt in ("%Y%m%d-%H%M%S", "%Y%m%d_%H%M%S"):
        try:
            return datetime.strptime(snapshot_id, fmt)
        except ValueError:
            continue

    return datetime.min


def _read_json(file_path: Path) -> Any:
    try:
        with file_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        return {"_error": f"Missing file: {file_path}"}
    except json.JSONDecodeError as exc:
        return {"_error": f"Invalid JSON in {file_path.name}: {exc}"}


def unwrap_endpoint_body(payload: Any) -> Any:
    if isinstance(payload, dict) and "body" in payload:
        return payload.get("body")
    return payload


def load_snapshot_repository(snapshot_root: Path | str) -> Dict[str, Any]:
    root = Path(snapshot_root)
    snapshots: List[Dict[str, Any]] = []

    if not root.exists():
        return {
            "root": str(root),
            "snapshot_count": 0,
            "snapshots": [],
            "latest_snapshot_id": None,
            "endpoint_names": [],
            "errors": [f"Snapshot root does not exist: {root}"],
        }

    for snapshot_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        manifest_path = snapshot_dir / "manifest.json"
        manifest = _read_json(manifest_path) if manifest_path.exists() else {}

        exported_at = manifest.get("exported_at") if isinstance(manifest, dict) else None
        snapshot_dt = _parse_snapshot_datetime(snapshot_dir.name, exported_at)

        endpoints: Dict[str, Dict[str, Any]] = {}
        files_meta = manifest.get("files", []) if isinstance(manifest, dict) else []

        if isinstance(files_meta, list) and files_meta:
            for item in files_meta:
                if not isinstance(item, dict):
                    continue
                endpoint_name = str(item.get("name") or Path(str(item.get("path", ""))).stem)
                rel_path = str(item.get("path") or f"{endpoint_name}.json")
                endpoint_path = snapshot_dir / rel_path
                endpoints[endpoint_name] = {
                    "name": endpoint_name,
                    "path": str(endpoint_path),
                    "meta": item,
                    "payload": _read_json(endpoint_path),
                }
        else:
            for endpoint_path in sorted(snapshot_dir.glob("*.json")):
                endpoint_name = endpoint_path.stem
                endpoints[endpoint_name] = {
                    "name": endpoint_name,
                    "path": str(endpoint_path),
                    "meta": {},
                    "payload": _read_json(endpoint_path),
                }

        snapshots.append(
            {
                "id": snapshot_dir.name,
                "path": str(snapshot_dir),
                "exported_at": exported_at,
                "exported_at_dt": snapshot_dt,
                "manifest": manifest,
                "endpoint_count": len(endpoints),
                "endpoints": endpoints,
            }
        )

    snapshots.sort(key=lambda item: item["exported_at_dt"])
    latest = snapshots[-1] if snapshots else None

    return {
        "root": str(root),
        "snapshot_count": len(snapshots),
        "snapshots": snapshots,
        "latest_snapshot_id": latest["id"] if latest else None,
        "endpoint_names": sorted(latest["endpoints"].keys()) if latest else [],
        "errors": [],
    }


def get_snapshot(repository: Dict[str, Any], snapshot_id: Optional[str]) -> Optional[Dict[str, Any]]:
    if not snapshot_id:
        return None
    for snapshot in repository.get("snapshots", []):
        if snapshot.get("id") == snapshot_id:
            return snapshot
    return None


def get_endpoint_payload(repository: Dict[str, Any], snapshot_id: Optional[str], endpoint_name: Optional[str]) -> Any:
    if not snapshot_id or not endpoint_name:
        return None

    snapshot = get_snapshot(repository, snapshot_id)
    if not snapshot:
        return None

    endpoint = snapshot.get("endpoints", {}).get(endpoint_name)
    if not endpoint:
        return None

    return endpoint.get("payload")


def snapshot_options(repository: Dict[str, Any]) -> List[Dict[str, str]]:
    return [
        {"label": str(item.get("exported_at") or item.get("id")), "value": str(item.get("id"))}
        for item in repository.get("snapshots", [])
    ]


def endpoint_options(repository: Dict[str, Any], snapshot_id: Optional[str]) -> List[Dict[str, str]]:
    snapshot = get_snapshot(repository, snapshot_id)
    if not snapshot:
        return []

    return [{"label": name, "value": name} for name in sorted(snapshot.get("endpoints", {}).keys())]


def endpoint_status_rows(repository: Dict[str, Any], snapshot_id: Optional[str]) -> List[Dict[str, Any]]:
    snapshot = get_snapshot(repository, snapshot_id)
    if not snapshot:
        return []

    rows: List[Dict[str, Any]] = []
    for endpoint_name, endpoint in sorted(snapshot.get("endpoints", {}).items()):
        meta = endpoint.get("meta", {})
        rows.append(
            {
                "endpoint": endpoint_name,
                "status": meta.get("status"),
                "ok": meta.get("ok"),
                "is_json": meta.get("is_json"),
                "file": Path(endpoint.get("path", "")).name,
            }
        )

    return rows


def render_json_preview(payload: Any, max_chars: int = 120_000) -> str:
    try:
        serialized = json.dumps(payload, indent=2, ensure_ascii=False)
    except TypeError:
        serialized = str(payload)

    if len(serialized) <= max_chars:
        return serialized

    omitted = len(serialized) - max_chars
    return f"{serialized[:max_chars]}\n\n... [truncated {omitted} characters]"
