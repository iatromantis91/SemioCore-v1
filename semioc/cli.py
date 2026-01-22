# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
import argparse
import json
import os
import sys

from pathlib import Path
from . import VERSION
from .sc_parser import parse_program_file
from .world import load_world
from .engine import run_program, make_manifest, write_json
from .replay import replay_from_manifest
from .ctxscan import ctxscan
from .parser import parse_program_to_ast
from .plasticity import compute_plasticity_report
from .contract_ids import LANG_SCHEMA_V1, AST_SCHEMA_V1
from .util import normalize_json

_ALLOWED_OPS = {"Add", "Sign", "JitterU"}


def _ensure_parent(path: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)


def _load_json_file(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json_file(path: str, payload: dict) -> None:
    _ensure_parent(path)
    Path(path).write_text(_dump_json(payload), encoding="utf-8")


def cmd_parse(args: argparse.Namespace) -> int:
    program_path = Path(args.program)

    # Lee fuente
    src = program_path.read_text(encoding="utf-8")

    # program_file estable y portable:
    # - si el archivo está bajo el cwd, usa ruta relativa POSIX
    # - si no, usa la ruta tal cual en POSIX
    try:
        program_file = program_path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except Exception:
        program_file = program_path.as_posix()
   
    lang_obj = _make_lang_manifest(program_file)
    ast_obj = parse_program_to_ast(src, program_file=program_file)

    if args.emit_lang:
        Path(args.emit_lang).write_text(_dump_json(lang_obj), encoding="utf-8")

    if args.emit_ast:
        Path(args.emit_ast).write_text(_dump_json(ast_obj), encoding="utf-8")
    else:
        sys.stdout.write(_dump_json(ast_obj))

    return 0

def _dump_json(payload: dict) -> str:
    # JSON determinista para diffs/golden tests y reproducibilidad
    payload = normalize_json(payload)
    return json.dumps(payload, sort_keys=True, ensure_ascii=False, indent=2) + "\n"

def _make_lang_manifest(program_file: str) -> dict:
    # Manifest v1: estable, extensible
    return {
        "schema": LANG_SCHEMA_V1,
        "program_file": program_file,
        "lang_version": "1",
        "features": [],
        "ast_schema": AST_SCHEMA_V1,
        # opcional: vacío por ahora; mantenemos el campo fuera si no se usa
        # "diagnostics": [],
    }

def _fail(msg: str) -> int:
    print(f"ERROR: {msg}", file=sys.stderr)
    return 2


def _rewrite_audit_alias(argv: list[str]) -> list[str]:
    """Accept the legacy form: `semioc audit --tool ...`.

    The v1.3 CLI models audit as a subcommand group. For usability and
    backwards-compatibility with the requested "literal" form, we transparently
    rewrite:

        semioc audit --tool ... --manifest ...

    into:

        semioc audit run --tool ... --manifest ...

    This keeps `semioc audit score-compare ...` intact.
    """

    if not argv:
        return argv
    if argv[0] != "audit":
        return argv

    # Explicit subcommands: do not rewrite.
    if len(argv) >= 2 and argv[1] in {"score-compare", "run"}:
        return argv

    # If the second token is an option, interpret it as the "run" form.
    if len(argv) >= 2 and argv[1].startswith("-"):
        return ["audit", "run", *argv[1:]]

    return argv

def check_strict(program_file: str) -> int:
    try:
        prog = parse_program_file(program_file)
    except Exception as e:
        return _fail(str(e))

    for op in prog.context.ops:
        if op.name not in _ALLOWED_OPS:
            return _fail(f"Unknown operator '{op.name}' in context. Allowed: {sorted(_ALLOWED_OPS)}")

        if op.name in ("Add", "JitterU") and op.arg is None:
            return _fail(f"Operator '{op.name}' requires a numeric argument, e.g. {op.name}(0.5)")

        if op.name == "Sign" and op.arg is not None:
            return _fail("Operator 'Sign' takes no argument; use 'Sign' not 'Sign(x)'")

    out_positions = [i for i, st in enumerate(prog.body) if st.kind == "out_summarize"]
    if len(out_positions) != 1:
        return _fail(f"Program must contain exactly one 'out := summarize;'. Found: {len(out_positions)}")
    if out_positions[0] != len(prog.body) - 1:
        return _fail("'out := summarize;' must be the last statement in the context block (Strict).")

    for st in prog.body:
        if st.kind == "tick" and (st.x is None or float(st.x) <= 0.0):
            return _fail("tick dt must be > 0")

    print(f"OK: {program_file}")
    return 0

def main(argv=None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    argv = _rewrite_audit_alias(list(argv))
    ap = argparse.ArgumentParser(prog="semioc", description=f"SemioCore reference toolchain (v{VERSION})")
    ap.add_argument("--version", action="store_true", help="Print version and exit")
    sub = ap.add_subparsers(dest="cmd", required=False)

    # check
    chk = sub.add_parser("check", help="Parse + Strict-lite checks")
    chk.add_argument("--strict", action="store_true", help="Enable Strict gate")
    chk.add_argument("program", help="Path to .sc program")

    # run
    runp = sub.add_parser("run", help="Execute a .sc program")
    runp.add_argument("program", help="Path to .sc program")
    runp.add_argument("--world", required=True, help="Path to world JSON (fixtures/world/...)")
    runp.add_argument("--emit-manifest", required=True, help="Output manifest JSON path")
    runp.add_argument("--emit-trace", required=True, help="Output trace JSON path")

    # replay
    rpl = sub.add_parser("replay", help="Replay deterministically from a manifest")
    rpl.add_argument("--manifest", required=True, help="Path to manifest JSON")
    rpl.add_argument("--emit-trace", required=True, help="Output trace JSON path")

    # ctxscan (NEW)
    cxs = sub.add_parser("ctxscan", help="Scan context permutations and report contextuality witness")
    cxs.add_argument("program", help="Path to .sc program")
    cxs.add_argument("--world", required=True, help="Path to world JSON")
    cxs.add_argument("--emit-report", required=True, help="Output ctxscan report JSON path")
    cxs.add_argument("--emit-dir", default=None, help="Optional directory to write per-permutation traces")
    cxs.add_argument("--max-perms", default=None, help="Optional cap on number of permutations")
    # parse (NEW)
    prs = sub.add_parser("parse", help="Parse a .sc program and emit a stable AST JSON")
    prs.add_argument("program", help="Path to the .sc program file")
    prs.add_argument("--emit-ast", dest="emit_ast", help="Write AST JSON to this file (default: stdout)")
    prs.add_argument("--emit-lang", dest="emit_lang", help="Write language manifest JSON to this file (default: no manifest)")


    # plasticity (NEW)
    plc = sub.add_parser("plasticity", help="Compute a semiodynamic plasticity report from trace files")
    plc.add_argument("--traces", nargs="+", required=True, help="One or more trace JSON files (semiocore.trace.v1)")
    plc.add_argument("--ctx", required=True, help="Context ID to analyze (must match trace.events[].ctx)")
    plc.add_argument("--channel", required=True, help="Channel to analyze (must match trace.events[].ch)")
    plc.add_argument("--protocol", default="Strict", help="Protocol label for the report (default: Strict)")
    plc.add_argument("--window-size", type=int, default=10, help="Event window size for stability metrics")
    plc.add_argument("--window-step", type=int, default=10, help="Event window step for stability metrics")
    plc.add_argument("--program-file", default="programs/conformance/plasticity.sc", help="Optional program file path to embed in the report")
    plc.add_argument("--emit-report", required=True, help="Output plasticity report JSON path")

    # contracts
    cts = sub.add_parser("contracts", help="Contracts: registry validation utilities")
    cts_sub = cts.add_subparsers(dest="contracts_cmd", required=True)
    cval = cts_sub.add_parser("validate", help="Validate contracts registry + referenced schemas/docs/fixtures")

    # biomed (Level C)
    biomed = sub.add_parser("biomed", help="Biomedical I/O + deterministic recipes + Level C comparators")
    bsub = biomed.add_subparsers(dest="biomed_cmd", required=True)

    brcp = bsub.add_parser("recipes", help="List available biomedical recipes")
    brcp.add_argument("--emit-index", default=None, help="Optional recipes index JSON path")
    brcp.add_argument("--realtime", action="store_true", help="Use real timestamps (default: fixed epoch)")

    bscore = bsub.add_parser("score", help="Compute a score artifact for a given recipe")
    bscore.add_argument("--recipe", required=True, help="Recipe id (e.g. inflammation_score_v1)")
    bscore.add_argument("--input", required=True, help="Input payload JSON path (labs_panel or wearable_timeseries)")
    bscore.add_argument("--emit-score", required=True, help="Output score artifact JSON path")
    bscore.add_argument("--repo-root", default=None, help="Optional repo root (defaults to auto-detected)")
    bscore.add_argument("--realtime", action="store_true", help="Use real timestamps (default: fixed epoch)")

    bcmp = bsub.add_parser("compare", help="Comparator v2: compute recovery report from score artifacts")
    bcmp.add_argument("--baseline-label", default="t0", help="Baseline label (default: t0)")
    bcmp.add_argument("--baseline-score", required=True, help="Baseline score artifact JSON path")
    bcmp.add_argument(
        "--post",
        action="append",
        default=[],
        help="Post score artifact as LABEL=PATH (repeatable)",
    )
    bcmp.add_argument("--emit-report", required=True, help="Output recovery report JSON path")
    bcmp.add_argument("--realtime", action="store_true", help="Use real timestamps (default: fixed epoch)")

    bpl = bsub.add_parser("plasticity2", help="Compute plasticity2 report from a recovery report")
    bpl.add_argument("--recovery-report", required=True, help="Input recovery report JSON path")
    bpl.add_argument("--emit-report", required=True, help="Output plasticity2 report JSON path")
    bpl.add_argument("--realtime", action="store_true", help="Use real timestamps (default: fixed epoch)")

    # audit
    audit = sub.add_parser("audit", help="Audit comparators for biomedical artifacts")
    asub = audit.add_subparsers(dest="audit_cmd", required=True)
    asc = asub.add_parser("score-compare", help="Compare two score artifacts under a tolerance")
    asc.add_argument("--baseline", required=True, help="Baseline score artifact JSON path")
    asc.add_argument("--candidate", required=True, help="Candidate score artifact JSON path")
    asc.add_argument("--tolerance-abs", type=float, default=0.01, help="Absolute tolerance (default: 0.01)")
    asc.add_argument("--emit-report", required=True, help="Output audit report JSON path")
    asc.add_argument("--realtime", action="store_true", help="Use real timestamps (default: fixed epoch)")

    arun = asub.add_parser("run", help="Audit an external tool against SemioCore oracles")
    arun.add_argument("--tool", required=True, help="Tool name (for report metadata)")
    arun.add_argument("--manifest", required=True, help="Intervention manifest JSON path")
    arun.add_argument(
        "--contracts",
        default="biomed_v1",
        help="Contract suite name (default: biomed_v1)",
    )
    arun.add_argument("--tolerance-abs", type=float, default=0.0, help="Absolute tolerance (default: 0.0)")
    arun.add_argument("--emit-report", required=True, help="Output tool audit report JSON path")
    arun.add_argument("--repo-root", default=None, help="Optional repo root (defaults to auto-detected)")
    arun.add_argument("--realtime", action="store_true", help="Use real timestamps (default: fixed epoch)")

    args = ap.parse_args(argv)

    if args.version:
        print(VERSION)
        return 0

    if args.cmd is None:
        ap.print_help()
        return 2

    if args.cmd == "parse":
        try:
            return cmd_parse(args)
        except Exception as e:
            return _fail(str(e))

    if args.cmd == "check":
        if args.strict:
            return check_strict(args.program)
        try:
            parse_program_file(args.program)
            print(f"OK: {args.program}")
            return 0
        except Exception as e:
            return _fail(str(e))

    if args.cmd == "replay":
        try:
            replay_from_manifest(args.manifest, args.emit_trace)
            print(f"OK: {args.emit_trace}")
            return 0
        except Exception as e:
            return _fail(str(e))

    if args.cmd == "ctxscan":
        try:
            maxp = int(args.max_perms) if args.max_perms is not None else None
            ctxscan(args.program, args.world, args.emit_report, emit_dir=args.emit_dir, max_perms=maxp)
            print(f"OK: {args.emit_report}")
            return 0
        except Exception as e:
            return _fail(str(e))


    if args.cmd == "plasticity":
        try:
            trace_paths = [Path(p) for p in args.traces]
            report = compute_plasticity_report(
                trace_paths,
                ctx=args.ctx,
                channel=args.channel,
                protocol=args.protocol,
                window_size=int(args.window_size),
                window_step=int(args.window_step),
                program_file=args.program_file,
            )
            os.makedirs(os.path.dirname(args.emit_report) or ".", exist_ok=True)
            Path(args.emit_report).write_text(_dump_json(report), encoding="utf-8")
            print(f"OK: {args.emit_report}")
            return 0
        except Exception as e:
            return _fail(str(e))


    if args.cmd == "contracts":
        if args.contracts_cmd == "validate":
            from .contracts.registry import validate_registry
            ok, errors = validate_registry(Path.cwd())
            if ok:
                print("OK: contracts registry validated")
                return 0
            print("ERROR: contracts registry validation failed")
            for e in errors:
                print(f"- {e}")
            return 1
        print(f"semioc: unknown contracts subcommand: {args.contracts_cmd}")
        return 2

    if args.cmd == "biomed":
        try:
            from .biomed import pipeline as biomed_pipeline
            from .biomed import levelc as biomed_levelc

            if args.biomed_cmd == "recipes":
                from .recipes.registry import recipe_index

                index = recipe_index(tool_version=VERSION, use_realtime=bool(args.realtime))
                if args.emit_index:
                    _write_json_file(args.emit_index, index)
                    print(f"OK: {args.emit_index}")
                else:
                    sys.stdout.write(_dump_json(index))
                return 0

            if args.biomed_cmd == "score":
                biomed_pipeline.score(
                    recipe_id=str(args.recipe),
                    input_path=str(args.input),
                    output_path=str(args.emit_score),
                    repo_root=args.repo_root,
                    use_realtime=bool(args.realtime),
                )
                print(f"OK: {args.emit_score}")
                return 0

            if args.biomed_cmd == "compare":
                baseline = _load_json_file(args.baseline_score)
                posts = []
                for spec in args.post:
                    if "=" not in spec:
                        raise ValueError("--post must be LABEL=PATH")
                    label, path = spec.split("=", 1)
                    posts.append((label, _load_json_file(path)))

                report = biomed_levelc.compare_v2(
                    tool_version=VERSION,
                    baseline_label=str(args.baseline_label),
                    baseline_score=baseline,
                    posts=posts,
                    use_realtime=bool(args.realtime),
                )
                _write_json_file(args.emit_report, report)
                print(f"OK: {args.emit_report}")
                return 0

            if args.biomed_cmd == "plasticity2":
                recovery = _load_json_file(args.recovery_report)
                report = biomed_levelc.plasticity_v2(
                    tool_version=VERSION,
                    recovery_report=recovery,
                    use_realtime=bool(args.realtime),
                )
                _write_json_file(args.emit_report, report)
                print(f"OK: {args.emit_report}")
                return 0

            raise ValueError(f"Unknown biomed subcommand: {args.biomed_cmd}")
        except Exception as e:
            return _fail(str(e))

    if args.cmd == "audit":
        try:
            from .audit.score_compare import score_compare
            from .audit.tool_audit import run_tool_audit

            if args.audit_cmd == "score-compare":
                baseline = _load_json_file(args.baseline)
                candidate = _load_json_file(args.candidate)
                report = score_compare(
                    tool_version=VERSION,
                    baseline=baseline,
                    candidate=candidate,
                    tolerance_abs=float(args.tolerance_abs),
                    use_realtime=bool(args.realtime),
                )
                _write_json_file(args.emit_report, report)
                print(f"OK: {args.emit_report}")
                return 0

            if args.audit_cmd == "run":
                repo_root = Path(args.repo_root).resolve() if args.repo_root else None
                run_tool_audit(
                    tool_name=str(args.tool),
                    manifest_path=Path(args.manifest),
                    contracts=str(args.contracts),
                    tolerance_abs=float(args.tolerance_abs),
                    emit_report=Path(args.emit_report),
                    repo_root=repo_root,
                    use_realtime=bool(args.realtime),
                )
                print(f"OK: {args.emit_report}")
                return 0

            raise ValueError(f"Unknown audit subcommand: {args.audit_cmd}")
        except Exception as e:
            return _fail(str(e))

    if args.cmd != "run":
        print(f"semioc: '{args.cmd}' not implemented yet (v1).")
        return 2

    program_file = args.program
    world_file = args.world

    prog = parse_program_file(program_file)
    world = load_world(world_file)

    trace = run_program(prog, world.channels, program_file=program_file)
    manifest = make_manifest(program_file=program_file, world_file=world_file, seed=prog.seed)

    os.makedirs(os.path.dirname(args.emit_manifest) or ".", exist_ok=True)
    os.makedirs(os.path.dirname(args.emit_trace) or ".", exist_ok=True)

    write_json(args.emit_manifest, manifest)
    write_json(args.emit_trace, trace)
    return 0
