from typing import List, Tuple
import re

from ..schemas.analysis import Finding, Summary


SUPPORTED_LANGS = {"python", "py", "javascript", "js", "typescript", "ts"}


def _normalize_language(lang: str | None) -> str:
    if not lang:
        return "unknown"
    lang_norm = lang.strip().lower()
    # map aliases
    if lang_norm in {"py"}:
        return "python"
    if lang_norm in {"js"}:
        return "javascript"
    if lang_norm in {"ts"}:
        return "typescript"
    return lang_norm


def _severity_for(rule: str) -> str:
    # simple mapping; could be extended
    mapping = {
        "dangerous_eval": "high",
        "dangerous_exec": "high",
        "broad_except": "medium",
        "debug_statement": "low",
        "todo_comment": "low",
        "unreachable_code_hint": "medium",
        "innerHTML_assignment": "high",
    }
    return mapping.get(rule, "low")


def _count_by_severity(findings: List[Finding]) -> dict:
    counts: dict = {"low": 0, "medium": 0, "high": 0}
    for f in findings:
        counts[f.severity] = counts.get(f.severity, 0) + 1
    return counts


def _analyze_common(code: str) -> List[Finding]:
    findings: List[Finding] = []
    for idx, line in enumerate(code.splitlines(), start=1):
        # TODO comments
        if "TODO" in line or "FIXME" in line:
            findings.append(
                Finding(
                    type="todo_comment",
                    message="Found TODO/FIXME comment",
                    line=idx,
                    severity=_severity_for("todo_comment"),
                )
            )
        # Heuristic unreachable code: 'return' followed by more code indented at same level
        if re.search(r"\breturn\b", line):
            # Look ahead next non-empty line; if same or lower indentation and not a new block marker, flag
            pass  # handled in language-specific where indentation known
    return findings


def _analyze_python(code: str) -> List[Finding]:
    findings: List[Finding] = _analyze_common(code)

    lines = code.splitlines()
    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()

        # Debug statements
        if re.search(r"\bprint\s*\(", stripped) or re.search(r"\bpdb\.set_trace\s*\(", stripped):
            findings.append(
                Finding(
                    type="debug_statement",
                    message="Debug/print statement detected",
                    line=idx,
                    severity=_severity_for("debug_statement"),
                )
            )

        # Dangerous eval/exec
        if re.search(r"\beval\s*\(", stripped):
            findings.append(
                Finding(
                    type="dangerous_eval",
                    message="Use of eval() detected; consider safer alternatives",
                    line=idx,
                    severity=_severity_for("dangerous_eval"),
                )
            )
        if re.search(r"\bexec\s*\(", stripped):
            findings.append(
                Finding(
                    type="dangerous_exec",
                    message="Use of exec() detected; this is potentially unsafe",
                    line=idx,
                    severity=_severity_for("dangerous_exec"),
                )
            )

        # Broad except
        if re.search(r"^\s*except\s*:\s*(#.*)?$", line):
            findings.append(
                Finding(
                    type="broad_except",
                    message="Broad 'except:' detected; specify exception types",
                    line=idx,
                    severity=_severity_for("broad_except"),
                )
            )

    # Unreachable code hint: detect 'return' then non-empty code on same indent level later
    returns_at_indent = set()
    for idx, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        curr_indent = len(line) - len(line.lstrip(" "))
        # track returns
        if re.search(r"\breturn\b", line.strip()):
            returns_at_indent.add(curr_indent)
        else:
            if curr_indent in returns_at_indent:
                # if we see executable-looking code after a return at same indent, hint unreachable
                if re.match(r"\s*(\w|[A-Za-z_]+\s*=)", line):
                    findings.append(
                        Finding(
                            type="unreachable_code_hint",
                            message="Code after return at the same indentation may be unreachable",
                            line=idx,
                            severity=_severity_for("unreachable_code_hint"),
                        )
                    )
                    # Do not spam multiple hints for same indent; remove to limit
                    returns_at_indent.discard(curr_indent)

    return findings


def _analyze_js(code: str) -> List[Finding]:
    findings: List[Finding] = _analyze_common(code)

    for idx, line in enumerate(code.splitlines(), start=1):
        stripped = line.strip()

        # Debug statements
        if re.search(r"\bconsole\.(log|debug|info|trace)\s*\(", stripped):
            findings.append(
                Finding(
                    type="debug_statement",
                    message="Console debug statement detected",
                    line=idx,
                    severity=_severity_for("debug_statement"),
                )
            )

        # Dangerous eval
        if re.search(r"\beval\s*\(", stripped):
            findings.append(
                Finding(
                    type="dangerous_eval",
                    message="Use of eval() detected; consider safer alternatives",
                    line=idx,
                    severity=_severity_for("dangerous_eval"),
                )
            )

        # innerHTML assignment (XSS risk)
        if re.search(r"\.innerHTML\s*=", stripped):
            findings.append(
                Finding(
                    type="innerHTML_assignment",
                    message="Assignment to innerHTML detected; ensure proper sanitization",
                    line=idx,
                    severity=_severity_for("innerHTML_assignment"),
                )
            )

        # Unreachable code hint: 'return' followed by statements at same block level (heuristic)
        # We rely on semicolons/braces; basic heuristic is coarse and limited to nearby lines
        if re.search(r"\breturn\b", stripped):
            pass  # simplistic heuristic handled below

    # A coarse unreachable heuristic: if a 'return;' appears and soon after a non-closing-brace statement appears, flag once
    lines = code.splitlines()
    return_indices = [i for i, l in enumerate(lines) if re.search(r"\breturn\b", l)]
    for ri in return_indices:
        for j in range(ri + 1, min(ri + 6, len(lines))):
            l2 = lines[j].strip()
            if not l2 or l2 in {"}", "};"}:
                continue
            if not l2.startswith("//"):
                findings.append(
                    Finding(
                        type="unreachable_code_hint",
                        message="Statement appears after a return; may be unreachable",
                        line=j + 1,
                        severity=_severity_for("unreachable_code_hint"),
                    )
                )
                break

    return findings


# PUBLIC_INTERFACE
def analyze_code(code: str, language: str | None) -> Tuple[list[Finding], Summary]:
    """
    Analyze code using a minimal static analysis pass.

    Args:
        code: Source code as a string
        language: Optional language hint (python, javascript, typescript)

    Returns:
        Tuple of (findings, summary)
    """
    lang = _normalize_language(language)
    if lang in {"python"}:
        findings = _analyze_python(code)
    elif lang in {"javascript", "typescript"}:
        findings = _analyze_js(code)
    else:
        # If unknown, try both and merge de-duplicating by (line, type, message)
        py_findings = _analyze_python(code)
        js_findings = _analyze_js(code)
        seen = set()
        findings: List[Finding] = []
        for f in py_findings + js_findings:
            key = (f.line, f.type, f.message)
            if key not in seen:
                findings.append(f)
                seen.add(key)

    summary = Summary(count_by_severity=_count_by_severity(findings))
    return findings, summary
