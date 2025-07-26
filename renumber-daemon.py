#!/usr/bin/env python3
import asyncio, json, sys

async def run(cmd):
    proc = await asyncio.create_subprocess_shell(cmd,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL)
    await proc.communicate()

async def capture(cmd):
    proc = await asyncio.create_subprocess_shell(cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL)
    out, _ = await proc.communicate()
    return out.decode()

async def renumber():
    wss = json.loads(await capture("hyprctl -j workspaces"))
    clients = json.loads(await capture("hyprctl -j clients"))

    # Group workspace IDs and client addresses per monitor
    monitors = {}
    for ws in wss:
        mon = ws["monitor"]
        monitors.setdefault(mon, {})[ws["id"]] = []

    for c in clients:
        mon = c["monitor"]
        wsid = c["workspace"]["id"]
        addr = c["address"]
        monitors.setdefault(mon, {}).setdefault(wsid, []).append(addr)

    for mon, id_map in monitors.items():
        sorted_ids = sorted(id_map.keys())
        target_id = sorted_ids[0] if sorted_ids else 1

        # Move windows down into sequential IDs
        for src_id in sorted_ids:
            if src_id != target_id and id_map[src_id]:
                # Find next empty lower workspace
                while target_id in id_map and id_map[target_id]:
                    target_id += 1
                if target_id < src_id:
                    for addr in id_map[src_id]:
                        await run(f"hyprctl dispatch movetoworkspacesilent {target_id},address:{addr}")
                    id_map[target_id] = id_map[src_id][:]
                    id_map[src_id] = []
            target_id += 1

    # After moves, rebuild workspace state
    wss = json.loads(await capture("hyprctl -j workspaces"))

    # Renaming per monitor
    per_monitor_ids = {}
    for ws in wss:
        mon = ws["monitor"]
        per_monitor_ids.setdefault(mon, []).append(ws["id"])

    for mon, ids in per_monitor_ids.items():
        for i, real_id in enumerate(sorted(ids), 1):
            await run(f"hyprctl dispatch renameworkspace {real_id} {i}")



async def watch():
    await renumber()
    p = await asyncio.create_subprocess_shell(
        "hyprctl events",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL
    )
    assert p.stdout
    while True:
        line = await p.stdout.readline()
        if not line:
            break
        if line.decode().startswith("workspace"):
            await renumber()

if __name__ == "__main__":
    try:
        asyncio.run(watch())
    except KeyboardInterrupt:
        sys.exit(0)
